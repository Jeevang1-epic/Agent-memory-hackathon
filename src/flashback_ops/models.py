from typing import Literal
from pydantic import BaseModel, Field


Severity = Literal["low", "medium", "high", "critical"]
Outcome = Literal["resolved", "partial", "failed", "unknown"]


class IncidentCreateRequest(BaseModel):
    incident_id: str = Field(min_length=3, max_length=120)
    service: str = Field(min_length=2, max_length=120)
    severity: Severity
    symptoms: list[str] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)
    root_cause: str = Field(min_length=3, max_length=2000)
    resolution_steps: list[str] = Field(default_factory=list)
    prevention: str = ""
    tags: list[str] = Field(default_factory=list)
    outcome: Outcome = "resolved"


class IncidentCreateResponse(BaseModel):
    memory_id: str
    status: str


class AssistRequest(BaseModel):
    session_id: str = Field(default="")
    service: str = Field(min_length=2, max_length=120)
    severity: Severity
    symptoms: list[str] = Field(default_factory=list)
    objective: str = Field(min_length=3, max_length=1000)
    logs: str = ""
    tags: list[str] = Field(default_factory=list)
    top_k: int = Field(default=4, ge=1, le=10)


class PlanCard(BaseModel):
    title: str
    confidence: float
    steps: list[str]
    rationale: list[str]
    risk_flags: list[str]


class MemoryHitView(BaseModel):
    memory_id: str
    incident_id: str
    service: str
    score: float
    root_cause: str
    actions: list[str]
    outcome: Outcome
    summary: str


class AssistResponse(BaseModel):
    query_id: str
    session_id: str
    memory_boost: float
    without_memory: PlanCard
    with_memory: PlanCard
    recalled_memories: list[MemoryHitView]
    tactical_takeaways: list[str]


class FeedbackRequest(BaseModel):
    session_id: str
    query_id: str
    outcome: Outcome
    notes: str = ""
    useful_steps: list[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    status: str
    memory_id: str


class SeedResponse(BaseModel):
    inserted: int
    status: str


class StatusResponse(BaseModel):
    app: str
    backend: str
    memory_entries: int
    sessions: int
    available: bool


class SubscriptionRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    team_name: str = Field(min_length=2, max_length=120)
    team_size: int = Field(ge=1, le=500)
    plan: Literal["starter", "growth", "enterprise"] = "growth"
    use_case: str = Field(default="", max_length=800)


class SubscriptionResponse(BaseModel):
    status: str
    record_id: str


class SubscriptionStatsResponse(BaseModel):
    total: int
    starter: int
    growth: int
    enterprise: int
