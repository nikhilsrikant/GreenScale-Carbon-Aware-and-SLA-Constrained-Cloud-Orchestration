from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx


@dataclass
class CarbonProvider:
    """Carbon intensity provider.

    The MVP works without external credentials by using each region's configured
    `carbon_gco2_kwh`. If an Electricity Maps token is supplied, this class can
    query live zone-level carbon intensity. The API shape is isolated here so
    experiments can swap in historical traces later.
    """

    token: str | None = None
    ttl_seconds: int = 900
    timeout_seconds: float = 3.0
    _cache: dict[str, tuple[float, float]] = field(default_factory=dict)

    async def get_carbon_intensity(self, zone: str | None, fallback: float) -> float:
        if not zone or not self.token:
            return fallback

        now = time.time()
        cached = self._cache.get(zone)
        if cached and now - cached[0] < self.ttl_seconds:
            return cached[1]

        url = "https://api.electricitymap.org/v3/carbon-intensity/latest"
        headers = {"auth-token": self.token}
        params = {"zone": zone}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                value = float(data["carbonIntensity"])
                self._cache[zone] = (now, value)
                return value
        except Exception:
            return fallback
