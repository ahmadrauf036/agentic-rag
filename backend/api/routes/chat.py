import json
import logging
from db.sessions import get_session
from fastapi import Request, APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from agent.memory_writer import store_turn
from agent.session_manager import get_or_create_graph
from core.auth import AuthenticatedUser, get_current_user
from model.chat import ChatRequest, ChatResponse
from core.rate_limit import limiter
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _user_facing_error(error: Exception) -> str:
    error_str = str(error).lower()
    if "timeout" in error_str or "timed out" in error_str:
        return "The AI service took too long to respond. Please try again."
    if "rate limit" in error_str or "429" in error_str:
        return "The AI service is currently rate-limited. Please wait a moment and try again."
    if "api key" in error_str or "unauthorized" in error_str or "401" in error_str:
        return "The AI service rejected the request due to a configuration issue. Please contact support."
    return "Something went wrong while processing your message. Please try again."

from db.audit import log_action

@router.post("", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ChatResponse:
    try:
        graph = await get_or_create_graph(
            thread_id=payload.thread_id,
            user_id=user.user_id,
            selected_files=payload.selected_files,
            page=payload.page,
            first_message=payload.message,
        )
        existing_session = get_session(payload.thread_id, user.user_id)
        if existing_session and existing_session.get("paused_reason"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=existing_session["paused_reason"],
            )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    config = {
        "configurable": {"thread_id": payload.thread_id},
        "recursion_limit": 25,
    }
    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=payload.message)]}, config=config
        )
        
        # In chat() (non-streaming), after getting `result`:
        result = await graph.ainvoke({"messages": [HumanMessage(content=payload.message)]}, config=config)
        reply = result["messages"][-1].content

        usage = _sum_usage_from_messages(result["messages"])
        log_usage(
            user_id=user.user_id, thread_id=payload.thread_id,
            input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"],
            model="openai/gpt-oss-120b",
        )
        reply = result["messages"][-1].content

        session = get_session(payload.thread_id, user.user_id)
        store_turn(
            thread_id=payload.thread_id,
            owner_id=user.user_id,
            session_title=session["title"] if session else "Untitled chat",
            user_message=payload.message,
            assistant_message=reply,
        )
    except Exception as error:
        logger.exception("Agent invocation failed for thread_id=%s user_id=%s", payload.thread_id, user.user_id)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=_user_facing_error(error))
    log_action(
        actor_id=user.user_id,
        actor_email=user.email,
        action="chat_message",
        target=payload.thread_id,
        metadata={"message_length": len(payload.message)},
    )
    return ChatResponse(thread_id=payload.thread_id, reply=reply)


@router.post("/stream")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        graph = await get_or_create_graph(
            thread_id=payload.thread_id,
            user_id=user.user_id,
            selected_files=payload.selected_files,
            page=payload.page,
            first_message=payload.message,
        )
        existing_session = get_session(payload.thread_id, user.user_id)
        if existing_session and existing_session.get("paused_reason"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=existing_session["paused_reason"],
            )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    config = {
        "configurable": {"thread_id": payload.thread_id},
        "recursion_limit": 25,
    }

    async def event_generator():
        full_reply = ""
        try:
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=payload.message)]},
                config=config,
                version="v2",
            ):
                kind = event["event"]

                if kind == "on_tool_start":
                    yield _sse("tool_start", {"tool": event["name"], "args": event["data"].get("input")})

                elif kind == "on_tool_end":
                    output = event["data"].get("output")
                    content = getattr(output, "content", str(output))
                    yield _sse("tool_end", {"tool": event["name"], "result": content})

                    artifact = getattr(output, "artifact", None)
                    if artifact:
                        yield _sse("sources", {"tool": event["name"], "sources": artifact})
                elif kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        full_reply += chunk.content
                        yield _sse("token", {"text": chunk.content})

            yield _sse("done", {"thread_id": payload.thread_id})
            session = get_session(payload.thread_id, user.user_id)
            # After the astream_events loop finishes, before/alongside the store_turn call:
            final_state = await graph.aget_state(config)
            usage = _sum_usage_from_messages(final_state.values.get("messages", [])[-10:])  # recent messages from this turn
            log_usage(
                user_id=user.user_id, thread_id=payload.thread_id,
                input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"],
                model="openai/gpt-oss-120b",
            )
            store_turn(
                thread_id=payload.thread_id,
                owner_id=user.user_id,
                session_title=session["title"] if session else "Untitled chat",
                user_message=payload.message,
                assistant_message=full_reply,
            )   
        except Exception as error:
            logger.exception("Streaming failed for thread_id=%s user_id=%s", payload.thread_id, user.user_id)
            yield _sse("error", {"detail": _user_facing_error(error)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


from db.usage import log_usage

def _sum_usage_from_messages(messages: list) -> dict:
    """Sum usage_metadata across every AIMessage in a turn — a turn can
    involve multiple LLM calls (one per tool-calling round-trip)."""
    total_input = 0
    total_output = 0
    for m in messages:
        usage = getattr(m, "usage_metadata", None)
        if usage:
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)
    return {"input_tokens": total_input, "output_tokens": total_output}

