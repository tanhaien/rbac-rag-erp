from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ..core.config import get_settings


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


cerbos_client = CerbosClientStub()
