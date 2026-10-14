import uuid

import psycopg
import pytest

from db.tenancy import _get_connection, create_organization, get_membership

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def cleanup():
    yield
    with _get_connection() as conn:
        conn.execute("DELETE FROM organizations WHERE name LIKE 'pytest-%'")  # cascades
        conn.commit()


def test_creator_becomes_owner():
    uid = str(uuid.uuid4())
    org = create_organization("pytest-owner-org", uid)
    m = get_membership(uid)
    assert m["role"] == "owner" and str(m["org_id"]) == org["id"]


def test_user_cannot_join_second_org_and_nothing_is_left_behind():
    uid = str(uuid.uuid4())
    create_organization("pytest-first", uid)
    with pytest.raises(psycopg.errors.UniqueViolation):
        create_organization("pytest-second", uid)
    with _get_connection() as conn:
        n = conn.execute(
            "SELECT COUNT(*) AS n FROM organizations WHERE name = 'pytest-second'"
        ).fetchone()["n"]
    assert n == 0  # the failed attempt rolled back completely


def test_org_cannot_have_two_owners():
    org = create_organization("pytest-two-owners", str(uuid.uuid4()))
    with pytest.raises(psycopg.errors.UniqueViolation):
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO memberships (user_id, org_id, role) VALUES (%s, %s, 'owner')",
                (str(uuid.uuid4()), org["id"]),
            )
            conn.commit()