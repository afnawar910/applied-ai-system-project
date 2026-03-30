"""
PawPal+ tests — run with: python -m pytest
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Task — completion
# ---------------------------------------------------------------------------

def test_mark_done_sets_is_completed():
    """Calling mark_done() should flip is_completed to True."""
    task = Task(name="Morning walk", category="walk", duration=30, priority="high")
    assert task.is_completed is False
    task.mark_done()
    assert task.is_completed is True


def test_mark_undone_resets_is_completed():
    """Calling mark_undone() after mark_done() should reset is_completed to False."""
    task = Task(name="Breakfast", category="feeding", duration=10, priority="high")
    task.mark_done()
    task.mark_undone()
    assert task.is_completed is False


# ---------------------------------------------------------------------------
# Task — recurring next_occurrence
# ---------------------------------------------------------------------------

def test_next_occurrence_daily_advances_one_day():
    """A daily task's next occurrence should be due tomorrow."""
    task = Task(name="Walk", category="walk", duration=20, priority="high", frequency="daily")
    next_task = task.next_occurrence()
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.is_completed is False


def test_next_occurrence_weekly_advances_seven_days():
    """A weekly task's next occurrence should be due in 7 days."""
    task = Task(name="Grooming", category="grooming", duration=15, priority="medium", frequency="weekly")
    next_task = task.next_occurrence()
    assert next_task.due_date == date.today() + timedelta(weeks=1)


def test_next_occurrence_as_needed_unchanged():
    """An as-needed task should not advance its due_date."""
    today = date.today()
    task = Task(name="Vet visit", category="meds", duration=60, priority="high",
                frequency="as-needed", due_date=today)
    next_task = task.next_occurrence()
    assert next_task.due_date == today


# ---------------------------------------------------------------------------
# Task — end_time
# ---------------------------------------------------------------------------

def test_end_time_calculated_correctly():
    """end_time should equal start_time + duration in HH:MM format."""
    task = Task(name="Walk", category="walk", duration=30, priority="high", start_time="09:00")
    assert task.end_time() == "09:30"


def test_end_time_empty_when_no_start_time():
    """end_time should return '' when start_time is not set."""
    task = Task(name="Walk", category="walk", duration=30, priority="high")
    assert task.end_time() == ""


# ---------------------------------------------------------------------------
# Pet — task management + conflict detection
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


def test_duplicate_task_name_returns_warning():
    """Adding a task with a duplicate name should return a warning string."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task(name="Breakfast", category="feeding", duration=10, priority="high"))
    warning = pet.add_task(Task(name="Breakfast", category="feeding", duration=10, priority="high"))
    assert warning is not None
    assert "already exists" in warning


# ---------------------------------------------------------------------------
# Scheduler — sorting
# ---------------------------------------------------------------------------

def test_sort_by_time_orders_by_start_time():
    """sort_by_time should return tasks in ascending HH:MM order."""
    owner = Owner(name="Jordan", available_time=120)
    pet   = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task(name="Evening walk",  category="walk",    duration=20, priority="medium", start_time="17:00"))
    pet.add_task(Task(name="Breakfast",     category="feeding", duration=10, priority="high",   start_time="07:30"))
    pet.add_task(Task(name="Morning meds",  category="meds",    duration=5,  priority="high",   start_time="08:00"))

    scheduler = Scheduler(owner)
    sorted_pairs = scheduler.sort_by_time(owner.get_all_tasks())
    times = [t.start_time for _, t in sorted_pairs]
    assert times == sorted(times)


# ---------------------------------------------------------------------------
# Scheduler — filtering
# ---------------------------------------------------------------------------

def test_filter_by_pet_name():
    """filter_tasks with pet_name should return only that pet's tasks."""
    owner = Owner(name="Jordan", available_time=120)
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna  = Pet(name="Luna",  species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task(name="Walk",      category="walk",    duration=20, priority="high"))
    luna.add_task(Task(name="Cat dinner", category="feeding", duration=5,  priority="high"))

    results = Scheduler(owner).filter_tasks(pet_name="Mochi")
    assert all(p.name == "Mochi" for p, _ in results)
    assert len(results) == 1


def test_filter_by_status_incomplete():
    """filter_tasks with status='incomplete' should exclude completed tasks."""
    owner = Owner(name="Jordan", available_time=120)
    pet   = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    done_task = Task(name="Walk",      category="walk",    duration=20, priority="high")
    todo_task = Task(name="Breakfast", category="feeding", duration=10, priority="high")
    done_task.mark_done()
    pet.add_task(done_task)
    pet.add_task(todo_task)

    results = Scheduler(owner).filter_tasks(status="incomplete")
    assert all(not t.is_completed for _, t in results)
    assert len(results) == 1


# ---------------------------------------------------------------------------
# Scheduler — conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_finds_overlap():
    """detect_conflicts should flag tasks with overlapping time windows."""
    owner = Owner(name="Jordan", available_time=120)
    pet   = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    # Walk 09:00-09:30, Grooming 09:15-09:35 — overlap
    pet.add_task(Task(name="Walk",     category="walk",     duration=30, priority="high",   start_time="09:00"))
    pet.add_task(Task(name="Grooming", category="grooming", duration=20, priority="medium", start_time="09:15"))

    warnings = Scheduler(owner).detect_conflicts(owner.get_all_tasks())
    assert len(warnings) == 1
    assert "CONFLICT" in warnings[0]


def test_detect_conflicts_no_overlap():
    """detect_conflicts should return empty list when tasks do not overlap."""
    owner = Owner(name="Jordan", available_time=120)
    pet   = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    # Walk 09:00-09:30, Grooming 10:00-10:20 — no overlap
    pet.add_task(Task(name="Walk",     category="walk",     duration=30, priority="high",   start_time="09:00"))
    pet.add_task(Task(name="Grooming", category="grooming", duration=20, priority="medium", start_time="10:00"))

    warnings = Scheduler(owner).detect_conflicts(owner.get_all_tasks())
    assert warnings == []


# ---------------------------------------------------------------------------
# Scheduler — time budget
# ---------------------------------------------------------------------------

def test_scheduler_respects_available_time():
    """Non-high-priority tasks should be skipped when time runs out."""
    owner = Owner(name="Jordan", available_time=30)
    pet   = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk",     category="walk",     duration=20, priority="medium"))
    pet.add_task(Task(name="Grooming", category="grooming", duration=20, priority="low"))

    schedule = Scheduler(owner).generate()
    assert len(schedule.get_skipped()) == 1


def test_high_priority_task_always_scheduled():
    """High-priority tasks should appear in the schedule even if over budget."""
    owner = Owner(name="Jordan", available_time=10)
    pet   = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task(name="Meds", category="meds", duration=30, priority="high"))

    schedule = Scheduler(owner).generate()
    scheduled_names = [t.name for _, t in schedule.get_checklist()]
    assert "Meds" in scheduled_names
