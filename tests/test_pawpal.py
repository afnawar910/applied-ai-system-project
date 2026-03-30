"""
PawPal+ tests — run with: python -m pytest
"""

import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_done_sets_is_completed():
    """Calling mark_done() should flip is_completed to True."""
    task = Task(name="Morning walk", category="walk", duration=30, priority="high")
    assert task.is_completed is False
    task.mark_done()
    assert task.is_completed is True


def test_mark_undone_resets_is_completed():
    """Calling mark_undone() after mark_done() should set is_completed back to False."""
    task = Task(name="Breakfast", category="feeding", duration=10, priority="high")
    task.mark_done()
    task.mark_undone()
    assert task.is_completed is False


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task count by 1."""
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(name="Walk", category="walk", duration=20, priority="medium"))
    assert len(pet.get_tasks()) == 1


def test_remove_task_decreases_pet_task_count():
    """Removing a task from a Pet should decrease its task count by 1."""
    pet = Pet(name="Luna", species="cat", age=5)
    task = Task(name="Brush coat", category="grooming", duration=15, priority="low")
    pet.add_task(task)
    pet.remove_task(task)
    assert len(pet.get_tasks()) == 0


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_scheduler_respects_available_time():
    """Scheduler should not exceed available time for non-high-priority tasks."""
    owner = Owner(name="Jordan", available_time=30)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk",        category="walk",    duration=20, priority="medium"))
    pet.add_task(Task(name="Grooming",    category="grooming",duration=20, priority="low"))

    schedule = Scheduler(owner).generate()
    # Only one 20-min task should fit; second is low priority so gets skipped
    assert len(schedule.get_skipped()) == 1


def test_high_priority_task_always_scheduled():
    """High-priority tasks should always appear in the schedule even if over budget."""
    owner = Owner(name="Jordan", available_time=10)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task(name="Meds", category="meds", duration=30, priority="high"))

    schedule = Scheduler(owner).generate()
    scheduled_names = [t.name for _, t in schedule.get_checklist()]
    assert "Meds" in scheduled_names
