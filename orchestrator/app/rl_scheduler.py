from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .models import Priority, RegionScore, WorkloadRequest
from .scheduler import CarbonAwareScheduler, SchedulerWeights


class EpsilonGreedyRLScheduler:
    """Lightweight online reinforcement-learning scheduler.

    This implementation is intentionally simple and transparent for research
    experiments. The base scheduler still computes feasible candidate regions.
    The RL layer learns a Q-value per (workload, priority, SLO bucket) state and
    region action. During exploitation it lowers the adjusted score of regions
    with historically better reward; during exploration it occasionally tries a
    different feasible region.
    """

    def __init__(
        self,
        base_scheduler: CarbonAwareScheduler,
        epsilon: float = 0.10,
        learning_rate: float = 0.20,
        discount: float = 0.0,
        qtable_path: str | None = None,
    ) -> None:
        self.base_scheduler = base_scheduler
        self.weights: SchedulerWeights = base_scheduler.weights
        self.strict_slo = base_scheduler.strict_slo
        self.epsilon = max(0.0, min(1.0, epsilon))
        self.learning_rate = max(0.0, min(1.0, learning_rate))
        self.discount = max(0.0, min(1.0, discount))
        self.qtable_path = Path(qtable_path) if qtable_path else None
        self.q_table: dict[str, dict[str, float]] = {}
        self._load()

    async def rank(self, request: WorkloadRequest, workload: str | None = None) -> list[RegionScore]:
        base_ranked = await self.base_scheduler.rank(request)
        if len(base_ranked) <= 1:
            return base_ranked

        state = self.state_key(request, workload)
        q_values = self.q_table.get(state, {})

        if random.random() < self.epsilon:
            exploration_pool = base_ranked[: min(3, len(base_ranked))]
            selected = random.choice(exploration_pool)
            return [selected] + [item for item in base_ranked if item.region.name != selected.region.name]

        # Base score is a cost to minimize; Q-value is learned reward to maximize.
        return sorted(base_ranked, key=lambda item: item.score - q_values.get(item.region.name, 0.0))

    async def choose(self, request: WorkloadRequest, workload: str | None = None) -> RegionScore:
        ranked = await self.rank(request, workload)
        if not ranked:
            raise RuntimeError("No candidate regions are available")
        return ranked[0]

    def observe(
        self,
        request: WorkloadRequest,
        workload: str,
        selected: RegionScore,
        worker_response: dict[str, Any] | None,
        success: bool = True,
    ) -> float:
        state = self.state_key(request, workload)
        action = selected.region.name
        reward = self.reward(request, selected, worker_response, success)
        current = self.q_table.setdefault(state, {}).get(action, 0.0)
        next_best = max(self.q_table.get(state, {}).values(), default=0.0)
        updated = current + self.learning_rate * (reward + self.discount * next_best - current)
        self.q_table[state][action] = updated
        self._save()
        return reward

    @staticmethod
    def state_key(request: WorkloadRequest, workload: str | None) -> str:
        if request.slo_ms <= 250:
            slo_bucket = "strict"
        elif request.slo_ms <= 750:
            slo_bucket = "interactive"
        else:
            slo_bucket = "relaxed"
        deadline_bucket = "deadline" if request.deadline_seconds else "no-deadline"
        priority = request.priority.value if isinstance(request.priority, Priority) else str(request.priority)
        return f"{workload or 'unknown'}|{priority}|{slo_bucket}|{deadline_bucket}"

    @staticmethod
    def reward(
        request: WorkloadRequest,
        selected: RegionScore,
        worker_response: dict[str, Any] | None,
        success: bool,
    ) -> float:
        if not success:
            return -2.0

        observed_latency_ms = selected.estimated_latency_ms
        cold_start = False
        if worker_response:
            observed_latency_ms = float(worker_response.get("elapsed_ms", observed_latency_ms))
            cold_start = bool(worker_response.get("cold_start", False))

        slo_ratio = observed_latency_ms / max(float(request.slo_ms), 1.0)
        slo_penalty = max(0.0, slo_ratio - 1.0)
        latency_penalty = min(2.0, slo_ratio)
        carbon_penalty = selected.components.get("carbon", 0.0)
        cost_penalty = selected.components.get("cost", 0.0)
        cold_penalty = 1.0 if cold_start else 0.0

        # Positive reward means a placement was fast, green, low-cost, and warm.
        return 1.0 - 0.45 * latency_penalty - 1.25 * slo_penalty - 0.25 * carbon_penalty - 0.15 * cost_penalty - 0.10 * cold_penalty

    def export_qtable(self) -> dict[str, dict[str, float]]:
        return self.q_table

    def _load(self) -> None:
        if not self.qtable_path or not self.qtable_path.exists():
            return
        try:
            data = json.loads(self.qtable_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.q_table = {
                    str(state): {str(action): float(value) for action, value in actions.items()}
                    for state, actions in data.items()
                    if isinstance(actions, dict)
                }
        except Exception:
            self.q_table = {}

    def _save(self) -> None:
        if not self.qtable_path:
            return
        try:
            self.qtable_path.parent.mkdir(parents=True, exist_ok=True)
            self.qtable_path.write_text(json.dumps(self.q_table, indent=2, sort_keys=True), encoding="utf-8")
        except Exception:
            # The scheduler must keep serving requests even if persistence fails.
            return
