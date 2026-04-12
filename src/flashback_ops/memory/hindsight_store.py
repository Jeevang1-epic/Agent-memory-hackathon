from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx

from .base import MemoryDocument, MemoryMatch, MemoryQuery, MemoryStore
from .local_store import LocalMemoryStore


class HindsightMemoryStore(MemoryStore):
    def __init__(self, base_url: str, api_key: str, bank_id: str, local_fallback: LocalMemoryStore):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.bank_id = bank_id
        self.local_fallback = local_fallback
        self.enabled = bool(self.base_url and self.api_key and self.bank_id)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _post(self, payload: dict[str, Any], paths: list[str]) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Hindsight backend is not configured")
        with httpx.Client(timeout=8.0) as client:
            for path in paths:
                url = f"{self.base_url}{path}"
                response = client.post(url, headers=self._headers(), json=payload)
                if response.status_code < 400:
                    if not response.content:
                        return {}
                    parsed = response.json()
                    return parsed if isinstance(parsed, dict) else {}
            raise RuntimeError("Hindsight endpoint rejected request")

    def retain(self, document: MemoryDocument) -> str:
        self.local_fallback.retain(document)
        payload = {
            "bank_id": self.bank_id,
            "content": document.summary,
            "tags": document.tags,
            "metadata": document.to_dict(),
        }
        try:
            self._post(payload, ["/retain", "/v1/retain", "/api/retain"])
        except Exception:
            return document.memory_id
        return document.memory_id

    def _parse_remote_results(self, raw: dict[str, Any], top_k: int) -> list[MemoryMatch]:
        items = raw.get("results") or raw.get("matches") or raw.get("data") or []
        parsed: list[MemoryMatch] = []
        for item in items[:top_k]:
            if not isinstance(item, dict):
                continue
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            incident_id = str(metadata.get("incident_id") or item.get("id") or "")
            memory_id = str(metadata.get("memory_id") or item.get("id") or f"hindsight::{uuid4().hex}")
            content = str(item.get("content") or metadata.get("summary") or "")
            score_raw = item.get("score") if item.get("score") is not None else item.get("distance")
            try:
                score = float(score_raw)
            except (TypeError, ValueError):
                score = 0.45
            if score > 1:
                score = 1 / (1 + score)
            doc = MemoryDocument(
                memory_id=memory_id,
                kind=str(metadata.get("kind") or "incident"),
                incident_id=incident_id,
                service=str(metadata.get("service") or ""),
                severity=str(metadata.get("severity") or "medium"),
                symptoms=[str(x) for x in metadata.get("symptoms", []) if isinstance(x, str)],
                root_cause=str(metadata.get("root_cause") or ""),
                actions=[str(x) for x in metadata.get("actions", []) if isinstance(x, str)],
                outcome=str(metadata.get("outcome") or "unknown"),
                summary=content,
                tags=[str(x) for x in metadata.get("tags", []) if isinstance(x, str)],
                created_at=str(metadata.get("created_at") or datetime.now(UTC).isoformat()),
                success_score=float(metadata.get("success_score") or 0.5),
                extra=metadata.get("extra", {}),
            )
            parsed.append(MemoryMatch(memory=doc, score=max(0.0, min(score, 1.0)), rationale="remote hindsight match"))
        return parsed

    def recall(self, query: MemoryQuery) -> list[MemoryMatch]:
        if not self.enabled:
            return self.local_fallback.recall(query)
        payload = {
            "bank_id": self.bank_id,
            "query": query.text,
            "top_k": query.top_k,
            "tags": query.tags,
        }
        try:
            raw = self._post(payload, ["/recall", "/v1/recall", "/api/recall"])
            parsed = self._parse_remote_results(raw, query.top_k)
            if parsed:
                return parsed
        except Exception:
            pass
        return self.local_fallback.recall(query)

    def stats(self) -> dict[str, Any]:
        base = self.local_fallback.stats()
        base["backend"] = "hindsight" if self.enabled else "local-fallback"
        base["hindsight_enabled"] = self.enabled
        base["bank_id"] = self.bank_id
        return base
