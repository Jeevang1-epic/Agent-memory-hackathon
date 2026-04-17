from importlib import import_module, reload
from pathlib import Path

from fastapi.testclient import TestClient


def _build_client(tmp_path: Path, monkeypatch):
    data_file = tmp_path / "memory.json"
    monkeypatch.setenv("FLASHBACK_DATA_FILE", str(data_file))
    monkeypatch.setenv("FLASHBACK_MEMORY_BACKEND", "local")
    module = import_module("flashback_ops.app")
    module = reload(module)
    return TestClient(module.app)


def test_seed_assist_feedback_flow(tmp_path: Path, monkeypatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    seed = client.post("/api/seed")
    assert seed.status_code == 200
    assert seed.json()["inserted"] >= 6

    assist = client.post(
        "/api/assist",
        json={
            "service": "payments-api",
            "severity": "high",
            "objective": "reduce checkout failure to below 3%",
            "symptoms": ["gateway timeout in card authorization", "redis pool saturation alerts"],
            "logs": "TimeoutError: redis connection pool exhausted",
            "tags": ["redis", "checkout"],
            "top_k": 4,
        },
    )
    assert assist.status_code == 200
    payload = assist.json()
    assert payload["with_memory"]["confidence"] >= payload["without_memory"]["confidence"]
    assert payload["recalled_memories"]

    feedback = client.post(
        "/api/feedback",
        json={
            "session_id": payload["session_id"],
            "query_id": payload["query_id"],
            "outcome": "resolved",
            "notes": "redis scale-out fixed saturation",
            "useful_steps": ["Scale Redis read replicas", "Reduce warmup concurrency"],
        },
    )
    assert feedback.status_code == 200
    assert feedback.json()["status"] == "stored"

    status = client.get("/api/status")
    assert status.status_code == 200
    assert status.json()["memory_entries"] >= 7

    subscription = client.post(
        "/api/subscriptions",
        json={
            "email": "oncall@example.com",
            "team_name": "Platform Reliability",
            "team_size": 12,
            "plan": "growth",
            "use_case": "incident response memory intelligence",
        },
    )
    assert subscription.status_code == 200
    assert subscription.json()["status"] == "queued"
