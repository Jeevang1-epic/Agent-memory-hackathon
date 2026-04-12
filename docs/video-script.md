## 3-Minute Demo Script

Name: Jeevan Kumar

### 0:00 - 0:30 Quick Intro

On screen:
- Open `README.md`
- Show project title and one-line purpose

Narration:
I built Flashback Ops, an incident response copilot that learns from every outage.  
Most assistants give generic playbooks. This one compares no-memory output against memory-augmented output in the same response, so you can see exactly what memory is adding.

### 0:30 - 1:00 Show the Problem Without Memory

On screen:
- Run `python -m flashback_ops`
- Open `http://127.0.0.1:8000`
- Fill incident form for `payments-api` and click `Run Memory-Assisted Plan`
- Point at the `Without Memory` card first

Narration:
The baseline card is what a stateless assistant gives you: validate health, inspect logs, assign owners, prep rollback. Useful, but generic.

### 1:00 - 2:30 Live Memory Demo

On screen:
- Click `Load Demo Memory`
- Re-run the same incident query
- Highlight `Memory Boost`
- Highlight `With Memory` card and `Recalled Memories` table
- Open `src/flashback_ops/memory/local_store.py`
- Open `src/flashback_ops/service.py`

Narration:
Now memory is active.  
The plan prioritizes actions that resolved similar incidents before, like Redis scaling and warmup throttling for this service pattern.  
Below, you can see recalled incidents with scores, root causes, and outcomes.  
Scoring is not just keyword matching. It combines service match, symptom overlap, severity, recency, tags, and historical outcome success.  
When I close this run with feedback, that result is retained as new memory and immediately improves future recall.

### 2:30 - 3:00 Wrap Up

On screen:
- Submit feedback in the UI
- Show `scripts/evaluate_learning_curve.py`
- Run `python scripts/evaluate_learning_curve.py`

Narration:
The key takeaway is that memory must be measurable.  
This project quantifies memory impact through confidence delta and shows a repeatable improvement curve across scenarios.  
Instead of resetting every incident, the system compounds what the team learns.

## 5 Video Title Options

1. I Built an Incident Copilot That Remembers Every Outage
2. Stateless Incident AI vs Memory-First Incident AI
3. This Agent Learned From Past Outages and Cut Triage Guesswork
4. How I Turned Incident Postmortems Into Real-Time Agent Memory
5. My Incident Response Agent Gets Better After Every Failure
