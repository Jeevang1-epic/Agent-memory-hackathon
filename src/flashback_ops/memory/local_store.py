from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import json
import math
from pathlib import Path
import re
from typing import Any

from .base import MemoryDocument, MemoryMatch, MemoryQuery, MemoryStore


TOKEN_RE = re.compile(r"[a-z0-9_./-]+")
OUTCOME_SCORE = {"resolved": 1.0, "partial": 0.65, "failed": 0.2, "unknown": 0.5}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_text(text: str) -> list[str]:
    text = text.lower()
    return TOKEN_RE.findall(text)


def _token_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    common = len(left.intersection(right))
    return common / (math.sqrt(len(left)) * math.sqrt(len(right)))


def _days_old(value: str) -> float:
    if not value:
        return 365.0
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return 365.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    delta = datetime.now(UTC) - dt
    return max(0.0, delta.total_seconds() / 86400.0)


class LocalMemoryStore(MemoryStore):
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._documents: list[MemoryDocument] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._documents = []
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self._documents = []
            return
        docs: list[MemoryDocument] = []
        for item in raw:
            if isinstance(item, dict):
                docs.append(self._from_raw(item))
        self._documents = docs

    def _save(self) -> None:
        payload = [x.to_dict() for x in self._documents]
        self.path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _from_raw(self, item: dict[str, Any]) -> MemoryDocument:
        outcome = str(item.get("outcome", "unknown")).lower()
        return MemoryDocument(
            memory_id=str(item.get("memory_id", "")),
            kind=str(item.get("kind", "incident")),
            incident_id=str(item.get("incident_id", "")),
            service=str(item.get("service", "")),
            severity=str(item.get("severity", "medium")),
            symptoms=[str(x) for x in item.get("symptoms", []) if isinstance(x, str)],
            root_cause=str(item.get("root_cause", "")),
            actions=[str(x) for x in item.get("actions", []) if isinstance(x, str)],
            outcome=outcome if outcome in OUTCOME_SCORE else "unknown",
            summary=str(item.get("summary", "")),
            tags=[str(x) for x in item.get("tags", []) if isinstance(x, str)],
            created_at=str(item.get("created_at", "")),
            success_score=float(item.get("success_score", OUTCOME_SCORE.get(outcome, 0.5))),
            extra=item.get("extra", {}) if isinstance(item.get("extra", {}), dict) else {},
        )

    def retain(self, document: MemoryDocument) -> str:
        if not document.created_at:
            document.created_at = _now_iso()
        if document.outcome not in OUTCOME_SCORE:
            document.outcome = "unknown"
        if document.success_score <= 0:
            document.success_score = OUTCOME_SCORE.get(document.outcome, 0.5)
        for idx, existing in enumerate(self._documents):
            if existing.memory_id == document.memory_id:
                self._documents[idx] = document
                self._save()
                return document.memory_id
        self._documents.append(document)
        self._save()
        return document.memory_id

    def _score_document(self, query: MemoryQuery, document: MemoryDocument) -> tuple[float, str]:
        query_tokens = set(_normalize_text(query.text))
        symptom_tokens = set(_normalize_text(" ".join(query.symptoms)))
        tag_tokens = set(_normalize_text(" ".join(query.tags)))
        document_tokens = set(
            _normalize_text(
                " ".join(
                    [
                        document.service,
                        document.severity,
                        document.summary,
                        document.root_cause,
                        " ".join(document.actions),
                        " ".join(document.symptoms),
                        " ".join(document.tags),
                    ]
                )
            )
        )
        lexical = _token_score(query_tokens, document_tokens)
        symptom_similarity = _token_score(symptom_tokens, set(_normalize_text(" ".join(document.symptoms))))
        tag_similarity = _token_score(tag_tokens, set(_normalize_text(" ".join(document.tags))))
        service_bonus = 0.25 if query.service.strip().lower() == document.service.strip().lower() else 0.0
        severity_bonus = 0.08 if query.severity.strip().lower() == document.severity.strip().lower() else 0.0
        recency_bonus = math.exp(-_days_old(document.created_at) / 45.0) * 0.1
        outcome_bonus = max(0.0, min(document.success_score, 1.0)) * 0.22
        total = lexical * 0.42 + symptom_similarity * 0.18 + tag_similarity * 0.08 + service_bonus + severity_bonus + recency_bonus + outcome_bonus
        total = max(0.0, min(total, 1.0))
        parts = []
        if service_bonus > 0:
            parts.append("same service")
        if severity_bonus > 0:
            parts.append("same severity")
        if symptom_similarity > 0.1:
            parts.append("symptom overlap")
        if outcome_bonus > 0.15:
            parts.append("high past resolution rate")
        if recency_bonus > 0.06:
            parts.append("recent signal")
        return total, ", ".join(parts) if parts else "lexical similarity"

    def recall(self, query: MemoryQuery) -> list[MemoryMatch]:
        scored: list[MemoryMatch] = []
        for document in self._documents:
            score, rationale = self._score_document(query, document)
            if score > 0.03:
                scored.append(MemoryMatch(memory=document, score=round(score, 4), rationale=rationale))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[: query.top_k]

    def stats(self) -> dict[str, Any]:
        service_counts = Counter(x.service for x in self._documents if x.service)
        outcome_counts = Counter(x.outcome for x in self._documents if x.outcome)
        return {
            "backend": "local",
            "entries": len(self._documents),
            "service_counts": dict(service_counts),
            "outcome_counts": dict(outcome_counts),
        }
