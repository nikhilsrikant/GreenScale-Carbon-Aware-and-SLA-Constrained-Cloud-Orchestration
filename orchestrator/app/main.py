from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .carbon_provider import CarbonProvider
from .metrics import (
    DECISIONS_TOTAL,
    ESTIMATED_CARBON,
    ESTIMATED_COST,
    ORCHESTRATOR_LATENCY,
    REQUESTS_TOTAL,
    SCHEDULER_SCORE,
    SLO_BUDGET_UTILIZATION,
    SLO_RISK_TOTAL,
    WORKER_LATENCY,
)
from .models import InvocationResult, WorkloadRequest
from .pareto import ParetoAwareScheduler
from .rl_scheduler import EpsilonGreedyRLScheduler
from .scheduler import CarbonAwareScheduler, SchedulerWeights
from .settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    regions = settings.regions()
    if not regions:
        raise RuntimeError("No regions configured. Set REGION_ENDPOINTS.")
    app.state.settings = settings
    app.state.regions = regions
    app.state.carbon_provider = CarbonProvider(
        token=settings.electricity_maps_token,
        ttl_seconds=settings.carbon_cache_ttl_seconds,
        timeout_seconds=settings.carbon_api_timeout_seconds,
    )
    base_scheduler = CarbonAwareScheduler(
        regions=regions,
        carbon_provider=app.state.carbon_provider,
        weights=SchedulerWeights(
            alpha_latency=settings.scheduler_alpha_latency,
            beta_cost=settings.scheduler_beta_cost,
            gamma_carbon=settings.scheduler_gamma_carbon,
            delta_coldstart=settings.scheduler_delta_coldstart,
        ),
        strict_slo=settings.strict_slo,
    )
    policy = settings.scheduler_policy.strip().lower()
    if policy == "rl":
        app.state.scheduler = EpsilonGreedyRLScheduler(
            base_scheduler=base_scheduler,
            epsilon=settings.rl_epsilon,
            learning_rate=settings.rl_learning_rate,
            discount=settings.rl_discount,
            qtable_path=settings.rl_qtable_path,
        )
    elif policy == "pareto":
        app.state.scheduler = ParetoAwareScheduler(base_scheduler)
    else:
        app.state.scheduler = base_scheduler
    yield


app = FastAPI(
    title="GreenScale Orchestrator",
    version="0.1.0",
    description="Carbon-aware, SLA-constrained workload router for cloud experiments.",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "configured_regions": [region.name for region in app.state.regions],
        "strict_slo": app.state.settings.strict_slo,
        "scheduler_policy": app.state.settings.scheduler_policy,
        "weights": {
            "latency": app.state.scheduler.weights.alpha_latency,
            "cost": app.state.scheduler.weights.beta_cost,
            "carbon": app.state.scheduler.weights.gamma_carbon,
            "cold_start": app.state.scheduler.weights.delta_coldstart,
        },
    }


@app.get("/regions")
async def regions() -> list[dict[str, Any]]:
    ranked = await app.state.scheduler.rank(WorkloadRequest(), workload="region-preview")
    return [score.model_dump(mode="json") for score in ranked]


@app.get("/scheduler/qtable")
async def scheduler_qtable() -> dict[str, Any]:
    if hasattr(app.state.scheduler, "export_qtable"):
        return {"policy": app.state.settings.scheduler_policy, "q_table": app.state.scheduler.export_qtable()}
    return {"policy": app.state.settings.scheduler_policy, "q_table": {}}


@app.post("/invoke/{workload}", response_model=InvocationResult)
async def invoke(workload: str, request: WorkloadRequest) -> InvocationResult:
    started = time.perf_counter()
    REQUESTS_TOTAL.labels(workload=workload, priority=request.priority.value).inc()

    ranked = await app.state.scheduler.rank(request, workload=workload)
    if not ranked:
        raise HTTPException(status_code=503, detail="No candidate regions are available")

    last_error: str | None = None
    for selected in ranked:
        worker_started = time.perf_counter()
        try:
            worker_response = await call_worker(selected.region.url, workload, request)
            if hasattr(app.state.scheduler, "observe"):
                app.state.scheduler.observe(request, workload, selected, worker_response, success=True)
            observed_worker_seconds = time.perf_counter() - worker_started
            WORKER_LATENCY.labels(workload=workload, region=selected.region.name).observe(observed_worker_seconds)
            DECISIONS_TOTAL.labels(
                region=selected.region.name,
                provider=selected.region.provider,
                workload=workload,
            ).inc()
            SCHEDULER_SCORE.labels(
                region=selected.region.name,
                provider=selected.region.provider,
            ).observe(selected.score)
            ESTIMATED_CARBON.labels(
                region=selected.region.name,
                provider=selected.region.provider,
                workload=workload,
            ).observe(selected.estimated_carbon_gco2)
            ESTIMATED_COST.labels(
                region=selected.region.name,
                provider=selected.region.provider,
                workload=workload,
            ).observe(selected.estimated_cost_usd)
            if request.slo_ms > 0:
                SLO_BUDGET_UTILIZATION.labels(
                    region=selected.region.name,
                    workload=workload,
                ).observe(selected.estimated_latency_ms / request.slo_ms)
            if selected.slo_violation_risk:
                SLO_RISK_TOTAL.labels(region=selected.region.name, workload=workload).inc()
            ORCHESTRATOR_LATENCY.labels(workload=workload, region=selected.region.name).observe(time.perf_counter() - started)

            alternatives = [
                {
                    "region": item.region.name,
                    "provider": item.region.provider,
                    "score": item.score,
                    "estimated_latency_ms": item.estimated_latency_ms,
                    "estimated_carbon_gco2": item.estimated_carbon_gco2,
                    "estimated_cost_usd": item.estimated_cost_usd,
                    "slo_violation_risk": item.slo_violation_risk,
                    "components": item.components,
                }
                for item in ranked
            ]

            return InvocationResult(
                selected_region=selected.region.name,
                provider=selected.region.provider,
                workload=workload,
                scheduler_score=selected.score,
                estimated_latency_ms=selected.estimated_latency_ms,
                estimated_carbon_gco2=selected.estimated_carbon_gco2,
                estimated_cost_usd=selected.estimated_cost_usd,
                slo_ms=request.slo_ms,
                worker_response=worker_response,
                alternatives=alternatives,
            )
        except Exception as exc:
            last_error = f"{selected.region.name}: {exc}"
            continue

    raise HTTPException(status_code=503, detail={"message": "All candidate regions failed", "last_error": last_error})


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def call_worker(region_url: str, workload: str, request: WorkloadRequest) -> dict[str, Any]:
    settings = app.state.settings
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        response = await client.post(
            f"{region_url}/run/{workload}",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
        return response.json()
