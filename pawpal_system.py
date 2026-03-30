"""
PawPal+ — backend logic layer.
All core classes live here; app.py imports from this module.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Natural time-of-day ordering for categories (used as sort tiebreak)
CATEGORY_TIME_SLOT = {
    "feeding":    0,
    "meds":       1,
    "walk":       2,
    "grooming":   3,
    "enrichment": 4,
    "other":      5,
}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care activity."""

    name: str
    category: str        # "walk", "feeding", "meds", "grooming", "enrichment", "other"
    duration: int        # minutes per session
    priority: str        # "high", "medium", "low"
    frequency: str = "daily"       # "daily", "weekly", "as-needed"
    start_time: str = ""           # optional HH:MM string for time-based sorting/conflicts
    due_date: Optional[date] = None  # defaults to today on first use
    is_completed: bool = False
    is_urgent: bool = False        # reminder flag shown as alert in the UI
    notes: str = ""

    def __post_init__(self) -> None:
        if self.due_date is None:
            self.due_date = date.today()

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def mark_undone(self) -> None:
        """Unmark this task (e.g. user accidentally checked it off)."""
        self.is_completed = False

    def next_occurrence(self) -> "Task":
        """
        Return a new Task instance for the next scheduled occurrence.
        Uses timedelta to calculate the correct future due_date:
          - daily  → today + 1 day
          - weekly → today + 7 days
          - as-needed → unchanged (returns a copy with same due_date)
        """
        if self.frequency == "daily":
            next_due = date.today() + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = date.today() + timedelta(weeks=1)
        else:
            next_due = self.due_date   # as-needed: no automatic next date

        return Task(
            name=self.name,
            category=self.category,
            duration=self.duration,
            priority=self.priority,
            frequency=self.frequency,
            start_time=self.start_time,
            due_date=next_due,
            notes=self.notes,
        )

    def end_time(self) -> str:
        """
        Return the HH:MM end time calculated from start_time + duration.
        Returns "" if start_time is not set.
        """
        if not self.start_time:
            return ""
        h, m = map(int, self.start_time.split(":"))
        total = h * 60 + m + self.duration
        return f"{total // 60:02d}:{total % 60:02d}"


# ---------------------------------------------------------------------------
# Pet — owns its own task list
# ---------------------------------------------------------------------------

class Pet:
    """Represents a pet and the care tasks associated with it."""

    def __init__(self, name: str, species: str, age: int) -> None:
        self.name = name
        self.species = species
        self.age = age
        self._tasks: list[Task] = []

    def add_task(self, task: Task) -> Optional[str]:
        """
        Add a care task for this pet.

        Returns a conflict warning string if a task with the same name already
        exists, otherwise None. The task is added regardless so the user can
        decide whether to remove the duplicate.
        """
        warning = self._find_conflict(task)
        self._tasks.append(task)
        return warning

    def _find_conflict(self, new_task: Task) -> Optional[str]:
        """Return a warning message if a duplicate task name is detected."""
        for existing in self._tasks:
            if existing.name.strip().lower() == new_task.name.strip().lower():
                return (
                    f"'{new_task.name}' already exists for {self.name}. "
                    "Added anyway — remove the duplicate if unintended."
                )
        return None

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        self._tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        """Return this pet's full task list."""
        return list(self._tasks)

    def get_care_needs(self) -> list[str]:
        """Return species-specific default task categories."""
        defaults = {
            "dog":    ["walk", "feeding", "grooming", "enrichment"],
            "cat":    ["feeding", "grooming", "enrichment"],
            "rabbit": ["feeding", "enrichment", "grooming"],
        }
        return defaults.get(self.species.lower(), ["feeding"])

    def __repr__(self) -> str:
        return f"Pet(name={self.name!r}, species={self.species!r}, age={self.age})"


# ---------------------------------------------------------------------------
# Owner — manages multiple pets
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner, their daily availability, and their pets."""

    def __init__(self, name: str, available_time: int) -> None:
        self.name = name
        self.available_time = available_time   # total minutes available per day
        self._pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self._pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        self._pets.remove(pet)

    def get_pets(self) -> list[Pet]:
        """Return the list of pets."""
        return list(self._pets)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task across all pets as (pet, task) pairs."""
        return [(pet, task) for pet in self._pets for task in pet.get_tasks()]

    def __repr__(self) -> str:
        return f"Owner(name={self.name!r}, available_time={self.available_time})"


# ---------------------------------------------------------------------------
# Schedule — the daily output
# ---------------------------------------------------------------------------

class Schedule:
    """A daily care plan containing the chosen and ordered tasks."""

    def __init__(self, plan_date: Optional[date] = None) -> None:
        self.plan_date = plan_date or date.today()
        self._items: list[tuple[Pet, Task]] = []
        self._skipped: list[tuple[Pet, Task, str]] = []   # (pet, task, reason)

    @property
    def total_time_used(self) -> int:
        """Total minutes consumed by all scheduled tasks."""
        return sum(task.duration for _, task in self._items)

    def add_item(self, pet: Pet, task: Task) -> None:
        """Add a (pet, task) pair to the schedule."""
        self._items.append((pet, task))

    def skip_item(self, pet: Pet, task: Task, reason: str = "") -> None:
        """Record a task that was not scheduled, with a reason."""
        self._skipped.append((pet, task, reason))

    def get_checklist(self) -> list[tuple[Pet, Task]]:
        """Return scheduled tasks as an ordered checklist."""
        return list(self._items)

    def get_skipped(self) -> list[tuple[Pet, Task, str]]:
        """Return tasks that were dropped, each with a reason string."""
        return list(self._skipped)

    def get_summary(self) -> str:
        """Return a human-readable explanation of the schedule."""
        lines = [f"Daily plan for {self.plan_date} -- {self.total_time_used} min scheduled\n"]
        if self._items:
            lines.append("Scheduled:")
            for pet, task in self._items:
                time_str = f" @ {task.start_time}" if task.start_time else ""
                urgent = " *** REMINDER ***" if task.is_urgent else ""
                lines.append(
                    f"  [{pet.name}] {task.name}{time_str} ({task.duration} min, {task.priority}){urgent}"
                )
        if self._skipped:
            lines.append("\nNot scheduled:")
            for pet, task, reason in self._skipped:
                lines.append(f"  [{pet.name}] {task.name} -- {reason}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler — standalone brain
# ---------------------------------------------------------------------------

class Scheduler:
    """Retrieves, sorts, filters, and schedules tasks for an Owner."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    # -------------------------------------------------------------------------
    # Algorithm 1 — Sort by start_time (HH:MM), then priority, then category
    # -------------------------------------------------------------------------

    def sort_by_time(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """
        Sort (pet, task) pairs by start_time in HH:MM format using a lambda key.
        Tasks without a start_time are sorted to the end ("99:99").
        Within the same time slot, tasks are ordered by priority then category.
        """
        return sorted(
            pairs,
            key=lambda pt: (
                pt[1].start_time or "99:99",
                PRIORITY_ORDER.get(pt[1].priority, 99),
                CATEGORY_TIME_SLOT.get(pt[1].category, 99),
            ),
        )

    def _sort_by_priority(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Sort by priority → category time slot → duration (used when no start_times set)."""
        return sorted(
            pairs,
            key=lambda pt: (
                PRIORITY_ORDER.get(pt[1].priority, 99),
                CATEGORY_TIME_SLOT.get(pt[1].category, 99),
                pt[1].duration,
            ),
        )

    # -------------------------------------------------------------------------
    # Algorithm 2 — Filter tasks by pet, status, or category
    # -------------------------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,      # "completed" | "incomplete"
        category: Optional[str] = None,
    ) -> list[tuple[Pet, Task]]:
        """
        Return a filtered subset of all tasks.

        Args:
            pet_name: If provided, only return tasks belonging to this pet.
            status:   "completed" returns only done tasks; "incomplete" returns undone.
            category: If provided, only return tasks of this category.
        """
        results = self.owner.get_all_tasks()
        if pet_name:
            results = [(p, t) for p, t in results if p.name == pet_name]
        if status == "completed":
            results = [(p, t) for p, t in results if t.is_completed]
        elif status == "incomplete":
            results = [(p, t) for p, t in results if not t.is_completed]
        if category:
            results = [(p, t) for p, t in results if t.category == category]
        return results

    # -------------------------------------------------------------------------
    # Algorithm 3 — Recurring task: advance to next occurrence after completion
    # -------------------------------------------------------------------------

    def advance_recurring(self, pet: Pet, task: Task) -> Optional[Task]:
        """
        When a recurring task is marked complete, remove the current instance
        from the pet and add the next occurrence (calculated via timedelta).
        Returns the new Task if one was created, or None for as-needed tasks.
        """
        if task.frequency == "as-needed":
            return None
        pet.remove_task(task)
        next_task = task.next_occurrence()
        pet.add_task(next_task)
        return next_task

    # -------------------------------------------------------------------------
    # Algorithm 4 — Conflict detection (overlapping time windows)
    # -------------------------------------------------------------------------

    def detect_conflicts(self, pairs: list[tuple[Pet, Task]]) -> list[str]:
        """
        Detect scheduling conflicts where two tasks for the same pet have
        overlapping time windows.

        Strategy: for each pair of tasks that share a pet and both have a
        start_time, check if their intervals overlap using the formula:
            A.start < B.end  AND  B.start < A.end
        Returns a list of human-readable warning strings (empty if no conflicts).
        This lightweight approach checks exact time-window overlap rather than
        exact-match only, catching partial overlaps too.
        """
        warnings: list[str] = []
        timed = [(p, t) for p, t in pairs if t.start_time]

        for i, (pet_a, task_a) in enumerate(timed):
            for pet_b, task_b in timed[i + 1:]:
                if pet_a.name != pet_b.name:
                    continue   # only flag conflicts for the same pet
                a_start = task_a.start_time
                a_end   = task_a.end_time()
                b_start = task_b.start_time
                b_end   = task_b.end_time()
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"CONFLICT [{pet_a.name}]: '{task_a.name}' ({a_start}-{a_end}) "
                        f"overlaps '{task_b.name}' ({b_start}-{b_end})"
                    )
        return warnings

    # -------------------------------------------------------------------------
    # Recurring filter — only include tasks due today
    # -------------------------------------------------------------------------

    def _is_due_today(self, task: Task) -> bool:
        """
        Decide whether a task is due in today's schedule based on frequency.
          - daily:     always due
          - weekly:    due only on Mondays (weekday 0)
          - as-needed: never auto-scheduled
        """
        if task.frequency == "daily":
            return True
        if task.frequency == "weekly":
            return datetime.today().weekday() == 0
        return False

    # -------------------------------------------------------------------------
    # Conflict check helper (for UI pre-flight check)
    # -------------------------------------------------------------------------

    def check_conflict(self, pet: Pet, task_name: str) -> bool:
        """Return True if a task with this name already exists for the pet."""
        return any(t.name.strip().lower() == task_name.strip().lower() for t in pet.get_tasks())

    # -------------------------------------------------------------------------
    # Main generate
    # -------------------------------------------------------------------------

    def generate(self) -> Schedule:
        """
        Build today's Schedule:
        1. Filter to tasks due today (recurring logic).
        2. Sort: by start_time if available, otherwise by priority → category → duration.
        3. Fit tasks within the owner's available time budget.
        4. High-priority tasks that exceed the budget are kept and flagged urgent.
        5. Tasks that don't fit are skipped with a human-readable reason.
        6. Run conflict detection on the final scheduled set and attach warnings.
        """
        schedule = Schedule()
        all_tasks = self.owner.get_all_tasks()

        # Step 1 — recurring filter
        due_today     = [(p, t) for p, t in all_tasks if self._is_due_today(t)]
        not_due_today = [(p, t) for p, t in all_tasks if not self._is_due_today(t)]
        for pet, task in not_due_today:
            schedule.skip_item(pet, task, reason=f"not due today ({task.frequency})")

        # Step 2 — sort
        has_times = any(t.start_time for _, t in due_today)
        sorted_tasks = self.sort_by_time(due_today) if has_times else self._sort_by_priority(due_today)

        # Steps 3-5 — fit into time budget
        time_remaining = self.owner.available_time
        for pet, task in sorted_tasks:
            task.is_urgent = False
            if task.duration <= time_remaining:
                schedule.add_item(pet, task)
                time_remaining -= task.duration
            elif task.priority == "high":
                task.is_urgent = True
                schedule.add_item(pet, task)
                time_remaining -= task.duration
            else:
                schedule.skip_item(pet, task, reason="not enough time today")

        # Step 6 — conflict detection (stored as warnings in schedule summary)
        schedule._conflicts = self.detect_conflicts(schedule.get_checklist())

        return schedule
