from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    org_id: str
    user_id: str
    thread_id: str