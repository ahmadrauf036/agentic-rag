from langchain_community.embeddings import FastEmbedEmbeddings
from functools import lru_cache
from config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def embedding_model()->FastEmbedEmbeddings:
    return FastEmbedEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )