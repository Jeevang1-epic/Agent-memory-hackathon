# I Built an Incident Copilot That Gets Smarter After Every Outage

I got tired of incident response feeling like organizational amnesia.

Every outage starts with the same ritual: open dashboards, dig through old tickets, scroll through stale postmortems, and hope someone remembers what worked last time. The team usually has the answer somewhere, but it is trapped in fragments across Slack, runbooks, issue trackers, and people's memory.

I wanted a system that remembers the way a strong SRE team remembers: what failed, what worked, what to do first, and what never to repeat.

That is why I built Flashback Ops, a memory-first incident response copilot that compares no-memory planning versus memory-augmented planning in real time. The core stack uses [Hindsight](https://github.com/vectorize-io/hindsight) concepts for persistent agent memory, with the implementation designed so memory is central to behavior, not just storage.

## The Real Problem I Wanted to Solve

Most AI incident assistants are stateless wrappers around playbook templates. They can suggest generic steps, but they do not know your environment history:

- Which mitigations have already failed for this service
- Which root causes recur in your architecture
- Which fixes usually resolve incidents quickly for your team
- Which classes of incidents are rising over time

Without memory, an agent can sound helpful while still being operationally expensive.

I wanted concrete behavior change:

- Baseline mode should produce a generic triage plan.
- Memory mode should prioritize historically successful actions for similar incidents.
- The delta should be measurable and visible.

## System Design: Keep Scope Tight, Make Memory Obvious

I intentionally narrowed scope to one workflow: incident triage for backend services.

The app has four major layers:

1. FastAPI service for retain/recall and plan generation
2. Memory adapter with local persistence and optional Hindsight backend mode
3. Deterministic scoring engine for ranking recalled incidents
4. Web console that shows baseline vs memory plans side by side

The architecture stays simple enough to demo in minutes, but each layer maps to a real production concern.

## How Retain and Recall Actually Work

Every incident record is normalized into one memory document:

- Service, severity, symptoms, root cause, actions, outcome, tags
- Timeline and prevention notes
- Outcome-derived success score

Those documents are persisted in local JSON by default and can also be sent to a Hindsight-compatible endpoint when backend mode is enabled via environment variables.

This is the retention shape from the service layer:

```python
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
```

For recall, I did not rely on a black-box similarity score alone. I combine multiple signals that incident responders care about:

- Lexical overlap between incident context and memory summary
- Symptom overlap
- Service and severity match bonuses
- Tag similarity
- Recency decay
- Historical outcome weighting

The ranking formula intentionally rewards memories that are both relevant and historically effective.

## Why I Added Baseline vs Memory Side-by-Side

I did not want to claim memory helps. I wanted to show it every single query.

Each assist call returns:

- No-memory baseline plan
- Memory-augmented plan
- Confidence for each
- Memory boost (`with_memory - without_memory`)
- Recalled incidents with scores and root causes

The plan generator starts with a baseline incident playbook and then rewrites priorities using recalled evidence:

```python
avg_score = sum(match.score for match in matches) / len(matches)
with_confidence = min(0.95, 0.45 + avg_score * 0.45 + len(matches) * 0.03)
memory_boost = round(with_card.confidence - without_card.confidence, 2)
```

That confidence delta is one of the most useful UI elements in the app because it turns memory from a buzzword into a measurable signal.

## Feedback Loop: The Part Most Demos Skip

I have seen too many agents with a one-way memory pipeline. They ingest data, but they never learn from outcomes.

In Flashback Ops, every incident run can be closed with structured feedback:

- Outcome (`resolved`, `partial`, `failed`)
- Useful mitigation steps
- Post-incident notes

That feedback is retained as a new memory object and becomes future retrieval signal. It means the system does not only remember incidents, it remembers whether its recommendations worked.

This piece is where [Hindsight agent memory](https://hindsight.vectorize.io/) shines conceptually: memory is not just conversation history, it is a continuously improving performance loop.

## Example Behavior Change

I seeded realistic outage data for services like `payments-api`, `auth-service`, and `search-indexer`.

When I submit a fresh payments incident with:

- card authorization timeouts
- retry spikes
- Redis pool errors

The baseline output is a generic incident response list: check health, isolate pattern, assign owners, prepare rollback.

The memory output does something very different:

- prioritizes Redis scaling and warmup-concurrency reduction first
- references previously successful payment outage mitigations
- ranks the likely root cause based on past outcomes

That is exactly the behavior shift I was aiming for. The no-memory plan is "textbook." The memory plan is "team memory at speed."

## The UI Was Designed for Judges and Operators

I built the frontend to minimize explanation overhead in a live walkthrough:

- one-click seed for realistic data
- one incident form
- two plan cards in parallel
- memory boost banner at the top
- recalled incidents table below
- feedback form at the bottom to close the loop

If someone can understand the value in 30 seconds, the demo is doing its job.

## What Was Harder Than Expected

The hardest part was not generating plans. It was preventing false confidence.

If a ranking model over-trusts weak matches, the output looks specific but can be wrong in dangerous ways. I handled this with:

- conservative confidence math
- explicit risk flags in both plans
- multi-factor scoring, not pure keyword match
- outcome-based weighting so failed fixes carry less influence

This is also where I think teams building memory agents should spend more time. Memory quality is a product problem, not just a retrieval problem.

## Why I Chose This Memory Stack

I needed an approach that is practical now and expandable later.

- Local mode gives instant portability for demos and offline usage.
- Hindsight mode enables production-grade memory orchestration when API credentials are available.

This pattern let me ship quickly while staying aligned with the long-term direction of persistent [agent memory](https://vectorize.io/what-is-agent-memory) systems.

## Lessons I Will Reuse in Future Agent Systems

1. If memory is not visible in the UX, users assume it is not working.
2. Baseline comparisons are mandatory when your value proposition is "improves over time."
3. Outcome-weighted recall is more useful than raw similarity.
4. Feedback capture should be first-class, not a post-launch task.
5. Narrow scope beats broad ambition during first implementation.

## Where This Goes Next

Flashback Ops is already useful for single-service triage, but the next upgrades are clear:

- incident family clustering across services
- change-intel correlation (deploys, config, infra events)
- role-aware recommendations for SRE, backend, and on-call management tracks
- memory hygiene controls for retention windows and auditability

The main idea remains the same: incident response should compound learning over time.

Stateless assistants reset to zero. Memory-first systems do not.
