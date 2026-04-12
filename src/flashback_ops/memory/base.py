from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass
class MemoryDocument:
    memory_id: str
    kind: str
    incident_id: str
    service: str
    severity: str
    symptoms: list[str]
    root_cause: str
    actions: list[str]
    outcome: str
    summary: str
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    success_score: float = 0.5
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryQuery:
    service: str
    severity: str
    symptoms: list[str]
    objective: str
    logs: str
    tags: list[str]
    top_k: int

    @property
    def text(self) -> str:
        parts = [self.service, self.severity, self.objective, self.logs, " ".join(self.symptoms)]
        return " ".join(x.strip() for x in parts if x and x.strip())


@dataclass
class MemoryMatch:
    memory: MemoryDocument
    score: float
    rationale: str


class MemoryStore(Protocol):
    def retain(self, document: MemoryDocument) -> str:
        ...

    def recall(self, query: MemoryQuery) -> list[MemoryMatch]:
        ...

    def stats(self) -> dict[str, Any]:
        ...
