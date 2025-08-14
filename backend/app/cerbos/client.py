from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..core.config import get_settings
from .real_client import CerbosHTTPClient as _Real


@dataclass
class CerbosHealth:
    ok: bool
    host: Optional[str]
    error: Optional[str] = None


class CerbosClientStub:
    """Lightweight Cerbos client placeholder.

    Replace with real gRPC/HTTP client integration.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def health(self) -> CerbosHealth:
        if not self.settings.cerbos_host:
            return CerbosHealth(ok=False, host=None, error="CERBOS host not configured")
        # In a real client, attempt a ping to host here.
        return CerbosHealth(ok=True, host=self.settings.cerbos_host)

    def authorize(self, roles: list[str], resource: str, action: str) -> bool:
        """Very simple authorization logic to simulate Cerbos decisions.

        - admin: allow all
        - user: allow read on demo resource
        - guest: deny
        """
        if "admin" in roles:
            return True
        if "user" in roles and resource == "demo" and action == "read":
            return True
        return False


def get_cerbos_client():
    settings = get_settings()
    if settings.cerbos_use_stub:
        return CerbosClientStub()
    return _Real()


cerbos_client = get_cerbos_client()
