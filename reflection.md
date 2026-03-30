# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three core actions a user should be able to perform in PawPal+ are:

1. **Enter owner and pet information** — The user provides basic details about themselves (name, time available per day) and their pet (name, species, age). This context allows the scheduler to personalize the plan and apply relevant constraints, such as how much time the owner realistically has each day.

2. **Add and manage care tasks with a checklist** — The user can create, edit, and remove pet care tasks such as walks, feeding, medication, grooming, and enrichment activities. Each task appears as a checklist item the owner can check off as completed throughout the day. Each task includes at minimum a duration (how long it takes) and a priority level (how essential it is), which the scheduler uses to decide what to include when time is limited.

3. **Generate a daily schedule with reminders** — The user requests a daily care plan based on their available time and task list. The app produces a prioritized schedule, explains the reasoning behind its choices (for example, why a lower-priority enrichment activity was dropped to fit in a required medication task), and surfaces reminders for high-priority tasks — such as alerting the owner that medication must not be skipped.

**UML overview (Mermaid class diagram)**

Five classes: `Pet`, `Task`, `Owner`, `Schedule`, and `Scheduler`.

- **Pet** — holds the animal's name, species, and age. Has a `get_care_needs()` method that will return species-specific default task categories.
- **Task** — holds all details about one care activity: name, category, duration, priority, completion state, and an `is_urgent` flag that acts as a reminder. Methods: `mark_done()` and `mark_undone()`.
- **Owner** — holds the owner's name, daily available time (minutes), and a reference to their `Pet`. Manages the master task list via `add_task()`, `remove_task()`, and `get_tasks()`.
- **Schedule** — the daily output. Holds an ordered list of tasks and exposes `get_checklist()` for the UI checkboxes and `get_summary()` for the reasoning explanation.
- **Scheduler** — standalone engine. Takes an `Owner`, sorts their tasks by priority, and produces a `Schedule` that fits within the owner's available time.

**b. Design changes**

Two significant changes were made during implementation:

1. **Tasks moved from Owner to Pet.** The initial design stored tasks on the Owner. During implementation it became clear that tasks are logically tied to a specific animal (a walk is Mochi's walk, not Jordan's walk), so tasks were moved to Pet. Owner gained `get_all_tasks()` to aggregate across all pets when needed by the Scheduler.

2. **Task gained `start_time`, `due_date`, and `next_occurrence()`.** The original Task was purely descriptive. Supporting time-based sorting, conflict detection, and recurring logic required adding a `start_time` (HH:MM string), a `due_date`, and a `next_occurrence()` method that uses `timedelta` to calculate the next scheduled date. This kept recurring logic inside the data class rather than scattering it across the Scheduler.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints:

1. **Time budget** — the owner's daily available minutes. Tasks are sorted and fit greedily; those that exceed the budget are skipped unless high-priority.
2. **Priority** — high/medium/low. High-priority tasks are always scheduled even if they exceed the budget (flagged as urgent). Medium and low tasks are dropped when time runs out.
3. **Frequency (recurring logic)** — daily tasks appear every day; weekly tasks only on Mondays; as-needed tasks are never auto-scheduled.

Time budget was treated as the primary constraint because it is the most concrete real-world limit. Priority was secondary because it determines which tasks survive when the budget is exceeded.

**b. Tradeoffs**

The conflict detector only flags overlaps between tasks belonging to the **same pet**. Two tasks assigned to different pets that run at the same time are not flagged, even though a single owner can only do one thing at a time.

This tradeoff is reasonable for the current scenario because the typical user has one or two pets with mostly independent routines (e.g., feeding one pet while the other is resting). Adding cross-pet conflict detection would increase complexity significantly — requiring the scheduler to model the owner's attention as a shared resource — and would produce false positives for tasks that genuinely can be interleaved (like leaving food out for both pets at the same time). A future iteration could add an optional "owner is sole caretaker" mode that enables cross-pet checks.

---

## 3. AI Collaboration

**a. How you used AI**

AI (Claude / Copilot) was used across every phase:

- **Design brainstorming** — asked for a Mermaid class diagram based on the four brainstormed objects; used the output as a starting point and manually adjusted relationships (e.g. moving tasks from Owner to Pet).
- **Code generation** — generated class skeletons and method stubs, then filled in logic incrementally rather than accepting one large block.
- **Test generation** — asked for edge cases ("pet with no tasks," "zero available time") that would have been easy to overlook, then reviewed each test before saving.
- **Refactoring suggestions** — asked whether `detect_conflicts` could be simplified; evaluated the suggestion against readability before deciding.

The most effective prompts were specific and scoped: *"Based on this skeleton, implement only the `generate()` method"* worked better than broad requests.

**b. Judgment and verification**

When AI suggested making `Scheduler` a method on `Owner` (so the owner could schedule itself),I rejected the suggestion
 Having a standalone `Scheduler` class keeps responsibilities separate — the Owner models data, the Scheduler models the algorithm. Mixing them would have made unit testing harder (you would need a full Owner object just to test one sorting function). The suggestion was evaluated by asking: *"Can I test this in isolation without constructing an Owner?"* 
---

## 4. Testing and Verification

**a. What you tested**

24 automated tests cover: task completion state, recurring next-occurrence dates, end-time calculation, pet task management, duplicate name detection, sort-by-time ordering, filter combinations, conflict detection (overlap and exact same time), empty owner/pet edge cases, zero-time-budget behavior, multi-pet aggregation, and the `advance_recurring` replacement flow. These were important because they verify both the happy paths (normal scheduling) and the edge cases (zero budget, no tasks, exact-time conflicts) that are most likely to cause silent bugs in production.

**b. Confidence**

★★★★☆ — Core scheduling logic is well covered. The main untested area is the Streamlit UI layer: session state persistence across reruns and the interaction between checkbox state and `task.is_completed` are not covered by the automated suite. The next edge cases to test would be: a pet with 50+ tasks (performance), tasks whose combined duration exactly equals `available_time` (boundary condition), and an owner updating `available_time` mid-session.

---

## 5. Reflection

**a. What went well**

The separation between the logic layer (`pawpal_system.py`) and the UI layer (`app.py`) worked well. Because all scheduling logic lives in plain Python classes with no Streamlit dependency, it was easy to write and run unit tests without launching the app. The UML-first approach also meant that class responsibilities were clear before any code was written, which reduced rework.

**b. What you would improve**

The recurring task system is simple (daily = every day, weekly = every Monday). A real pet care app would need per-task day-of-week configuration (e.g., walks on Mon/Wed/Fri), time-window preferences (morning vs. evening), and the ability to mark a task as "skipped today but still due" rather than completed. The data model would need a `TaskSchedule` object to represent this without overloading the `Task` class.

**c. Key takeaway**

AI tools are most useful when you remain the architect. Asking AI to generate an entire system produces code that works but often reflects generic patterns rather than your specific design decisions. 
