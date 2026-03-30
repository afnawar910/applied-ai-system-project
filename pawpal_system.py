"""
PawPal+ — backend logic layer.
All core classes live here; app.py imports from this module.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents the pet whose care is being planned."""
    name: str
    species: str      # e.g. "dog", "cat", "rabbit"
    age: int          # years

    def get_care_needs(self) -> list[str]:
        """Return species-specific default care categories."""
        # TODO: implement species-based defaults
        return []


@dataclass
class Task:
    """A single pet care task that can appear in a daily schedule."""
    name: str
    category: str     # "walk", "feeding", "meds", "grooming", "enrichment"
    duration: int     # minutes
    priority: str     # "high", "medium", "low"
    is_completed: bool = False
    is_urgent: bool = False   # reminder flag — surfaces an alert in the UI
    notes: str = ""

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def mark_undone(self) -> None:
        """Unmark this task."""
        self.is_completed = False


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner and their daily availability."""

    def __init__(self, name: str, available_time: int, pet: Pet) -> None:
        self.name = name
        self.available_time = available_time  # minutes per day
        self.pet = pet
        self._tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the owner's task list."""
        self._tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the owner's task list."""
        self._tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        """Return a copy of the current task list."""
        return list(self._tasks)


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

class Schedule:
    """A daily care plan containing the chosen and ordered tasks."""

    def __init__(self, plan_date: Optional[date] = None) -> None:
        self.plan_date = plan_date or date.today()
        self._tasks: list[Task] = []

    @property
    def total_time_used(self) -> int:
        """Total minutes consumed by all tasks in this schedule."""
        return sum(t.duration for t in self._tasks)

    def add_task(self, task: Task) -> None:
        self._tasks.append(task)

    def remove_task(self, task: Task) -> None:
        self._tasks.remove(task)

    def get_checklist(self) -> list[Task]:
        """Return tasks as an ordered checklist with completion state."""
        return list(self._tasks)

    def get_summary(self) -> str:
        """Return a human-readable summary of the schedule."""
        # TODO: implement summary with reasoning
        return ""


# ---------------------------------------------------------------------------
# Scheduler — standalone engine
# ---------------------------------------------------------------------------

class Scheduler:
    """Generates a daily Schedule from an Owner's task list and constraints."""

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate(self) -> Schedule:
        """
        Sort tasks by priority, fit as many as possible within available time.
        High-priority tasks that exceed the time budget are still included
        and flagged as urgent (is_urgent=True).
        """
        # TODO: implement scheduling logic
        schedule = Schedule()
        return schedule
