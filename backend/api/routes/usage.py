# api/routes/usage.py — new file
from fastapi import APIRouter, Depends
from core.auth import AuthenticatedUser, get_current_user, require_admin
from db.usage import get_user_usage, get_all_usage

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("")
def my_usage(days: int = 30, user: AuthenticatedUser = Depends(get_current_user)):
    return get_user_usage(user.user_id, since_days=days)


@router.get("/all")
def all_usage(days: int = 30, admin: AuthenticatedUser = Depends(require_admin)):
    return get_all_usage(since_days=days)