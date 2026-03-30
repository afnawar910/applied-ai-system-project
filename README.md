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

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

The suite covers **24 tests** across the following behaviors:

| Area | What is tested |
|------|---------------|
| **Task completion** | `mark_done()` and `mark_undone()` toggle `is_completed` correctly |
| **Recurring tasks** | Daily tasks advance +1 day, weekly +7 days, as-needed unchanged; `advance_recurring()` replaces the old task on the pet |
| **Time calculation** | `end_time()` computes HH:MM end from `start_time + duration`; returns `""` when no start time |
| **Checklist** | Scheduled tasks reflect completion state in real time |
| **Pet management** | Adding/removing tasks updates pet task count; duplicate names return a warning |
| **Sorting** | `sort_by_time()` returns tasks in ascending HH:MM order |
| **Filtering** | Filter by pet name and completion status returns correct subsets |
| **Conflict detection** | Overlapping windows flagged; exact same start times flagged; non-overlapping windows clear |
| **Scheduling — happy path** | Tasks fit within time budget and appear in the checklist |
| **Scheduling — edge cases** | Owner with no pets, pet with no tasks, zero available time all produce empty/safe schedules |
| **Multi-pet** | `get_all_tasks()` aggregates across all pets correctly |
| **Time budget** | High-priority tasks always scheduled; low/medium tasks skipped when time runs out |

**Confidence level: ★★★★☆** — Core scheduling behaviors are well covered. The main gap is integration testing between the UI and the logic layer (Streamlit session state is not tested here).

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
