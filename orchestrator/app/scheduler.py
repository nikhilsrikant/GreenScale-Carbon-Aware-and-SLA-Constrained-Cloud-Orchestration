from __future__ import annotations

from dataclasses import dataclass
from math import inf

from .carbon_provider import CarbonProvider
from .models import Priority, RegionEndpoint, RegionScore, WorkloadRequest


@dataclass(frozen=True)
class SchedulerWeights:
    alpha_latency: float = 0.45
    beta_cost: float = 0.20
    gamma_carbon: float = 0.25
    delta_coldstart: float = 0.10

    def normalized(self) -> "SchedulerWeights":
        total = self.alpha_latency + self.beta_cost + self.gamma_carbon + self.delta_coldstart
        if total <= 0:
            return SchedulerWeights()
        return SchedulerWeights(
            alpha_latency=self.alpha_latency / total,
            beta_cost=self.beta_cost / total,
            gamma_carbon=self.gamma_carbon / total,
            delta_coldstart=self.delta_coldstart / total,
        )


class CarbonAwareScheduler:
    def __init__(
        self,
        regions: list[RegionEndpoint],
        carbon_provider: CarbonProvider,
        weights: SchedulerWeights,
        strict_slo: bool = True,
    ) -> None:
        if not regions:
            raise ValueError("At least one region endpoint is required")
        self.regions = regions
        self.carbon_provider = carbon_provider
        self.weights = weights.normalized()
        self.strict_slo = strict_slo

    async def rank(self, request: WorkloadRequest, workload: str | None = None) -> list[RegionScore]:
        carbon_values: dict[str, float] = {}
        for region in self.regions:
            carbon_values[region.name] = await self.carbon_provider.get_carbon_intensity(
                region.zone,
                region.carbon_gco2_kwh,
            )

        max_latency = max((r.base_latency_ms + r.cold_start_ms for r in self.regions), default=1.0)
        max_carbon = max(carbon_values.values(), default=1.0)
        max_cost = max((r.cost_per_million_requests for r in self.regions), default=1.0)
        max_cold = max((r.cold_start_ms for r in self.regions), default=1.0)

        scores = []
        for region in self.regions:
            carbon_intensity = carbon_values[region.name]
            priority_multiplier = self._priority_latency_multiplier(request.priority)
            estimated_latency = (region.base_latency_ms + 0.35 * region.cold_start_ms) * priority_multiplier
            estimated_carbon = request.estimated_energy_kwh * carbon_intensity
            estimated_cost = region.cost_per_million_requests / 1_000_000.0
            slo_violation = estimated_latency > request.slo_ms

            latency_component = self._safe_norm(estimated_latency, max_latency)
            carbon_component = self._safe_norm(carbon_intensity, max_carbon)
            cost_component = self._safe_norm(region.cost_per_million_requests, max_cost)
            cold_component = self._safe_norm(region.cold_start_ms, max_cold)

            score = (
                self.weights.alpha_latency * latency_component
                + self.weights.beta_cost * cost_component
                + self.weights.gamma_carbon * carbon_component
                + self.weights.delta_coldstart * cold_component
            )

            if slo_violation:
                score += self._slo_penalty(estimated_latency, request.slo_ms)

            if request.priority == Priority.delay_tolerant and request.deadline_seconds:
                score *= 0.95

            scores.append(
                RegionScore(
                    region=region,
                    score=score,
                    estimated_latency_ms=estimated_latency,
                    estimated_carbon_gco2=estimated_carbon,
                    estimated_cost_usd=estimated_cost,
                    slo_violation_risk=slo_violation,
                    components={
                        "latency": latency_component,
                        "carbon": carbon_component,
                        "cost": cost_component,
                        "cold_start": cold_component,
                    },
                )
            )

        ranked = sorted(scores, key=lambda item: item.score)
        if self.strict_slo:
            feasible = [score for score in ranked if not score.slo_violation_risk]
            if feasible:
                return feasible + [score for score in ranked if score.slo_violation_risk]
        return ranked

    async def choose(self, request: WorkloadRequest, workload: str | None = None) -> RegionScore:
        ranked = await self.rank(request, workload)
        if not ranked:
            raise RuntimeError("No candidate regions are available")
        return ranked[0]

    @staticmethod
    def _safe_norm(value: float, maximum: float) -> float:
        if maximum <= 0:
            return 0.0
        return max(0.0, min(1.0, value / maximum))

    @staticmethod
    def _slo_penalty(estimated_latency_ms: float, slo_ms: int) -> float:
        if slo_ms <= 0:
            return inf
        overage = max(0.0, estimated_latency_ms - slo_ms)
        return 1.0 + overage / slo_ms

    @staticmethod
    def _priority_latency_multiplier(priority: Priority) -> float:
        if priority == Priority.latency_critical:
            return 1.15
        if priority == Priority.delay_tolerant:
            return 0.90
        return 1.0
