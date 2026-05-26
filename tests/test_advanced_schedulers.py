from __future__ import annotations

from orchestrator.app.models import RegionScore, WorkloadRequest
from orchestrator.app.pareto import ParetoAwareScheduler
from orchestrator.app.rl_scheduler import EpsilonGreedyRLScheduler


def test_rl_state_key_buckets_strict_interactive_relaxed() -> None:
    assert "strict" in EpsilonGreedyRLScheduler.state_key(WorkloadRequest(slo_ms=180), "ml")
    assert "interactive" in EpsilonGreedyRLScheduler.state_key(WorkloadRequest(slo_ms=450), "api")
    assert "relaxed" in EpsilonGreedyRLScheduler.state_key(WorkloadRequest(slo_ms=1200), "batch")


def test_rl_reward_penalizes_slo_violation(sample_score: RegionScore | None = None) -> None:
    # Build a minimal object using existing pydantic model constructors indirectly.
    from orchestrator.app.models import RegionEndpoint

    region = RegionEndpoint(name="r1", provider="p", url="http://example.com", base_latency_ms=100)
    score = RegionScore(
        region=region,
        score=0.5,
        estimated_latency_ms=100,
        estimated_carbon_gco2=0.1,
        estimated_cost_usd=0.000001,
        slo_violation_risk=False,
        components={"carbon": 0.2, "cost": 0.1, "latency": 0.2, "cold_start": 0.1},
    )
    ok = EpsilonGreedyRLScheduler.reward(WorkloadRequest(slo_ms=500), score, {"elapsed_ms": 100, "cold_start": False}, True)
    bad = EpsilonGreedyRLScheduler.reward(WorkloadRequest(slo_ms=100), score, {"elapsed_ms": 250, "cold_start": True}, True)
    assert ok > bad


def test_pareto_dominance() -> None:
    from orchestrator.app.models import RegionEndpoint

    r1 = RegionEndpoint(name="a", provider="p", url="http://a.example")
    r2 = RegionEndpoint(name="b", provider="p", url="http://b.example")
    better = RegionScore(region=r1, score=0.1, estimated_latency_ms=10, estimated_carbon_gco2=0.1, estimated_cost_usd=0.1, slo_violation_risk=False, components={"latency": 0.1, "carbon": 0.1, "cost": 0.1, "cold_start": 0.1})
    worse = RegionScore(region=r2, score=0.9, estimated_latency_ms=20, estimated_carbon_gco2=0.2, estimated_cost_usd=0.2, slo_violation_risk=False, components={"latency": 0.2, "carbon": 0.2, "cost": 0.2, "cold_start": 0.2})
    assert ParetoAwareScheduler._dominates(better, worse)
    assert not ParetoAwareScheduler._dominates(worse, better)
