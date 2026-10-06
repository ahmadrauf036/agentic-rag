from langchain_chroma import Chroma
from core.embeddings import embedding_model
import os
from dotenv import load_dotenv
from functools import lru_cache
load_dotenv()

embeddings = embedding_model()


@lru_cache(maxsize=1)
def get_vector_store():
    vector_store = Chroma(
        collection_name="rag",
        embedding_function=embeddings,
        chroma_cloud_api_key=os.getenv("CHROMA_API_KEY"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )

    return vector_store
