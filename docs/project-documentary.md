# Flashback Ops Documentary

## Project Identity

- Project: Flashback Ops
- Team: Solo Leveling11
- Team Code: af50adfd
- Builder: Jeevan Kumar
- Category: Engineering and DevOps agent

## Executive Summary

Flashback Ops is a memory-first incident response agent that converts past outage history into ranked mitigation plans for new incidents.  
It is built to solve a practical operational pain: teams repeatedly lose context during high-pressure incidents and spend precious time rediscovering fixes they already found before.

The product proves value through a direct comparison between:

- no-memory baseline planning
- memory-augmented planning with confidence boost

Each run can be closed with structured feedback, which is retained and reused during future recall.

## Problem Statement

Engineering organizations handle recurring incidents:

- similar failure signatures reappear across services
- prior remediation context is scattered across systems
- new responders repeat the same analysis work

Stateless AI assistants amplify this problem because they cannot accumulate team memory.

## Solution Design

### 1. Retain Layer

Incident records are stored with service, severity, symptoms, root cause, actions, tags, timeline, prevention, and outcome score.

### 2. Recall Layer

Memories are ranked by:

- lexical relevance
- symptom overlap
- service and severity match
- tag similarity
- recency decay
- outcome success weighting

### 3. Plan Layer

The planner generates:

- baseline playbook without memory
- memory-adapted plan using high-score memories
- tactical takeaways
- confidence delta

### 4. Learning Layer

Post-incident feedback is stored as new memory, increasing future retrieval quality.

## Technical Stack

- FastAPI backend
- Typed Pydantic models
- Local persistent memory store
- Optional Hindsight remote backend mode
- Vanilla JavaScript frontend
- Pytest validation suite

## Notable Product Decisions

### Memory as a Visible Feature

The user sees two plans side by side. This removes ambiguity around whether memory is helping.

### Deterministic Ranking

I used transparent scoring logic instead of opaque embeddings-only behavior so the recall signal is explainable in demos and debugging.

### Dual Backend Strategy

Local mode keeps the project demo-ready for any environment. Hindsight mode supports hosted memory workflows when credentials are present.

## Validation Evidence

### Automated Tests

- API flow: seed -> assist -> feedback
- Recall scoring quality: relevant successful service memories outrank weaker matches

### Learning Curve Simulation

`python scripts/evaluate_learning_curve.py` produced:

- payments-api boost: +0.49
- auth-service boost: +0.46
- search-indexer boost: +0.48
- average memory boost: +0.477

## Demo Narrative

1. Seed realistic outage memories.
2. Trigger a new incident query.
3. Show generic baseline response.
4. Show memory-specific response.
5. Submit feedback.
6. Repeat and observe improved recall confidence.

## Real-World Adoption Path

- Integrate with incident management data sources (PagerDuty, Jira, internal runbooks)
- Add role-based response views for on-call, SRE, and engineering managers
- Add governance around memory retention, redaction, and audit trails

## Risks and Mitigation

- Risk: stale memories can overfit old architectures  
  Mitigation: recency weighting + explicit risk flags in generated plans

- Risk: false confidence from weak recall  
  Mitigation: confidence is conservative and tied to recall quality

- Risk: memory drift from low-quality feedback  
  Mitigation: structured feedback fields and outcome weighting

## Final Outcome

Flashback Ops demonstrates a production-relevant memory pattern:

- retain operational history
- recall context under pressure
- adapt recommendations using outcomes

The result is an incident agent that learns continuously instead of resetting every run.
