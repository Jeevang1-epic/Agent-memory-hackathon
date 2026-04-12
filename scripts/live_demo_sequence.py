import json

from fastapi.testclient import TestClient

from flashback_ops.app import app


def run() -> None:
    client = TestClient(app)
    client.post("/api/seed")
    scenarios = [
        {
            "service": "payments-api",
            "severity": "critical",
            "objective": "recover checkout success in 30 minutes",
            "symptoms": ["card auth timeout", "retry queue growth", "redis pool saturation"],
            "logs": "TimeoutError redis connection pool exhausted",
            "tags": ["redis", "checkout", "timeouts"],
            "top_k": 4,
        },
        {
            "service": "auth-service",
            "severity": "critical",
            "objective": "restore login conversion above 95%",
            "symptoms": ["jwt verification failures", "invalid signature spikes"],
            "logs": "signature mismatch for key id",
            "tags": ["jwt", "identity-provider"],
            "top_k": 4,
        },
    ]
    transcript = []
    for scenario in scenarios:
        response = client.post("/api/assist", json=scenario)
        payload = response.json()
        transcript.append(
            {
                "service": scenario["service"],
                "memory_boost": payload["memory_boost"],
                "top_memory": payload["recalled_memories"][0]["incident_id"] if payload["recalled_memories"] else "",
                "first_memory_step": payload["with_memory"]["steps"][0] if payload["with_memory"]["steps"] else "",
            }
        )
    print(json.dumps(transcript, indent=2))


if __name__ == "__main__":
    run()
