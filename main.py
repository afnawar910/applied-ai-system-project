"""
PawPal+ demo script — run this to verify scheduling logic in the terminal.
Usage: python main.py
"""

from pawpal_system import Task, Pet, Owner, Scheduler


def main():
    # --- Setup owner ---
    owner = Owner(name="Jordan", available_time=90)

    # --- Create pets ---
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # --- Add tasks to Mochi (dog) ---
    mochi.add_task(Task(name="Morning walk",    category="walk",       duration=30, priority="high",   frequency="daily"))
    mochi.add_task(Task(name="Breakfast",       category="feeding",    duration=10, priority="high",   frequency="daily"))
    mochi.add_task(Task(name="Flea medication", category="meds",       duration=5,  priority="high",   frequency="weekly"))
    mochi.add_task(Task(name="Fetch in yard",   category="enrichment", duration=20, priority="medium", frequency="daily"))

    # --- Add tasks to Luna (cat) ---
    luna.add_task(Task(name="Breakfast",        category="feeding",    duration=5,  priority="high",   frequency="daily"))
    luna.add_task(Task(name="Brush coat",       category="grooming",   duration=15, priority="medium", frequency="weekly"))
    luna.add_task(Task(name="Laser toy play",   category="enrichment", duration=10, priority="low",    frequency="daily"))

    # --- Generate schedule ---
    scheduler = Scheduler(owner)
    schedule = scheduler.generate()

    # --- Print results ---
    print("=" * 55)
    print(f"  PawPal+ -- Daily Schedule for {owner.name}")
    print(f"  Available time: {owner.available_time} min")
    print("=" * 55)

    checklist = schedule.get_checklist()
    if checklist:
        print("\nSCHEDULED TASKS\n")
        for i, (pet, task) in enumerate(checklist, 1):
            urgent_flag = "  *** REMINDER ***" if task.is_urgent else ""
            print(f"  {i}. [{pet.name}] {task.name}")
            print(f"       Category : {task.category}")
            print(f"       Duration : {task.duration} min")
            print(f"       Priority : {task.priority}{urgent_flag}")
            print()
    else:
        print("\n  No tasks scheduled.\n")

    skipped = schedule.get_skipped()
    if skipped:
        print("-" * 55)
        print("\nSKIPPED (not enough time)\n")
        for pet, task in skipped:
            print(f"  - [{pet.name}] {task.name} ({task.duration} min, {task.priority})")
        print()

    print("-" * 55)
    over = schedule.total_time_used > owner.available_time
    used = schedule.total_time_used
    avail = owner.available_time
    if over:
        print(f"  Time used: {used} min  (over budget by {used - avail} min -- urgent tasks kept)")
    else:
        print(f"  Time used: {used} / {avail} min  ({avail - used} min to spare)")
    print("=" * 55)


if __name__ == "__main__":
    main()
