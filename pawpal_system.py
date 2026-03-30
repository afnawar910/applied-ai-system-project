"""
PawPal+ — backend logic layer.
All core classes live here; app.py imports from this module.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

# Natural time-of-day ordering for categories
CATEGORY_TIME_SLOT = {
    "feeding":    0,   # morning first
    "meds":       1,
    "walk":       2,
    "grooming":   3,
    "enrichment": 4,
    "other":      5,
}

@dataclass
class Task:
    """A single pet care activity."""
    name: str
    category: str        # "walk", "feeding", "meds", "grooming", "enrichment", "other"
    duration: int        # minutes per session
    priority: str        # "high", "medium", "low"
    frequency: str = "daily"    # "daily", "weekly", "as-needed"
    is_completed: bool = False
    is_urgent: bool = False     # reminder flag — shown as alert in the UI
    notes: str = ""

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def mark_undone(self) -> None:
        """Unmark this task (e.g. user accidentally checked it off)."""
        self.is_completed = False


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

    def add_task(self, task: Task) -> str | None:
        """
        Add a care task for this pet.
        Returns a conflict warning string if a task with the same name already
        exists, otherwise None (task is added regardless so the user can decide).
        """
        conflict = self._find_conflict(task)
        self._tasks.append(task)
        return conflict

    def _find_conflict(self, new_task: Task) -> str | None:
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
        self._pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        self._pets.remove(pet)

    def get_pets(self) -> list[Pet]:
        return list(self._pets)

    def get_all_tasks(self) -> list[tuple["Pet", Task]]:
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
        return sum(task.duration for _, task in self._items)

    def add_item(self, pet: Pet, task: Task) -> None:
        self._items.append((pet, task))

    def skip_item(self, pet: Pet, task: Task, reason: str = "") -> None:
        self._skipped.append((pet, task, reason))

    def get_checklist(self) -> list[tuple[Pet, Task]]:
        return list(self._items)

    def get_skipped(self) -> list[tuple[Pet, Task, str]]:
        return list(self._skipped)

    def get_summary(self) -> str:
        lines = [f"Daily plan for {self.plan_date} -- {self.total_time_used} min scheduled\n"]
        if self._items:
            lines.append("Scheduled:")
            for pet, task in self._items:
                urgent = " *** REMINDER ***" if task.is_urgent else ""
                lines.append(
                    f"  [{pet.name}] {task.name} ({task.duration} min, {task.priority}){urgent}"
                )
        if self._skipped:
            lines.append("\nNot scheduled:")
            for pet, task, reason in self._skipped:
                lines.append(f"  [{pet.name}] {task.name} -- {reason}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler — standalone brain
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    """Retrieves, sorts, filters, and schedules tasks for an Owner."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    # -- Algorithm 1: Sort by priority then natural time-of-day slot ----------

    def _sort_tasks(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """
        Sort (pet, task) pairs by:
          1. Priority (high → medium → low)
          2. Natural time-of-day slot (feeding/meds in the morning, enrichment later)
          3. Duration (shorter tasks first as final tiebreak)
        """
        return sorted(
            pairs,
            key=lambda pt: (
                PRIORITY_ORDER.get(pt[1].priority, 99),
                CATEGORY_TIME_SLOT.get(pt[1].category, 99),
                pt[1].duration,
            ),
        )

    # -- Algorithm 2: Filter tasks --------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,       # "completed" | "incomplete"
        category: Optional[str] = None,
    ) -> list[tuple[Pet, Task]]:
        """
        Return a filtered subset of all tasks.
        - pet_name: only tasks belonging to this pet
        - status:   "completed" or "incomplete"
        - category: only tasks of this category
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

    # -- Algorithm 3: Recurring task logic ------------------------------------

    def _is_due_today(self, task: Task) -> bool:
        """
        Decide whether a task should appear in today's schedule based on frequency.
        - daily:     always due
        - weekly:    due only on Mondays (day 0)
        - as-needed: never auto-scheduled (owner adds manually)
        """
        if task.frequency == "daily":
            return True
        if task.frequency == "weekly":
            return datetime.today().weekday() == 0   # Monday
        return False   # as-needed

    # -- Algorithm 4: Conflict detection (duplicate name check) ---------------
    # Handled inside Pet.add_task() — returns a warning string on conflict.
    # Scheduler exposes a helper so the UI can call it before committing.

    def check_conflict(self, pet: Pet, task_name: str) -> bool:
        """Return True if a task with this name already exists for the pet."""
        return any(t.name.strip().lower() == task_name.strip().lower() for t in pet.get_tasks())

    # -- Main generate --------------------------------------------------------

    def generate(self) -> Schedule:
        """
        Build today's Schedule:
        1. Filter to tasks that are due today (recurring logic).
        2. Sort by priority → time-of-day slot → duration.
        3. Fit tasks within available time budget.
        4. High-priority tasks that exceed budget are kept and flagged urgent.
        5. Everything else that doesn't fit is skipped with a reason.
        """
        schedule = Schedule()
        all_tasks = self.owner.get_all_tasks()

        # Step 1 — recurring filter
        due_today = [(pet, task) for pet, task in all_tasks if self._is_due_today(task)]
        skipped_not_due = [(pet, task) for pet, task in all_tasks if not self._is_due_today(task)]
        for pet, task in skipped_not_due:
            schedule.skip_item(pet, task, reason=f"not due today ({task.frequency})")

        # Step 2 — sort
        sorted_tasks = self._sort_tasks(due_today)

        # Step 3-5 — fit into time budget
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

        return schedule
