from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .memory.base import MemoryMatch
from .models import AssistRequest


@dataclass
class PlanBundle:
    without_memory_confidence: float
    with_memory_confidence: float
    without_memory_steps: list[str]
    with_memory_steps: list[str]
    with_memory_rationale: list[str]
    without_memory_rationale: list[str]
    with_memory_risk_flags: list[str]
    without_memory_risk_flags: list[str]
    tactical_takeaways: list[str]


def _baseline_steps(request: AssistRequest) -> list[str]:
    steps = [
        f"Validate {request.service} health, recent deploys, and error-rate trend in the last 30 minutes.",
        "Open logs and isolate one reproducible failure pattern before touching infrastructure.",
        "Declare severity and assign one owner for diagnosis, one owner for mitigation, and one owner for comms.",
    ]
    if request.severity in {"high", "critical"}:
        steps.append("Start rollback readiness in parallel while root-cause investigation is running.")
    steps.append("Capture timeline events for postmortem while incident response is in progress.")
    return steps


def _derive_from_memory(matches: list[MemoryMatch]) -> tuple[list[str], list[str], list[str], list[str]]:
    action_counter: Counter[str] = Counter()
    root_counter: Counter[str] = Counter()
    service_counter: Counter[str] = Counter()
    tags_counter: Counter[str] = Counter()
    for match in matches:
        for action in match.memory.actions:
            action_counter[action.strip()] += 1
        if match.memory.root_cause.strip():
            root_counter[match.memory.root_cause.strip()] += 1
        if match.memory.service.strip():
            service_counter[match.memory.service.strip()] += 1
        for tag in match.memory.tags:
            tags_counter[tag.strip().lower()] += 1
    top_actions = [item for item, _ in action_counter.most_common(4)]
    top_causes = [item for item, _ in root_counter.most_common(3)]
    top_services = [item for item, _ in service_counter.most_common(2)]
    top_tags = [item for item, _ in tags_counter.most_common(3)]
    return top_actions, top_causes, top_services, top_tags


def build_plan_bundle(request: AssistRequest, matches: list[MemoryMatch]) -> PlanBundle:
    without_steps = _baseline_steps(request)
    without_confidence = 0.34
    without_rationale = [
        "No historical memory context applied.",
        "Plan is based on standard incident-response playbook only.",
    ]
    without_flags = [
        "Potentially repeats failed mitigations from prior incidents.",
        "No recall of prior root-cause patterns.",
    ]
    if not matches:
        return PlanBundle(
            without_memory_confidence=without_confidence,
            with_memory_confidence=without_confidence,
            without_memory_steps=without_steps,
            with_memory_steps=without_steps,
            with_memory_rationale=without_rationale,
            without_memory_rationale=without_rationale,
            with_memory_risk_flags=without_flags,
            without_memory_risk_flags=without_flags,
            tactical_takeaways=["Seed incident memories to unlock adaptive response plans."],
        )

    actions, causes, services, tags = _derive_from_memory(matches)
    with_steps = []
    if causes:
        with_steps.append(f"Start with the highest-likelihood root cause: {causes[0]}.")
    with_steps.extend(actions[:3])
    with_steps.append("Run mitigation in small batches and verify error-rate delta before full rollout.")
    if len(actions) < 3:
        with_steps.extend(without_steps[: max(0, 4 - len(with_steps))])
    unique_steps = []
    seen = set()
    for step in with_steps:
        key = step.strip().lower()
        if key and key not in seen:
            unique_steps.append(step)
            seen.add(key)
    with_steps = unique_steps[:6]
    avg_score = sum(match.score for match in matches) / len(matches)
    with_confidence = min(0.95, 0.45 + avg_score * 0.45 + len(matches) * 0.03)
    with_rationale = []
    if services:
        with_rationale.append(f"Matched incidents from {', '.join(services)}.")
    if causes:
        with_rationale.append(f"Recurring causes observed: {', '.join(causes)}.")
    if tags:
        with_rationale.append(f"High-signal tags in memory: {', '.join(tags)}.")
    with_rationale.append(f"Average recall relevance score: {avg_score:.2f}.")
    with_flags = [
        "Validate current blast radius before reusing old mitigations.",
        "Confirm dependency versions because fix effectiveness can drift over time.",
    ]
    tactical_takeaways = []
    if actions:
        tactical_takeaways.append(f"Highest-yield mitigation from memory: {actions[0]}")
    if causes:
        tactical_takeaways.append(f"Most frequent historical root cause: {causes[0]}")
    tactical_takeaways.append("Close each incident with feedback to improve future recall rankings.")
    return PlanBundle(
        without_memory_confidence=without_confidence,
        with_memory_confidence=with_confidence,
        without_memory_steps=without_steps,
        with_memory_steps=with_steps,
        with_memory_rationale=with_rationale,
        without_memory_rationale=without_rationale,
        with_memory_risk_flags=with_flags,
        without_memory_risk_flags=without_flags,
        tactical_takeaways=tactical_takeaways,
    )
