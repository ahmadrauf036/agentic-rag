"""
Vector store for conversation history — separate collection from the
document store ("rag"), so document search and cross-session chat
recall never accidentally mix results.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_chroma import Chroma

from core.embeddings import embedding_model

load_dotenv()


@lru_cache(maxsize=1)
def get_memory_store() -> Chroma:
    embeddings = embedding_model()
    return Chroma(
        collection_name="chat_history",
        embedding_function=embeddings,
        chroma_cloud_api_key=os.getenv("CHROMA_API_KEY"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )