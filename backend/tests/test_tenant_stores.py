import pytest

from retrieval.tenant_stores import get_docs_store, get_memory_store


@pytest.mark.parametrize("bad", ["", "not-a-uuid", "../other", "org_x_docs"])
def test_collection_names_only_come_from_uuids(bad):
    with pytest.raises(ValueError):
        get_docs_store(bad)
    with pytest.raises(ValueError):
        get_memory_store(bad)