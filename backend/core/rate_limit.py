"""
Per-user rate limiting via slowapi. Keyed by the authenticated user's ID
(extracted from the JWT), not IP address, since auth already exists and
per-user limits are more accurate than per-IP (multiple users could share
an IP; one user could rotate IPs).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def _user_id_or_ip(request: Request) -> str:
    """
    Rate-limit key: the authenticated user's ID if available, falling
    back to IP address for unauthenticated requests (which will mostly
    just get rejected by auth anyway, but this keeps the limiter safe
    for any route that doesn't require auth).
    """
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            import jwt as pyjwt
            # Decode without verification just to extract the user id for
            # rate-limit keying — the real verification still happens in
            # the actual auth dependency; this is purely for bucketing.
            payload = pyjwt.decode(token, options={"verify_signature": False})
            return payload.get("sub", get_remote_address(request))
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_user_id_or_ip)