from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .memory.base import MemoryDocument, MemoryQuery, MemoryStore
from .models import (
    AssistRequest,
    AssistResponse,
    FeedbackRequest,
    FeedbackResponse,
    IncidentCreateRequest,
    IncidentCreateResponse,
    MemoryHitView,
    PlanCard,
    SeedResponse,
    SubscriptionRequest,
    SubscriptionResponse,
    SubscriptionStatsResponse,
)
from .reasoning import build_plan_bundle


OUTCOME_SCORE = {"resolved": 1.0, "partial": 0.65, "failed": 0.2, "unknown": 0.5}


class IncidentService:
    def __init__(self, store: MemoryStore, subscriptions_file: Path | None = None):
        self.store = store
        self.sessions: dict[str, dict[str, Any]] = {}
        self.subscriptions_file = subscriptions_file

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _incident_summary(self, request: IncidentCreateRequest) -> str:
        parts = [
            f"Service: {request.service}",
            f"Severity: {request.severity}",
            f"Symptoms: {'; '.join(request.symptoms)}",
            f"Root cause: {request.root_cause}",
            f"Resolution: {'; '.join(request.resolution_steps)}",
            f"Prevention: {request.prevention}",
        ]
        return " | ".join(x for x in parts if x.strip())

    def retain_incident(self, request: IncidentCreateRequest) -> IncidentCreateResponse:
        outcome = request.outcome if request.outcome in OUTCOME_SCORE else "unknown"
        document = MemoryDocument(
            memory_id=f"incident::{request.incident_id}",
            kind="incident",
            incident_id=request.incident_id,
            service=request.service,
            severity=request.severity,
            symptoms=request.symptoms,
            root_cause=request.root_cause,
            actions=request.resolution_steps,
            outcome=outcome,
            summary=self._incident_summary(request),
            tags=request.tags,
            created_at=self._now(),
            success_score=OUTCOME_SCORE[outcome],
            extra={"timeline": request.timeline, "prevention": request.prevention},
        )
        memory_id = self.store.retain(document)
        return IncidentCreateResponse(memory_id=memory_id, status="stored")

    def assist(self, request: AssistRequest) -> AssistResponse:
        session_id = request.session_id.strip() or f"session-{uuid4().hex[:8]}"
        query_id = f"query-{uuid4().hex[:10]}"
        query = MemoryQuery(
            service=request.service,
            severity=request.severity,
            symptoms=request.symptoms,
            objective=request.objective,
            logs=request.logs,
            tags=request.tags,
            top_k=request.top_k,
        )
        recalls = self.store.recall(query)
        plan_bundle = build_plan_bundle(request, recalls)
        with_card = PlanCard(
            title="Memory-Augmented Plan",
            confidence=round(plan_bundle.with_memory_confidence, 2),
            steps=plan_bundle.with_memory_steps,
            rationale=plan_bundle.with_memory_rationale,
            risk_flags=plan_bundle.with_memory_risk_flags,
        )
        without_card = PlanCard(
            title="No-Memory Baseline",
            confidence=round(plan_bundle.without_memory_confidence, 2),
            steps=plan_bundle.without_memory_steps,
            rationale=plan_bundle.without_memory_rationale,
            risk_flags=plan_bundle.without_memory_risk_flags,
        )
        memory_boost = round(with_card.confidence - without_card.confidence, 2)
        hits = [
            MemoryHitView(
                memory_id=match.memory.memory_id,
                incident_id=match.memory.incident_id,
                service=match.memory.service,
                score=round(match.score, 3),
                root_cause=match.memory.root_cause,
                actions=match.memory.actions,
                outcome=match.memory.outcome,
                summary=match.memory.summary,
            )
            for match in recalls
        ]
        self.sessions[query_id] = {
            "session_id": session_id,
            "request": request.model_dump(),
            "memory_ids": [x.memory_id for x in hits],
            "created_at": self._now(),
        }
        return AssistResponse(
            query_id=query_id,
            session_id=session_id,
            memory_boost=memory_boost,
            without_memory=without_card,
            with_memory=with_card,
            recalled_memories=hits,
            tactical_takeaways=plan_bundle.tactical_takeaways,
        )

    def feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        context = self.sessions.get(request.query_id)
        if not context:
            raise ValueError("Unknown query_id")
        notes = request.notes.strip()
        summary_parts = [
            f"Feedback for {request.query_id}",
            f"Outcome: {request.outcome}",
            f"Useful steps: {'; '.join(request.useful_steps)}",
            notes,
        ]
        summary = " | ".join(x for x in summary_parts if x)
        document = MemoryDocument(
            memory_id=f"feedback::{uuid4().hex}",
            kind="feedback",
            incident_id=request.query_id,
            service=context["request"]["service"],
            severity=context["request"]["severity"],
            symptoms=context["request"]["symptoms"],
            root_cause=notes or "feedback-signal",
            actions=request.useful_steps,
            outcome=request.outcome,
            summary=summary,
            tags=context["request"].get("tags", []),
            created_at=self._now(),
            success_score=OUTCOME_SCORE.get(request.outcome, 0.5),
            extra={"memory_ids": context.get("memory_ids", [])},
        )
        memory_id = self.store.retain(document)
        return FeedbackResponse(status="stored", memory_id=memory_id)

    def seed(self) -> SeedResponse:
        records = [
            IncidentCreateRequest(
                incident_id="INC-2026-0001",
                service="payments-api",
                severity="critical",
                symptoms=["card authorizations timing out", "spike in 504 gateway errors"],
                timeline=["10:03 latency crossed 2s", "10:08 checkout failures reached 32%"],
                root_cause="Redis connection pool exhaustion after aggressive checkout cache warmup",
                resolution_steps=["Scale Redis read replicas", "Reduce warmup concurrency to 25 workers", "Recycle stale payment worker pods"],
                prevention="Install checkout cache warmup circuit breaker and pool saturation alert",
                tags=["redis", "timeouts", "checkout"],
                outcome="resolved",
            ),
            IncidentCreateRequest(
                incident_id="INC-2026-0002",
                service="payments-api",
                severity="high",
                symptoms=["duplicate capture attempts", "idempotency key mismatch"],
                timeline=["14:11 retry queue backlog started", "14:19 duplicate capture alarms fired"],
                root_cause="Missing idempotency header propagation in async retry consumer",
                resolution_steps=["Patch retry consumer header mapping", "Replay only non-committed capture jobs", "Add temporary duplicate-capture blocklist"],
                prevention="Contract test for idempotency headers across sync and async paths",
                tags=["idempotency", "queue", "billing"],
                outcome="resolved",
            ),
            IncidentCreateRequest(
                incident_id="INC-2026-0003",
                service="auth-service",
                severity="critical",
                symptoms=["token verification failing", "login success dropped to 41%"],
                timeline=["09:40 auth error rate jumped", "09:49 support ticket surge started"],
                root_cause="Expired JWKS cache after identity provider key rotation",
                resolution_steps=["Force JWKS cache refresh", "Lower cache TTL from 6h to 10m", "Backfill failed login sessions"],
                prevention="Key-rotation webhook to invalidate cache immediately",
                tags=["jwt", "cache", "identity-provider"],
                outcome="resolved",
            ),
            IncidentCreateRequest(
                incident_id="INC-2026-0004",
                service="search-indexer",
                severity="high",
                symptoms=["catalog search returning stale products", "index lag exceeded 45 minutes"],
                timeline=["18:01 index lag alarm", "18:07 queue depth exceeded threshold"],
                root_cause="Kafka consumer rebalance loop caused by uneven partition ownership",
                resolution_steps=["Pin partition assignment by consumer group", "Increase heartbeat interval", "Rehydrate missed indexing jobs"],
                prevention="Add rebalance loop detector with automatic group reset",
                tags=["kafka", "search", "indexing"],
                outcome="resolved",
            ),
            IncidentCreateRequest(
                incident_id="INC-2026-0005",
                service="orders-service",
                severity="medium",
                symptoms=["order confirmations delayed", "retry count spike"],
                timeline=["11:15 email queue delay started", "11:28 retries doubled"],
                root_cause="SMTP provider throttling after sudden campaign traffic",
                resolution_steps=["Switch to backup SMTP region", "Throttle campaign send rate", "Enable priority queue for transactional emails"],
                prevention="Dedicated transactional channel and per-provider rate budgets",
                tags=["smtp", "email", "throttling"],
                outcome="resolved",
            ),
            IncidentCreateRequest(
                incident_id="INC-2026-0006",
                service="analytics-api",
                severity="high",
                symptoms=["query latency above 6 seconds", "cpu saturation on read replicas"],
                timeline=["07:32 p95 latency breach", "07:41 dashboard timeouts reported"],
                root_cause="Runaway ad-hoc query pattern bypassed materialized views",
                resolution_steps=["Apply query guardrails by tenant", "Force materialized view route", "Kill long-running sessions above 30s"],
                prevention="Tenant-level query budget and strict query planner hints",
                tags=["postgres", "latency", "analytics"],
                outcome="resolved",
            ),
        ]
        for record in records:
            self.retain_incident(record)
        return SeedResponse(inserted=len(records), status="seeded")

    def demo_scenarios(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "payments-critical",
                "name": "Payments timeout storm",
                "payload": {
                    "service": "payments-api",
                    "severity": "critical",
                    "objective": "restore checkout success above 97% in under 30 minutes",
                    "symptoms": ["gateway timeout in card authorization", "checkout retries increased 4x", "redis pool saturation alerts"],
                    "logs": "TimeoutError: redis connection pool exhausted on payment-session-cache",
                    "tags": ["redis", "checkout", "timeouts"],
                    "top_k": 4,
                },
            },
            {
                "id": "auth-jwt-break",
                "name": "Auth signature mismatch",
                "payload": {
                    "service": "auth-service",
                    "severity": "critical",
                    "objective": "recover login conversion above 95%",
                    "symptoms": ["token verification failing", "invalid signature spike"],
                    "logs": "JWT signature mismatch after identity provider key rotation",
                    "tags": ["jwt", "identity-provider", "cache"],
                    "top_k": 4,
                },
            },
            {
                "id": "search-index-lag",
                "name": "Search index lag",
                "payload": {
                    "service": "search-indexer",
                    "severity": "high",
                    "objective": "reduce index lag below 5 minutes",
                    "symptoms": ["catalog search stale products", "consumer rebalance loop"],
                    "logs": "Kafka heartbeat timeout and partition rebalance churn",
                    "tags": ["kafka", "indexing", "search"],
                    "top_k": 4,
                },
            },
        ]

    def status(self) -> dict[str, Any]:
        stats = self.store.stats()
        return {
            "backend": stats.get("backend", "local"),
            "memory_entries": int(stats.get("entries", 0)),
            "sessions": len(self.sessions),
            "available": True,
        }

    def _read_subscriptions(self) -> list[dict[str, Any]]:
        if not self.subscriptions_file:
            return []
        if not self.subscriptions_file.exists():
            return []
        try:
            payload = json.loads(self.subscriptions_file.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError):
            return []
        return []

    def _write_subscriptions(self, records: list[dict[str, Any]]) -> None:
        if not self.subscriptions_file:
            return
        self.subscriptions_file.parent.mkdir(parents=True, exist_ok=True)
        self.subscriptions_file.write_text(json.dumps(records, indent=2, ensure_ascii=True), encoding="utf-8")

    def subscribe(self, request: SubscriptionRequest) -> SubscriptionResponse:
        records = self._read_subscriptions()
        normalized_email = request.email.strip().lower()
        normalized_team = request.team_name.strip().lower()
        for record in records:
            if record.get("email") == normalized_email and str(record.get("team_name", "")).strip().lower() == normalized_team:
                return SubscriptionResponse(status="already_registered", record_id=str(record.get("record_id", "")))
        record_id = f"sub-{uuid4().hex[:10]}"
        records.append(
            {
                "record_id": record_id,
                "email": normalized_email,
                "team_name": request.team_name.strip(),
                "team_size": request.team_size,
                "plan": request.plan,
                "use_case": request.use_case.strip(),
                "created_at": self._now(),
            }
        )
        self._write_subscriptions(records)
        return SubscriptionResponse(status="queued", record_id=record_id)

    def subscription_stats(self) -> SubscriptionStatsResponse:
        records = self._read_subscriptions()
        counts = {"starter": 0, "growth": 0, "enterprise": 0}
        for record in records:
            plan = str(record.get("plan", "")).strip().lower()
            if plan in counts:
                counts[plan] += 1
        return SubscriptionStatsResponse(total=len(records), starter=counts["starter"], growth=counts["growth"], enterprise=counts["enterprise"])
