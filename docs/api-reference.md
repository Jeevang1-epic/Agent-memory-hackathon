# API Reference

## `GET /health`

Health probe.

Response:

```json
{"ok": true}
```

## `GET /api/status`

Runtime status.

Response fields:

- `app`
- `backend`
- `memory_entries`
- `sessions`
- `available`

## `POST /api/seed`

Seeds six realistic incident memories.

Response:

```json
{
  "inserted": 6,
  "status": "seeded"
}
```

## `POST /api/incidents`

Retains one incident memory.

Request body:

```json
{
  "incident_id": "INC-2026-0100",
  "service": "payments-api",
  "severity": "critical",
  "symptoms": ["gateway timeouts", "retry spike"],
  "timeline": ["10:00 alert", "10:05 mitigation started"],
  "root_cause": "redis pool exhaustion",
  "resolution_steps": ["scale redis", "reduce warmup concurrency"],
  "prevention": "set saturation alert",
  "tags": ["redis", "checkout"],
  "outcome": "resolved"
}
```

## `POST /api/assist`

Generates no-memory and memory-augmented plans.

Request body:

```json
{
  "service": "payments-api",
  "severity": "critical",
  "objective": "restore checkout success above 97%",
  "symptoms": ["card authorization timeout", "redis saturation"],
  "logs": "TimeoutError redis pool exhausted",
  "tags": ["redis", "checkout"],
  "top_k": 4
}
```

Response highlights:

- `query_id`
- `memory_boost`
- `without_memory`
- `with_memory`
- `recalled_memories`
- `tactical_takeaways`

## `POST /api/feedback`

Retains run outcome as new memory signal.

Request body:

```json
{
  "session_id": "session-1234abcd",
  "query_id": "query-1234567890",
  "outcome": "resolved",
  "notes": "redis scaling resolved issue",
  "useful_steps": ["Scale Redis read replicas", "Reduce warmup concurrency"]
}
```

Response:

```json
{
  "status": "stored",
  "memory_id": "feedback::..."
}
```

## `POST /api/subscriptions`

Queues a team for hosted SaaS access.

Request body:

```json
{
  "email": "oncall@company.com",
  "team_name": "Platform Reliability",
  "team_size": 12,
  "plan": "growth",
  "use_case": "incident response for payment and auth services"
}
```

Response:

```json
{
  "status": "queued",
  "record_id": "sub-1234567890"
}
```

If the same email and team already exists:

```json
{
  "status": "already_registered",
  "record_id": "sub-1234567890"
}
```

## `GET /api/subscriptions/stats`

Returns subscription totals by plan.

Response:

```json
{
  "total": 4,
  "starter": 1,
  "growth": 2,
  "enterprise": 1
}
```
