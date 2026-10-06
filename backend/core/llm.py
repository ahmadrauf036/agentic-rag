"""
Groq LLM client.

This module ONLY builds the raw, tool-agnostic LLM connection. It knows
nothing about tools, prompts, or per-request state like selected_files —
those are request-scoped and get bound in agent/factory.py instead. This
keeps the LLM client reusable and safe to treat as a singleton.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from config import GROQ_MODEL

load_dotenv()


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    """Singleton Groq chat model client — no tools bound here."""
    return ChatGroq(
        model=GROQ_MODEL,
        temperature=0.0,
        max_retries=2,
        api_key=os.getenv("GROQ_API_KEY"),
    )