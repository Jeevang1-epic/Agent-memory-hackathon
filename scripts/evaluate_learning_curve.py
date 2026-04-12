from pathlib import Path
import json
import tempfile

from flashback_ops.memory.local_store import LocalMemoryStore
from flashback_ops.models import AssistRequest
from flashback_ops.service import IncidentService


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = LocalMemoryStore(Path(tmp) / "memory.json")
        service = IncidentService(store)
        service.seed()
        scenarios = [
            AssistRequest(
                service="payments-api",
                severity="critical",
                objective="restore card authorization success",
                symptoms=["gateway timeout in card authorization", "redis pool saturation alerts"],
                logs="TimeoutError redis pool exhausted",
                tags=["redis", "checkout"],
                top_k=4,
            ),
            AssistRequest(
                service="auth-service",
                severity="critical",
                objective="recover login conversion",
                symptoms=["token verification failing", "invalid signature spike"],
                logs="JWKS signature mismatch",
                tags=["jwt", "identity-provider"],
                top_k=4,
            ),
            AssistRequest(
                service="search-indexer",
                severity="high",
                objective="reduce index lag under 5 minutes",
                symptoms=["index lag exceeded 45 minutes", "consumer rebalance loop"],
                logs="Kafka heartbeat timeout",
                tags=["kafka", "indexing"],
                top_k=4,
            ),
        ]
        rows = []
        for scenario in scenarios:
            result = service.assist(scenario)
            rows.append(
                {
                    "service": scenario.service,
                    "baseline_confidence": result.without_memory.confidence,
                    "memory_confidence": result.with_memory.confidence,
                    "memory_boost": result.memory_boost,
                    "top_memory": result.recalled_memories[0].incident_id if result.recalled_memories else "",
                }
            )
        aggregate_boost = round(sum(row["memory_boost"] for row in rows) / len(rows), 3)
        report = {"scenarios": rows, "average_memory_boost": aggregate_boost}
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
