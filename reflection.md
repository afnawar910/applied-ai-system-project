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

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
