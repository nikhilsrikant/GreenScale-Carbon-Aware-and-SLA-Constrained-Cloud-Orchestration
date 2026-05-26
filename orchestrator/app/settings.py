from __future__ import annotations

import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import RegionEndpoint


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    region_endpoints: str = Field(default="[]", alias="REGION_ENDPOINTS")
    electricity_maps_token: str | None = Field(default=None, alias="ELECTRICITY_MAPS_TOKEN")
    carbon_cache_ttl_seconds: int = Field(default=900, alias="CARBON_CACHE_TTL_SECONDS")
    carbon_api_timeout_seconds: float = Field(default=3.0, alias="CARBON_API_TIMEOUT_SECONDS")
    strict_slo: bool = Field(default=True, alias="STRICT_SLO")

    scheduler_policy: str = Field(default="weighted", alias="SCHEDULER_POLICY")
    rl_epsilon: float = Field(default=0.10, alias="RL_EPSILON")
    rl_learning_rate: float = Field(default=0.20, alias="RL_LEARNING_RATE")
    rl_discount: float = Field(default=0.0, alias="RL_DISCOUNT")
    rl_qtable_path: str | None = Field(default=None, alias="RL_QTABLE_PATH")

    scheduler_alpha_latency: float = Field(default=0.45, alias="SCHEDULER_ALPHA_LATENCY")
    scheduler_beta_cost: float = Field(default=0.20, alias="SCHEDULER_BETA_COST")
    scheduler_gamma_carbon: float = Field(default=0.25, alias="SCHEDULER_GAMMA_CARBON")
    scheduler_delta_coldstart: float = Field(default=0.10, alias="SCHEDULER_DELTA_COLDSTART")

    request_timeout_seconds: float = Field(default=10.0, alias="REQUEST_TIMEOUT_SECONDS")

    def regions(self) -> list[RegionEndpoint]:
        try:
            raw = json.loads(self.region_endpoints)
        except json.JSONDecodeError as exc:
            raise ValueError("REGION_ENDPOINTS must be valid JSON") from exc
        if not isinstance(raw, list):
            raise ValueError("REGION_ENDPOINTS must be a JSON list")
        regions = [RegionEndpoint.model_validate(item) for item in raw]
        return [region for region in regions if region.enabled]


@lru_cache
def get_settings() -> Settings:
    return Settings()
