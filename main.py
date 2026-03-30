"""
PawPal+ demo script — run this to verify scheduling logic in the terminal.
Usage: python main.py
"""

from pawpal_system import Task, Pet, Owner, Scheduler


def section(title: str) -> None:
    print("\n" + "=" * 55)
    print(f"  {title}")
    print("=" * 55)


def main():
    # --- Setup ---
    owner = Owner(name="Jordan", available_time=90)
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna  = Pet(name="Luna",  species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks added OUT OF ORDER (sort demo will reorder them)
    mochi.add_task(Task(name="Fetch in yard",   category="enrichment", duration=20, priority="medium", frequency="daily",  start_time="17:00"))
    mochi.add_task(Task(name="Flea medication", category="meds",       duration=5,  priority="high",   frequency="weekly", start_time="08:30"))
    mochi.add_task(Task(name="Breakfast",       category="feeding",    duration=10, priority="high",   frequency="daily",  start_time="07:30"))
    mochi.add_task(Task(name="Morning walk",    category="walk",       duration=30, priority="high",   frequency="daily",  start_time="09:00"))

    luna.add_task(Task(name="Laser toy play",   category="enrichment", duration=10, priority="low",    frequency="daily",  start_time="18:00"))
    luna.add_task(Task(name="Brush coat",       category="grooming",   duration=15, priority="medium", frequency="weekly", start_time="14:00"))
    luna.add_task(Task(name="Breakfast",        category="feeding",    duration=5,  priority="high",   frequency="daily",  start_time="07:30"))

    scheduler = Scheduler(owner)

    # ------------------------------------------------------------------
    # 1. SORT BY TIME — tasks listed out of order, should reorder to HH:MM
    # ------------------------------------------------------------------
    section("1. SORT BY START TIME (HH:MM)")
    all_pairs = owner.get_all_tasks()
    sorted_pairs = scheduler.sort_by_time(all_pairs)
    for pet, task in sorted_pairs:
        print(f"  {task.start_time or '??:??'}  [{pet.name}] {task.name} ({task.priority})")

    # ------------------------------------------------------------------
    # 2. FILTER — show only Mochi's incomplete tasks
    # ------------------------------------------------------------------
    section("2. FILTER — Mochi's incomplete tasks")
    mochi_tasks = scheduler.filter_tasks(pet_name="Mochi", status="incomplete")
    for pet, task in mochi_tasks:
        print(f"  [{pet.name}] {task.name} ({task.category}, {task.duration} min)")

    # ------------------------------------------------------------------
    # 3. CONFLICT DETECTION — add an overlapping task to Mochi
    # ------------------------------------------------------------------
    section("3. CONFLICT DETECTION")
    # Mochi already has "Morning walk" at 09:00 (30 min, ends 09:30)
    # Add a grooming at 09:15 — should trigger a conflict warning
    mochi.add_task(Task(name="Grooming", category="grooming", duration=20,
                        priority="low", frequency="daily", start_time="09:15"))
    conflicts = scheduler.detect_conflicts(owner.get_all_tasks())
    if conflicts:
        for w in conflicts:
            print(f"  WARNING: {w}")
    else:
        print("  No conflicts detected.")
    # Remove the conflicting task so the schedule stays clean
    mochi.remove_task(mochi.get_tasks()[-1])

    # ------------------------------------------------------------------
    # 4. RECURRING TASK — mark Mochi's Breakfast done, advance to next day
    # ------------------------------------------------------------------
    section("4. RECURRING TASK — advance after completion")
    breakfast = next(t for t in mochi.get_tasks() if t.name == "Breakfast")
    print(f"  Before: '{breakfast.name}' due {breakfast.due_date}, completed={breakfast.is_completed}")
    breakfast.mark_done()
    next_task = scheduler.advance_recurring(mochi, breakfast)
    if next_task:
        print(f"  After:  '{next_task.name}' due {next_task.due_date}, completed={next_task.is_completed}")

    # ------------------------------------------------------------------
    # 5. GENERATE SCHEDULE
    # ------------------------------------------------------------------
    section("5. TODAY'S SCHEDULE")
    print(f"  Owner: {owner.name}  |  Available: {owner.available_time} min\n")
    schedule = scheduler.generate()

    checklist = schedule.get_checklist()
    if checklist:
        print("  SCHEDULED:\n")
        for i, (pet, task) in enumerate(checklist, 1):
            time_str   = f" @ {task.start_time}" if task.start_time else ""
            urgent_str = "  *** REMINDER ***" if task.is_urgent else ""
            print(f"  {i}. [{pet.name}] {task.name}{time_str} ({task.duration} min, {task.priority}){urgent_str}")

    skipped = schedule.get_skipped()
    if skipped:
        print("\n  SKIPPED:\n")
        for pet, task, reason in skipped:
            print(f"  - [{pet.name}] {task.name}  ({reason})")

    conflicts = getattr(schedule, "_conflicts", [])
    if conflicts:
        print("\n  CONFLICTS:")
        for w in conflicts:
            print(f"  ! {w}")

    print()
    print("-" * 55)
    used  = schedule.total_time_used
    avail = owner.available_time
    if used > avail:
        print(f"  Time used: {used} min  (over by {used - avail} min -- urgent tasks kept)")
    else:
        print(f"  Time used: {used} / {avail} min  ({avail - used} min to spare)")
    print("=" * 55)


if __name__ == "__main__":
    main()
