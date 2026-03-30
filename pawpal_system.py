"""
PawPal+ — backend logic layer.
All core classes live here; app.py imports from this module.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care activity."""
    name: str
    category: str        # "walk", "feeding", "meds", "grooming", "enrichment"
    duration: int        # minutes per session
    priority: str        # "high", "medium", "low"
    frequency: str = "daily"   # "daily", "weekly", "as-needed"
    is_completed: bool = False
    is_urgent: bool = False    # reminder flag — shown as alert in the UI
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
        self.species = species   # e.g. "dog", "cat", "rabbit"
        self.age = age           # years
        self._tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        self._tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        self._tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        """Return this pet's task list."""
        return list(self._tasks)

    def get_care_needs(self) -> list[str]:
        """Return species-specific default task categories."""
        defaults = {
            "dog": ["walk", "feeding", "grooming", "enrichment"],
            "cat": ["feeding", "grooming", "enrichment"],
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
        self._items: list[tuple[Pet, Task]] = []   # (pet, task) pairs
        self._skipped: list[tuple[Pet, Task]] = []  # tasks that didn't fit

    @property
    def total_time_used(self) -> int:
        """Total minutes consumed by all scheduled tasks."""
        return sum(task.duration for _, task in self._items)

    def add_item(self, pet: Pet, task: Task) -> None:
        self._items.append((pet, task))

    def skip_item(self, pet: Pet, task: Task) -> None:
        self._skipped.append((pet, task))

    def get_checklist(self) -> list[tuple[Pet, Task]]:
        """Return scheduled tasks as an ordered checklist."""
        return list(self._items)

    def get_skipped(self) -> list[tuple[Pet, Task]]:
        """Return tasks that were dropped due to time constraints."""
        return list(self._skipped)

    def get_summary(self) -> str:
        """Return a human-readable explanation of the schedule."""
        lines = [f"Daily plan for {self.plan_date} — {self.total_time_used} min scheduled\n"]

        if self._items:
            lines.append("Scheduled:")
            for pet, task in self._items:
                urgent = " *** REMINDER ***" if task.is_urgent else ""
                lines.append(
                    f"  [{pet.name}] {task.name} ({task.duration} min, {task.priority} priority){urgent}"
                )

        if self._skipped:
            lines.append("\nNot scheduled (time ran out):")
            for pet, task in self._skipped:
                lines.append(f"  [{pet.name}] {task.name} ({task.duration} min, {task.priority} priority)")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler — standalone brain
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Retrieves all tasks from an Owner's pets, sorts them by priority,
    and fits as many as possible within the owner's available time.
    """

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate(self) -> Schedule:
        """
        Build a Schedule for today:
        1. Collect all (pet, task) pairs from every pet the owner has.
        2. Sort by priority (high first), then by duration (shorter first as tiebreak).
        3. Fit tasks into available time budget.
        4. High-priority tasks that still don't fit are included anyway and flagged urgent.
        5. Everything else that doesn't fit is recorded as skipped with a reason.
        """
        schedule = Schedule()
        all_tasks = self.owner.get_all_tasks()

        # Sort: priority first, then shorter tasks first as a tiebreak
        sorted_tasks = sorted(
            all_tasks,
            key=lambda pt: (self.PRIORITY_ORDER.get(pt[1].priority, 99), pt[1].duration),
        )

        time_remaining = self.owner.available_time

        for pet, task in sorted_tasks:
            task.is_urgent = False  # reset before deciding

            if task.duration <= time_remaining:
                schedule.add_item(pet, task)
                time_remaining -= task.duration
            elif task.priority == "high":
                # Must-do task: include it and flag as urgent reminder
                task.is_urgent = True
                schedule.add_item(pet, task)
                # Note: we allow going over budget for high-priority tasks
                time_remaining -= task.duration
            else:
                schedule.skip_item(pet, task)

        return schedule
