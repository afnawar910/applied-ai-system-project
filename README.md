# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

PawPal+ includes four algorithms that make the daily planner more intelligent:

| Feature | How it works |
|---------|-------------|
| **Sort by time** | Tasks with a `start_time` (HH:MM) are sorted chronologically using a lambda key. Tasks without a time are pushed to the end. |
| **Filter tasks** | `Scheduler.filter_tasks()` accepts `pet_name`, `status` ("completed"/"incomplete"), and `category` to return a targeted subset of tasks. |
| **Recurring tasks** | `frequency="daily"` tasks advance to the next day via `timedelta(days=1)` when completed; `weekly` tasks advance by 7 days. `as-needed` tasks are never auto-scheduled. |
| **Conflict detection** | `Scheduler.detect_conflicts()` checks for overlapping time windows within the same pet using the formula `A.start < B.end AND B.start < A.end`, returning human-readable warnings instead of crashing. |

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
