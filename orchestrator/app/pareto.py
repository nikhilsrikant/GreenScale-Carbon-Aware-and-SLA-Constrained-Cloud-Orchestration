from __future__ import annotations

from .models import RegionScore, WorkloadRequest
from .scheduler import CarbonAwareScheduler, SchedulerWeights


class ParetoAwareScheduler:
    """Pareto-front wrapper around the weighted GreenScale scheduler.

    The base scheduler produces normalized objective components for latency,
    carbon, cost, and cold-start risk. This wrapper first filters the ranked
    candidates to the non-dominated set and then uses the weighted score as a
    deterministic tie-breaker. A region A dominates region B when A is no worse
    on every objective and strictly better on at least one objective.
    """

    def __init__(self, base_scheduler: CarbonAwareScheduler) -> None:
        self.base_scheduler = base_scheduler
        self.weights: SchedulerWeights = base_scheduler.weights
        self.strict_slo = base_scheduler.strict_slo

    async def rank(self, request: WorkloadRequest, workload: str | None = None) -> list[RegionScore]:
        ranked = await self.base_scheduler.rank(request)
        if len(ranked) <= 1:
            return ranked
        front = self._pareto_front(ranked)
        dominated = [candidate for candidate in ranked if candidate not in front]
        return sorted(front, key=lambda item: item.score) + sorted(dominated, key=lambda item: item.score)

    async def choose(self, request: WorkloadRequest, workload: str | None = None) -> RegionScore:
        ranked = await self.rank(request, workload)
        if not ranked:
            raise RuntimeError("No candidate regions are available")
        return ranked[0]

    @staticmethod
    def _objectives(item: RegionScore) -> tuple[float, float, float, float]:
        return (
            item.components.get("latency", 0.0),
            item.components.get("carbon", 0.0),
            item.components.get("cost", 0.0),
            item.components.get("cold_start", 0.0),
        )

    @classmethod
    def _dominates(cls, left: RegionScore, right: RegionScore) -> bool:
        left_obj = cls._objectives(left)
        right_obj = cls._objectives(right)
        no_worse = all(l <= r for l, r in zip(left_obj, right_obj, strict=False))
        strictly_better = any(l < r for l, r in zip(left_obj, right_obj, strict=False))
        return no_worse and strictly_better

    @classmethod
    def _pareto_front(cls, candidates: list[RegionScore]) -> list[RegionScore]:
        front: list[RegionScore] = []
        for candidate in candidates:
            if not any(cls._dominates(other, candidate) for other in candidates if other is not candidate):
                front.append(candidate)
        return front
