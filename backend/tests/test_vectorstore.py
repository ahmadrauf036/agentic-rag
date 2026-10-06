import pytest
from retrieval.vectorstore import get_vector_store


@pytest.mark.integration
def test_vector_store_connects_and_roundtrips():
    vector_store = get_vector_store()
    vector_store.add_texts(["hello world, this is a test document"])
    results = vector_store.similarity_search("hello", k=1)
    assert len(results) == 1
    assert "hello" in results[0].page_content.lower()