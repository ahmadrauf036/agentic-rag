import uuid

import pytest
from fastapi.testclient import TestClient

from agent.memory_writer import store_turn
from core.auth import AuthenticatedUser, get_current_user
from db.documents import get_missing_hashes, list_documents
from db.sessions import create_session, get_session
from ingestion.pipeline import ingestion
from main import app
from retrieval.memory_retriever import search_chat_history
from retrieval.retriever import search

pytestmark = pytest.mark.integration

MARKER = "zephyr-quokka-protocol"
POLICY = f"The {MARKER} requires all travel to be approved by the regional director. " * 5


def _user(org, role="org_admin"):
    return AuthenticatedUser(str(uuid.uuid4()), "t@example.com", org["id"], org["name"], role, None)


def _ingest(tmp_path, org, text=POLICY):
    p = tmp_path / f"{uuid.uuid4().hex}.txt"
    p.write_text(text)
    result = ingestion([str(p)], org_id=org["id"], uploaded_by=str(uuid.uuid4()))
    assert result.success, result.detail
    return result.files[0].file_hash


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def _act_as(user):
    app.dependency_overrides[get_current_user] = lambda: user


def test_search_cannot_cross_orgs(make_org, tmp_path):
    org_a, org_b = make_org(), make_org()
    h = _ingest(tmp_path, org_a)
    assert search(org_a["id"], [h], MARKER)
    assert search(org_b["id"], [h], MARKER) == []  # same hash, other org: nothing


def test_identical_file_in_two_orgs_is_fully_independent(make_org, tmp_path, client):
    org_a, org_b = make_org(), make_org()
    user_a, user_b = _user(org_a), _user(org_b, "member")
    ha, hb = _ingest(tmp_path, org_a), _ingest(tmp_path, org_b)
    assert ha == hb  # identical content, identical hash: the dangerous case

    ta, tb = str(uuid.uuid4()), str(uuid.uuid4())
    create_session(ta, user_a.user_id, org_a["id"], [ha], None, "a")
    create_session(tb, user_b.user_id, org_b["id"], [hb], None, "b")

    _act_as(user_a)
    resp = client.delete(f"/documents/{ha}")
    assert resp.status_code == 200 and resp.json()["paused_sessions"] == 1

    assert get_session(ta, user_a.user_id)["paused_reason"]
    assert get_session(tb, user_b.user_id)["paused_reason"] is None  # org B untouched
    assert search(org_a["id"], [ha], MARKER) == []
    assert search(org_b["id"], [hb], MARKER)                          # org B still answers

    _act_as(user_b)
    assert [d["file_hash"] for d in client.get("/documents").json()] == [hb]


def test_members_cannot_mutate_documents(make_org, client):
    _act_as(_user(make_org(), "member"))
    assert client.delete("/documents/abc").status_code == 403
    assert client.get("/documents/abc/dependents").status_code == 403


def test_memory_is_private_per_user_and_per_org(make_org):
    org_a, org_b = make_org(), make_org()
    u1, u2 = str(uuid.uuid4()), str(uuid.uuid4())
    store_turn(org_id=org_a["id"], user_id=u1, thread_id=str(uuid.uuid4()), session_title="t",
               user_message=f"What is {MARKER}?", assistant_message="Needs director approval.")
    assert search_chat_history(org_a["id"], u1, MARKER)
    assert search_chat_history(org_a["id"], u2, MARKER) == []  # same org, other user
    assert search_chat_history(org_b["id"], u1, MARKER) == []  # other org, same user id


def test_unknown_hashes_are_reported(make_org):
    org = make_org()
    assert get_missing_hashes(org["id"], ["nope"]) == ["nope"]
    assert list_documents(org["id"]) == []