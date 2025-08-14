from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import httpx

from ..core.config import get_settings


@dataclass
class CerbosHealth:
    ok: bool
    host: Optional[str]
    error: Optional[str] = None


class CerbosHTTPClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base = f"http://{self.settings.cerbos_host}" if self.settings.cerbos_host else None

    def health(self) -> CerbosHealth:
        if not self.base:
            return CerbosHealth(ok=False, host=None, error="CERBOS host not configured")
        try:
            # Cerbos exposes /_cerbos/health on http port by default
            url = f"{self.base}/_cerbos/health"
            r = httpx.get(url, timeout=2.0)
            return CerbosHealth(ok=r.status_code == 200, host=self.settings.cerbos_host, error=None)
        except Exception as e:
            return CerbosHealth(ok=False, host=self.settings.cerbos_host, error=str(e))

    def authorize(self, roles: list[str], resource: str, action: str) -> bool:
        # Placeholder: In real integration, call Cerbos check API
        # For now, deny by default to avoid false positives
        return False
