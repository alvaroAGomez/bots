import time
from typing import Dict, List, Optional

from cauciones_bot.config import Config
from cauciones_bot.models import DatosCaucion


class CacheService:
    def __init__(self, ttl_seconds: int = Config.CACHE_TTL_SECONDS) -> None:
        self._cache: Dict[str, object] = {"timestamp": 0.0, "data": []}
        self._ttl = ttl_seconds

    def get(self) -> Optional[List[DatosCaucion]]:
        now = time.time()
        if self._cache["data"] and (now - self._cache["timestamp"] < self._ttl):
            return self._cache["data"]  # type: ignore[return-value]
        return None

    def set(self, data: List[DatosCaucion]) -> None:
        self._cache["data"] = data
        self._cache["timestamp"] = time.time()
