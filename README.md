# Flashback Ops

Flashback Ops is a memory-first incident response copilot for engineering teams.  
It turns previous outages, fixes, and postmortem lessons into ranked recovery plans for the next incident in seconds.

## Why This Project Wins

| Judging Dimension | What This Project Demonstrates |
| --- | --- |
| Innovation (30%) | Side-by-side no-memory vs memory plan generation with quantified memory boost per incident query |
| Hindsight Memory (25%) | Pluggable Hindsight backend plus local persistent memory fallback, with explicit retain/recall loop and feedback capture |
| Technical Implementation (20%) | Typed FastAPI backend, modular memory adapters, deterministic scoring engine, tests, and simulation script |
| User Experience (15%) | High-clarity web console built for live demos with confidence deltas, recalled incidents, and feedback loop |
| Real-World Impact (10%) | Solves a costly DevOps workflow: faster triage, fewer repeated mistakes, and compounding organizational learning |

## Core Demo Story

1. Seed historical incidents.
2. Submit a fresh outage signal.
3. Watch the baseline plan (generic).
4. Watch the memory plan (specific, ranked, context-aware).
5. Save feedback so the next response gets better.

## Product Highlights

- Memory is the product, not an add-on.
- Recalled incidents are scored by service, symptoms, severity, tags, recency, and prior outcomes.
- Confidence delta makes the value of memory measurable in real time.
- Feedback from resolved incidents is retained as new memory.
- Hindsight backend mode is available with fallback so the demo still runs instantly.
- SaaS access requests can be captured from the app UI.
- Operator form state is restored automatically between refreshes.
- `Ctrl+Enter` or `Cmd+Enter` runs plan generation from the incident form.

## Architecture

![Architecture](assets/architecture.svg)

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic v2
- Vanilla JS frontend
- Optional Hindsight integration through REST endpoints

## Quick Start

```bash
python -m pip install -e .[dev]
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

App URL: `http://127.0.0.1:8000`

## UI Preview

![Dashboard](images/ui/01-dashboard.png)
![Plan View](images/ui/02-plan-view.png)
![Subscription](images/ui/03-subscription.png)
![Mobile](images/ui/04-mobile.png)

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `FLASHBACK_MEMORY_BACKEND` | `local` | `local` or `hindsight` |
| `FLASHBACK_DATA_FILE` | `data/memory.json` | Local memory persistence path |
| `FLASHBACK_SUBSCRIPTIONS_FILE` | `data/subscriptions.json` | Stores SaaS waitlist requests |
| `FLASHBACK_MAX_RECALL` | `5` | Max recall candidates |
| `HINDSIGHT_BASE_URL` | empty | Hindsight API base URL |
| `HINDSIGHT_API_KEY` | empty | Hindsight auth token |
| `HINDSIGHT_BANK_ID` | `flashback-ops` | Memory bank identifier |

## API Endpoints

- `POST /api/seed` seed realistic incident memories
- `POST /api/incidents` retain one incident memory
- `POST /api/assist` generate baseline vs memory plan
- `POST /api/feedback` retain resolution feedback
- `POST /api/subscriptions` capture SaaS access requests
- `GET /api/subscriptions/stats` subscription plan distribution
- `GET /api/status` runtime snapshot
- `GET /api/memory/stats` memory distribution

## Vercel Deployment

- `vercel.json` routes all requests to `api/index.py`
- `api/index.py` loads the FastAPI app from `src/flashback_ops/app.py`
- `requirements.txt` is included for dependency install on Vercel
- Ready for serverless deploy on Vercel with Python runtime

## Quality Gates

```bash
python -m pytest -q --basetemp "C:\Users\Jeevan kumar\AppData\Local\Temp\flashback_pytest"
python scripts/evaluate_learning_curve.py
python scripts/live_demo_sequence.py
```

Reference simulation output:

- Scenario 1 memory boost: `+0.49`
- Scenario 2 memory boost: `+0.46`
- Scenario 3 memory boost: `+0.48`
- Average memory boost: `+0.477`

![Memory Boost Curve](assets/memory-boost-curve.svg)

## Submission Assets

- Technical article: [`article.md`](article.md)
- Project documentary: [`docs/project-documentary.md`](docs/project-documentary.md)
- Submission checklist: [`docs/submission-checklist.md`](docs/submission-checklist.md)
- API reference: [`docs/api-reference.md`](docs/api-reference.md)

## Team

- Team Name: `Solo Leveling11`
- Team Code: `af50adfd`
- Builder: `Jeevan Kumar`
