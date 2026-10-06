# from ingestion.pipeline import ingestion

# res = ingestion(["data/same_as_gov.pdf","data/prompt_engineering.pdf"])

# print(res)

# from agent.tools.calculator_tool import calculator_tool

# print(calculator_tool.invoke({"expression": "2 + 2"}))
# print(calculator_tool.invoke({"expression": "(15 * 3.5) / 7"}))
# print(calculator_tool.invoke({"expression": "sqrt(144)"}))



# from agent.tools.doc_search_tool import make_doc_search_tool

# tool = make_doc_search_tool(selected_files=["e83014e71fc8"])
# print(tool.invoke({"query": "what is this document about?"}))

# from agent.factory import build_agent
# from config import SYSTEM_PROMPT
# from agent.tools.calculator_tool import calculator_tool

# agent = build_agent(selected_files=["<your_real_file_hash>"], page=None)

# messages = [
#     ("system", SYSTEM_PROMPT),
#     ("human", "What is invozone."),
# ]

# ai_msg = agent.invoke(messages)
# print(ai_msg.tool_calls[0]['args'])
# print(ai_msg.tool_calls[0]['name'])

# print(calculator_tool.name)

# lst = [{'name':'tool1'},{'name':'tool2'},{'name':'tool3'}]

# q = [lst[i]['name'] for i in range(len(lst))]
# print(q)
# from langgraph.graph import StateGraph, MessagesState, START, END

# def should_continue(messages: MessagesState):
#     last_msg = messages[-1]
#     if(last_msg.response_metadata["finish_reason"] == 'stop'):
#         return END
#     return 'tool_node'

# def tool_node(messages:MessagesState):
#     last_msg = messages[-1]
#     tools = [[last_msg.tool_calls[i]['name'] for i in range(len(last_msg.tool_calls))]]
    
#     tool_by_name = {
#         'document_search': 'doc_search_tool',
#         'calculator': 'calculator_tool'
#     }
        
#     for tool in tools:
#         res = tool_by_name[tool].invoke(tool['args'])
#         messages.append(res)
    
#     return
    


# graph = StateGraph(MessagesState)
# graph.add_node('call_agent', agent)
# graph.add_node('tool_node', tool_node)
    
# graph.add_edge(START, 'call_agent')
# graph.add_conditional_edges('call_agent', should_continue, ['tool_node',END])
# graph.add_edge('tool_node','call_agent')
# graph = graph.compile()

# png_bytes = graph.get_graph().draw_mermaid_png()

# with open("graph.png", "wb") as f:
#     f.write(png_bytes)
    
# from agent.state import build_graph
# from langchain_core.messages import HumanMessage

# graph = build_graph(selected_files=["ced564edfc31"], page=None)

# result = graph.invoke({"messages": [HumanMessage(content="What is invozone?")]})

# for msg in result["messages"]:
#     print(type(msg).__name__, "->", getattr(msg, "content", None) or getattr(msg, "tool_calls", None))


# from ingestion.loader import compute_file_hash

# with open("data/same_as_gov-dup.pdf", "rb") as f:
#     hash_a = compute_file_hash(f.read())
# with open("data/same_as_gov.pdf", "rb") as f:
#     hash_b = compute_file_hash(f.read())

# print(hash_a, hash_b, hash_a == hash_b)


# """
# test_memory.py — manual test for Phase 5 (multi-turn memory).
# """

# from agent.state import build_graph
# from langchain_core.messages import HumanMessage

# # Build ONE graph, reused across multiple invoke() calls below —
# # this is what makes the thread_id-based memory actually work.
# graph = build_graph(selected_files=["ced564edfc31"], page=None)


# def print_last_message(result):
#     last = result["messages"][-1]
#     print(f"{type(last).__name__} -> {getattr(last, 'content', None)}")


# # --- Test 1: same thread_id, two turns, second turn should use memory ---
# print("=== Test 1: same thread_id (memory should work) ===")
# config_a = {"configurable": {"thread_id": "conversation-a"}}

# result = graph.invoke({"messages": [HumanMessage(content="What is InvoZone?")]}, config=config_a)
# print_last_message(result)

# result = graph.invoke({"messages": [HumanMessage(content="What page was that on?")]}, config=config_a)
# print_last_message(result)
# # Expect: the agent correctly answers using context from the FIRST question,
# # without you re-explaining what "that" refers to.


# # --- Test 2: different thread_id, should have NO memory of conversation-a ---
# print("\n=== Test 2: different thread_id (should have no memory) ===")
# config_b = {"configurable": {"thread_id": "conversation-b"}}

# result = graph.invoke({"messages": [HumanMessage(content="What page was that on?")]}, config=config_b)
# print_last_message(result)
# # Expect: the agent should be confused / say it doesn't know what "that"
# # refers to, since this is a brand new thread with no prior context.


# # --- Test 3: resume conversation-a again later, memory should still be there ---
# print("\n=== Test 3: resume conversation-a (memory should persist within this process) ===")
# result = graph.invoke({"messages": [HumanMessage(content="Summarize what you told me so far.")]}, config=config_a)
# print_last_message(result)
# # Expect: a coherent summary referencing InvoZone content from turn 1,
# # proving conversation-a's full history is still intact.


# # --- Test 4: inspect full history length per thread ---
# print("\n=== Test 4: message count per thread ===")
# state_a = graph.get_state(config_a)
# state_b = graph.get_state(config_b)
# print("conversation-a message count:", len(state_a.values["messages"]))
# print("conversation-b message count:", len(state_b.values["messages"]))
# # Expect: conversation-a has many more messages (3 full turns' worth)
# # than conversation-b (1 turn).

# """test_chat_route.py — manual test for the /chat endpoint, no server needed."""

# from api.routes.chat import chat
# from model.chat import ChatRequest

# thread_id = "test-session-1"

# # First request — new thread, must include selected_files
# request_1 = ChatRequest(
#     thread_id=thread_id,
#     message="What is InvoZone?",
#     selected_files=["<your_real_file_hash>"],
# )
# response_1 = chat(request_1)
# print("Turn 1:", response_1.reply)

# # Second request — same thread, no selected_files needed (session already exists)
# request_2 = ChatRequest(
#     thread_id=thread_id,
#     message="What page was that on?",
# )
# response_2 = chat(request_2)
# print("Turn 2:", response_2.reply)

# # Third request — brand new thread, no selected_files provided -> should raise 400
# try:
#     bad_request = ChatRequest(thread_id="brand-new-thread", message="hi")
#     chat(bad_request)
# except Exception as error:
#     print("Expected error for missing selected_files on new thread:", error)

# from ingestion.loader import compute_file_hash

# with open("data/same_as_gov.pdf", "rb") as f:
#     print(compute_file_hash(f.read()))
    
# from retrieval.vectorstore import get_vector_store

# vector_store = get_vector_store()
# all_metadata = vector_store._collection.get(include=["metadatas"])["metadatas"]
# seen = {m["file_hash"] for m in all_metadata}
# print(seen)

# """test_chat_route.py — manual test for the /chat endpoint, no server needed."""

# from api.routes.chat import chat
# from model.chat import ChatRequest

# thread_id = "test-session-1"

# # First request — new thread, must include selected_files
# request_1 = ChatRequest(
#     thread_id=thread_id,
#     message="What is InvoZone?",
#     selected_files=["ced564edfc31"],   # <-- real hash now
# )
# response_1 = chat(request_1)
# print("Turn 1:", response_1.reply)

# # Second request — same thread, no selected_files needed (session already exists)
# request_2 = ChatRequest(
#     thread_id=thread_id,
#     message="What page was that on?",
# )
# response_2 = chat(request_2)
# print("Turn 2:", response_2.reply)

# # Third request — brand new thread, no selected_files provided -> should raise 400
# try:
#     bad_request = ChatRequest(thread_id="brand-new-thread", message="hi")
#     chat(bad_request)
# except Exception as error:
#     print("Expected error for missing selected_files on new thread:", error)

# """test_stream.py"""

# import asyncio
# from agent.session_manager import get_or_create_graph
# from langchain_core.messages import HumanMessage

# async def main():
#     graph = get_or_create_graph(
#         thread_id="stream-test-1",
#         selected_files=["ced564edfc31"],
#     )
#     config = {"configurable": {"thread_id": "stream-test-1"}}

#     async for event in graph.astream_events(
#         {"messages": [HumanMessage(content="What is InvoZone?")]},
#         config=config,
#         version="v2",
#     ):
#         kind = event["event"]
#         if kind == "on_tool_start":
#             print(f"\n[TOOL START] {event['name']} args={event['data'].get('input')}")
#         elif kind == "on_tool_end":
#             output = event["data"].get("output")
#             content = getattr(output, "content", str(output))
#             print(f"\n[TOOL END] {event['name']} -> {content[:200]}")
#         elif kind == "on_chat_model_stream":
#             chunk = event["data"]["chunk"]
#             if chunk.content:
#                 print(chunk.content, end="", flush=True)

# asyncio.run(main())


# 1. Blank message rejected
# from model.chat import ChatRequest
# try:
#     ChatRequest(thread_id="t1", message="   ")
# except Exception as e:
#     print("Blank message correctly rejected:", e)

# # 2. Corrupt PDF handled gracefully
# from ingestion.pipeline import ingestion
# import os

# with open("data/fake_corrupt.pdf", "wb") as f:
#     f.write(b"this is not a real pdf file, just garbage bytes")

# result = ingestion(["data/fake_corrupt.pdf"])
# print("Corrupt PDF result:", result.success, "-", result.detail)
# os.remove("data/fake_corrupt.pdf")

# 3. Groq failure produces clean error (temporarily break your API key to test)
# In .env, temporarily set GROQ_API_KEY=invalid_key_test, restart server, then:
# curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
#   -d '{"thread_id": "err-test", "message": "hi", "selected_files": ["ced564edfc31"]}'
# Expect: 502 with a clean "configuration issue" message, not a raw stack trace.
# Remember to restore your real GROQ_API_KEY afterward.

# from db.sessions import init_db, create_session, list_sessions, get_session, delete_session

# init_db()
# create_session("test-thread-1", ["ced564edfc31"], None, "Test session")
# print(list_sessions())
# print(get_session("test-thread-1"))
# print(delete_session("test-thread-1"))
# print(list_sessions())

# quick_test_checkpointer.py
# from agent.state import build_graph
# from langchain_core.messages import HumanMessage

# graph = build_graph(selected_files=["ced564edfc31"], page=None)
# config = {"configurable": {"thread_id": "pg-checkpoint-test"}}

# result = graph.invoke({"messages": [HumanMessage(content="What is InvoZone?")]}, config=config)
# print(result["messages"][-1].content)

# # Confirm it's actually in Postgres now, not memory — check state persists
# state = graph.get_state(config)
# print("Message count:", len(state.values["messages"]))


# from db.sessions import get_session
# print(get_session("restart-test-1"))

# """test_auth.py — sanity check the JWT verification logic in isolation."""
# import os
# import jwt
# from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv

# load_dotenv()
# SECRET = os.getenv("SUPABASE_JWT_SECRET")

# # Simulate a Supabase-issued token
# fake_payload = {
#     "sub": "test-user-id-123",
#     "email": "test@example.com",
#     "aud": "authenticated",
#     "exp": datetime.now(timezone.utc) + timedelta(hours=1),
# }
# fake_token = jwt.encode(fake_payload, SECRET, algorithm="HS256")
# print("Fake token:", fake_token)

# from core.auth import get_current_user
# user = get_current_user(sb_access_token=fake_token)
# print("Verified user_id:", user.user_id, "email:", user.email)

# """test_isolation.py"""
# import asyncio
# import uuid
# from agent.session_manager import get_or_create_graph
# from langchain_core.messages import HumanMessage

# USER_A = str(uuid.uuid4())
# USER_B = str(uuid.uuid4())

# async def main():
#     graph_a = await get_or_create_graph(
#         thread_id="isolation-test-a",
#         user_id=USER_A,
#         selected_files=["ced564edfc31"],
#     )
#     config_a = {"configurable": {"thread_id": "isolation-test-a"}}
#     result_a = await graph_a.ainvoke(
#         {"messages": [HumanMessage(content="What is InvoZone?")]}, config=config_a
#     )
#     print("User A:", result_a["messages"][-1].content[:150])

#     graph_b = await get_or_create_graph(
#         thread_id="isolation-test-b",
#         user_id=USER_B,
#         selected_files=["ced564edfc31"],
#     )
#     config_b = {"configurable": {"thread_id": "isolation-test-b"}}
#     result_b = await graph_b.ainvoke(
#         {"messages": [HumanMessage(content="What is InvoZone?")]}, config=config_b
#     )
#     print("User B:", result_b["messages"][-1].content[:150])

# asyncio.run(main())


# # import jwt
# token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjgyOTRmYTRjLTI3ZTctNGU0NC04MmU2LTQ2OGI0Yjc0MWMyZSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3pmcWxydW9qcWl6YmVwdmZudXJyLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJkYTU2MDQ1MC01ZjE4LTQwOTgtYmVkOS0xNGY4NzNjMDUyZGYiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzkwNjc4MjQ3LCJpYXQiOjE3OTA2NzQ2NDcsImVtYWlsIjoiYWhtYWQucmF1ZkBpbnZvem9uZS5kZXYiLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoiYWhtYWQucmF1ZkBpbnZvem9uZS5kZXYiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiJkYTU2MDQ1MC01ZjE4LTQwOTgtYmVkOS0xNGY4NzNjMDUyZGYifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc5MDY3NDY0N31dLCJzZXNzaW9uX2lkIjoiY2FjM2EwYTktY2RiMS00YzJiLTk5NTItNTg3NmU2ZDQ3M2YyIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.KB32hlbWy7lxhq_dbZpNiM3l7PRh75CzTTc1eC5dOSGBxhEvonkXPq5ih5BCdYCH6dVHpfakZv09uCrfDWTbRw"
# # decoded = jwt.decode(token, options={"verify_signature": False})
# # print(decoded)

# from core.auth import get_current_user
# user = get_current_user(authorization=f"Bearer {token}")
# print(user.user_id, user.email)

# # import jwt
# # header = jwt.get_unverified_header(token)
# # print(header)

# """test_isolation.py"""
# import asyncio
# import uuid
# from agent.session_manager import get_or_create_graph
# from langchain_core.messages import HumanMessage

# REAL_USER_ID = "da560450-5f18-4098-bed9-14f873c052df"
# FAKE_STRANGER_ID = str(uuid.uuid4())  # genuinely has no documents
# FRESH_FILE_HASH = "0fc74fc8a3f0"


# async def main():
#     # Real owner — should find real content
#     graph_owner = await get_or_create_graph(
#         thread_id="isolation-owner-test",
#         user_id=REAL_USER_ID,
#         selected_files=[FRESH_FILE_HASH],
#     )
#     config_owner = {"configurable": {"thread_id": "isolation-owner-test"}}
#     result_owner = await graph_owner.ainvoke(
#         {"messages": [HumanMessage(content="What is this document about?")]},
#         config=config_owner,
#     )
#     print("Owner:", result_owner["messages"][-1].content[:200])

#     # Stranger, same file_hash — should find NOTHING
#     graph_stranger = await get_or_create_graph(
#         thread_id="isolation-stranger-test",
#         user_id=FAKE_STRANGER_ID,
#         selected_files=[FRESH_FILE_HASH],
#     )
#     config_stranger = {"configurable": {"thread_id": "isolation-stranger-test"}}
#     result_stranger = await graph_stranger.ainvoke(
#         {"messages": [HumanMessage(content="What is this document about?")]},
#         config=config_stranger,
#     )
#     print("Stranger:", result_stranger["messages"][-1].content[:200])


# asyncio.run(main())

# """test_memory_tools.py"""
# import asyncio
# from agent.session_manager import get_or_create_graph
# from langchain_core.messages import HumanMessage

# REAL_USER_ID = "da560450-5f18-4098-bed9-14f873c052df"

# async def main():
#     # Session 1: talk about InvoZone
#     graph1 = await get_or_create_graph(
#         thread_id="memory-test-session-1",
#         user_id=REAL_USER_ID,
#         selected_files=["ced564edfc31"],
#     )
#     config1 = {"configurable": {"thread_id": "memory-test-session-1"}}
#     result1 = await graph1.ainvoke(
#         {"messages": [HumanMessage(content="What is this document about?")]},
#         config=config1,
#     )
#     print("Session 1 answer:", result1["messages"][-1].content[:150])

#     # Manually store this turn into chat_history (normally the route does this automatically)
#     from agent.memory_writer import store_turn
#     store_turn(
#         thread_id="memory-test-session-1",
#         owner_id=REAL_USER_ID,
#         session_title="InvoZone discussion",
#         user_message="What is InvoZone's role in this project?",
#         assistant_message=result1["messages"][-1].content,
#     )

#     # Session 2: a NEW, different session — ask about the past conversation
#     graph2 = await get_or_create_graph(
#         thread_id="memory-test-session-2",
#         user_id=REAL_USER_ID,
#         selected_files=["<a_real_file_hash_you_own>"],
#     )
#     config2 = {"configurable": {"thread_id": "memory-test-session-2"}}
#     result2 = await graph2.ainvoke(
#         {"messages": [HumanMessage(content="What did we discuss about InvoZone before?")]},
#         config=config2,
#     )
#     print("Session 2 answer:", result2["messages"][-1].content[:300])

# asyncio.run(main())

# """test_delete_cleanup.py"""
# import asyncio
# from agent.session_manager import get_or_create_graph, delete_session
# from agent.memory_writer import store_turn
# from retrieval.memory_retriever import search_chat_history
# from langchain_core.messages import HumanMessage

# REAL_USER_ID = "da560450-5f18-4098-bed9-14f873c052df"
# THREAD_ID = "memory-test-session-1"

# async def main():
#     # Create a session and manually store a distinctive memory
#     graph = await get_or_create_graph(
#         thread_id=THREAD_ID,
#         user_id=REAL_USER_ID,
#         selected_files=["ced564edfc31"],
#     )
#     store_turn(
#         thread_id=THREAD_ID,
#         owner_id=REAL_USER_ID,
#         session_title="Delete cleanup test",
#         user_message="What is the capital of Atlantis?",
#         assistant_message="A distinctive test fact about Atlantis for cleanup verification.",
#     )

#     # Confirm it's searchable BEFORE deletion
#     before = search_chat_history(query="Atlantis", owner_id=REAL_USER_ID)
#     print("Found before delete:", len(before) > 0)

#     # Delete the session
#     delete_session(THREAD_ID, REAL_USER_ID)

#     # Confirm it's GONE after deletion
#     after = search_chat_history(query="Atlantis", owner_id=REAL_USER_ID)
#     print("Found after delete:", len(after) > 0)
#     from agent.state import _pool
#     await _pool.close()

# asyncio.run(main())


# import asyncio
# from agent.session_manager import get_or_create_graph


# async def main():
#     thread_id = "4269a8a6-a344-48b7-b60b-c2c3e22a82d4"
#     user_id = "39a6158e-bacf-4b53-ba8c-20b26d87befa"

#     graph = await get_or_create_graph(
#         thread_id=thread_id,
#         user_id=user_id
#     )

#     config = {
#         "configurable": {
#             "thread_id": thread_id
#         }
#     }

#     state = await graph.aget_state(config)

#     messages = state.values.get("messages", [])

#     print("Restored message count:", len(messages))

#     for m in messages:
#         print(
#             type(m).__name__,
#             "-",
#             getattr(m, "content", "")[:50]
#         )
#     from agent.state import _pool
#     await _pool.close()


# if __name__ == "__main__":
#     asyncio.run(main())

# from retrieval.hybrid_retriever import hybrid_search

# results = hybrid_search(
# #     query="prompt writing techniques",
# #     selected_files=["0fc74fc8a3f0"],
# #     owner_id="39a6158e-bacf-4b53-ba8c-20b26d87befa",
# # )
# # for r in results:
# #     print(r.metadata.get("page"), "-", r.page_content[:100])
    
    
# from agent.tools.doc_search_tool import make_doc_search_tool

# tool = make_doc_search_tool(selected_files=["0fc74fc8a3f0"], owner_id="39a6158e-bacf-4b53-ba8c-20b26d87befa")
# # result = tool.invoke({"query": "prompt writing techniques"})
# # print(result)

# # from agent.tools.doc_search_tool import make_doc_search_tool

# # tool = make_doc_search_tool(selected_files=["<real_file_hash>"], owner_id="<real_user_id>")

# # Call the underlying function directly to see both parts of the tuple
# content, artifact = tool.func("prompt writing techniques")
# print("CONTENT:\n", content[:200])
# print("\nARTIFACT:\n", artifact)

