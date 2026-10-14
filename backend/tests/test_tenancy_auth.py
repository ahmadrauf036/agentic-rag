import pytest
from fastapi import HTTPException

from core.auth import (AuthenticatedUser, Identity, get_current_user,
                       require_org_admin, require_owner, require_platform_admin)

IDENT = Identity("u1", "u@x.com", False)


def _membership(**over):
    base = {"org_id": "o1", "org_name": "Acme", "role": "member", "position": None,
            "member_status": "active", "org_status": "active"}
    return {**base, **over}


@pytest.mark.parametrize("membership", [
    None,
    _membership(member_status="removed"),
    _membership(org_status="suspended"),
])
def test_inactive_access_is_rejected(monkeypatch, membership):
    monkeypatch.setattr("core.auth.get_membership", lambda uid: membership)
    with pytest.raises(HTTPException) as exc:
        get_current_user(identity=IDENT)
    assert exc.value.status_code == 403


def test_active_member_gets_org_context(monkeypatch):
    monkeypatch.setattr("core.auth.get_membership", lambda uid: _membership(role="org_admin"))
    user = get_current_user(identity=IDENT)
    assert user.org_id == "o1" and user.is_org_admin and not user.is_owner


def test_role_gates():
    member = AuthenticatedUser("u", "e", "o", "Acme", "member", None)
    admin = AuthenticatedUser("u", "e", "o", "Acme", "org_admin", None)
    with pytest.raises(HTTPException):
        require_org_admin(user=member)
    with pytest.raises(HTTPException):
        require_owner(user=admin)
    assert require_org_admin(user=admin) is admin


def test_platform_gate():
    with pytest.raises(HTTPException) as exc:
        require_platform_admin(identity=IDENT)
    assert exc.value.status_code == 403