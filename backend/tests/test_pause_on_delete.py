import uuid

import pytest

from db.sessions import create_session, delete_session, get_session, pause_sessions_referencing_file


@pytest.mark.integration
class TestPauseOnDelete:
    def test_deleting_referenced_file_pauses_session(self):
        user_id = str(uuid.uuid4())
        thread_id = f"pause-test-{uuid.uuid4()}"
        file_hash = "fake-file-hash-for-pause-test"

        create_session(thread_id, user_id, [file_hash], None, title="Test chat")

        count = pause_sessions_referencing_file(
            file_hash=file_hash, user_id=user_id, reason="Test document deleted"
        )
        assert count == 1

        session = get_session(thread_id, user_id)
        assert session["paused_reason"] == "Test document deleted"

        delete_session(thread_id, user_id)  # cleanup

    def test_pausing_does_not_affect_unrelated_sessions(self):
        user_id = str(uuid.uuid4())
        thread_id_unrelated = f"unrelated-test-{uuid.uuid4()}"

        create_session(thread_id_unrelated, user_id, ["different-hash"], None, title="Unrelated chat")

        pause_sessions_referencing_file(
            file_hash="some-other-hash", user_id=user_id, reason="irrelevant"
        )

        session = get_session(thread_id_unrelated, user_id)
        assert session["paused_reason"] is None

        delete_session(thread_id_unrelated, user_id)  # cleanup

    def test_pausing_does_not_leak_across_users(self):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())
        shared_hash = "shared-file-hash-test"

        thread_a = f"pause-user-a-{uuid.uuid4()}"
        thread_b = f"pause-user-b-{uuid.uuid4()}"

        create_session(thread_a, user_a, [shared_hash], None, title="A's chat")
        create_session(thread_b, user_b, [shared_hash], None, title="B's chat")

        # Only pause user_a's session referencing this hash
        pause_sessions_referencing_file(file_hash=shared_hash, user_id=user_a, reason="A's doc deleted")

        session_a = get_session(thread_a, user_a)
        session_b = get_session(thread_b, user_b)

        assert session_a["paused_reason"] is not None
        assert session_b["paused_reason"] is None  # must not be affected

        delete_session(thread_a, user_a)
        delete_session(thread_b, user_b)