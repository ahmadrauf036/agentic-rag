import uuid

import pytest

from db.tenancy import _get_connection, create_organization
from retrieval.tenant_stores import drop_org_collections


@pytest.fixture
def make_org():
    created = []

    def _make():
        org = create_organization(f"pytest-{uuid.uuid4().hex[:8]}", str(uuid.uuid4()))
        created.append(org["id"])
        return org

    yield _make
    for org_id in created:
        try:
            drop_org_collections(org_id)
        except Exception:
            pass
        with _get_connection() as conn:
            conn.execute("DELETE FROM organizations WHERE id = %s", (org_id,))  # cascades
            conn.commit()