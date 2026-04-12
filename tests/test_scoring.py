from pathlib import Path

from flashback_ops.memory.base import MemoryDocument, MemoryQuery
from flashback_ops.memory.local_store import LocalMemoryStore


def test_local_recall_prefers_service_and_success(tmp_path: Path) -> None:
    store = LocalMemoryStore(tmp_path / "memory.json")
    store.retain(
        MemoryDocument(
            memory_id="m-1",
            kind="incident",
            incident_id="INC-1",
            service="payments-api",
            severity="critical",
            symptoms=["timeouts", "redis saturation"],
            root_cause="redis pool exhaustion",
            actions=["scale redis"],
            outcome="resolved",
            summary="payments outage due to redis pool exhaustion",
            tags=["redis", "checkout"],
            success_score=1.0,
        )
    )
    store.retain(
        MemoryDocument(
            memory_id="m-2",
            kind="incident",
            incident_id="INC-2",
            service="search-api",
            severity="critical",
            symptoms=["timeouts", "index drift"],
            root_cause="queue starvation",
            actions=["restart index workers"],
            outcome="failed",
            summary="search incidents with timeout and index drift",
            tags=["search"],
            success_score=0.2,
        )
    )
    matches = store.recall(
        MemoryQuery(
            service="payments-api",
            severity="critical",
            symptoms=["timeouts", "checkout failing"],
            objective="restore payments",
            logs="redis saturation",
            tags=["redis"],
            top_k=2,
        )
    )
    assert matches
    assert matches[0].memory.memory_id == "m-1"
    assert matches[0].score > matches[1].score
