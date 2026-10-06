"""
Privileged Supabase client using the service-role key — for admin
operations that need to query/modify auth.users directly (listing users,
changing roles). NEVER expose this key or client to the frontend; it
bypasses all row-level security.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


@lru_cache(maxsize=1)
def get_admin_client() -> Client:
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not set — admin features unavailable.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)