import uuid

import pytest
from langchain_core.messages import HumanMessage

from agent.session_manager import get_or_create_graph
from db.sessions import create_session, delete_session, get_session

# Replace with a real file_hash from a document already ingested under
# REAL_OWNER_ID in your test Supabase project.
REAL_OWNER_ID = "da560450-5f18-4098-bed9-14f873c052df"
KNOWN_FILE_HASH = "0fc74fc8a3f0"  # update if this document has since been deleted


@pytest.mark.integration
class TestCrossUserIsolation:
    async def test_stranger_cannot_retrieve_owners_document(self):
        stranger_id = str(uuid.uuid4())
        thread_id = f"isolation-test-{uuid.uuid4()}"

        graph = await get_or_create_graph(
            thread_id=thread_id,
            user_id=stranger_id,
            selected_files=[KNOWN_FILE_HASH],
        )
        config = {"configurable": {"thread_id": thread_id}}
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="What is this document about?")]},
            config=config,
        )
        reply = result["messages"][-1].content.lower()

        assert "couldn't find" in reply or "could not find" in reply

        delete_session(thread_id, stranger_id)  # cleanup

    async def test_owner_can_retrieve_their_own_document(self):
        thread_id = f"isolation-owner-test-{uuid.uuid4()}"

        graph = await get_or_create_graph(
            thread_id=thread_id,
            user_id=REAL_OWNER_ID,
            selected_files=[KNOWN_FILE_HASH],
        )
        config = {"configurable": {"thread_id": thread_id}}
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="What is this document about?")]},
            config=config,
        )
        reply = result["messages"][-1].content.lower()

        assert "couldn't find" not in reply

        delete_session(thread_id, REAL_OWNER_ID)  # cleanup


@pytest.mark.integration
class TestSessionOwnership:
    def test_user_cannot_read_another_users_session(self):
        owner_id = str(uuid.uuid4())
        stranger_id = str(uuid.uuid4())
        thread_id = f"ownership-test-{uuid.uuid4()}"

        create_session(thread_id, owner_id, ["fake-hash"], None, title="Owner's chat")

        # Stranger looks up the same thread_id under their own user_id
        result = get_session(thread_id, stranger_id)
        assert result is None  # must not leak the owner's session

        owned_result = get_session(thread_id, owner_id)
        assert owned_result is not None

        delete_session(thread_id, owner_id)  # cleanup