# PawPal+ Model Card

## Project Name

**PawPal+**: an AI-assisted pet care planner for daily and recurring care tasks.

## Intended Use

PawPal+ is designed to help pet owners organize routine care tasks such as feeding, walks, medication reminders, grooming, and enrichment. The app generates a daily schedule, shows upcoming recurring tasks on a calendar, provides in-app reminders, and produces AI Care Notes grounded in a local pet-care knowledge base.

The AI feature is intended for planning support and general care guidance only. It is not intended to diagnose illness, replace a veterinarian, or make medication decisions.

## Original Project Summary

The original Modules 1-3 project was **PawPal+**, a deterministic pet care scheduling app. Its original goals were to let users create an owner profile, add pets, enter care tasks, and generate a daily plan based on available time, task priority, frequency, and conflicts. It included multi-pet support, filtering, checklists, recurring task logic, urgent reminders, conflict detection, and tests for the scheduling behaviors.

The current version extends that project with local RAG, AI Care Notes, reliability checks, logging, biweekly recurrence, and an upcoming calendar.

## AI System Overview

PawPal+ uses a local Retrieval-Augmented Generation workflow:

1. The user enters pets and care tasks in the Streamlit UI.
2. The deterministic `Scheduler` generates the daily plan and skipped-task list.
3. `CareCoach` builds a query from the actual schedule, including pet species, categories, priorities, skipped tasks, urgent tasks, conflicts, and notes.
4. `PetCareKnowledgeBase` retrieves relevant guidance from markdown files in `knowledge_base/`.
5. `CareCoach` writes user-facing AI Care Notes from the schedule plus retrieved guidance.
6. `CareNoteReliabilityTester` checks the generated note for safety and consistency.
7. Logs are written to `pawpal.log`, and automated tests verify the AI and scheduling behavior.

The user sees the final care notes, not the raw retrieved sources or reliability PASS/FAIL details.

## AI Collaboration Reflection

AI was used as a development collaborator throughout the project. It helped brainstorm architecture, generate Mermaid diagrams, suggest class responsibilities, identify edge cases, draft tests, and refine the README and model card. AI was also used to reason through how to add RAG and reliability checks without making the app depend on an external API key.

The most useful AI collaboration happened when prompts were specific and scoped. For example, asking for a targeted system diagram or a test case for recurrence was more effective than asking AI to design the whole app at once.

I did not accept AI suggestions automatically. I kept the deterministic scheduler separate from the AI care-note system because scheduling should be predictable and testable. I also removed raw reliability-check UI from the user experience after seeing that it looked like developer/debug output instead of helpful product behavior.

## Human Judgment and Verification

Human judgment was used in several places:

- Deciding that AI should explain the schedule, not create the schedule.
- Keeping medication guidance conservative and adding veterinary guardrails.
- Hiding retrieved-source and reliability-check details from the user-facing UI.
- Adding a calendar because weekly and biweekly tasks are easier to understand visually.
- Reviewing tests to make sure they covered realistic failures like zero available time, overlapping tasks, and unsafe medication advice.

The AI-generated or AI-assisted work was verified through code review, manual app checks, and automated tests.

## Biases and Limitations

### Knowledge Base Bias

The RAG system retrieves from a small local knowledge base. This makes the app reproducible, but it also means the AI Care Notes reflect only the content included in those markdown files. The current knowledge base covers common dog, cat, rabbit, medication, enrichment, and scheduling guidance, but it is not comprehensive.

### Species Coverage Bias

The strongest built-in guidance is for dogs, cats, and rabbits. Birds and other animals can still be added as pets, but their AI care notes may be less specific because the knowledge base has less species-specific information for them.

### Medical Safety Limitations

The app can remind users that medication tasks are important, but it cannot determine whether a medication is correct, whether symptoms are urgent, or whether a dose should change. Medication-related notes include a guardrail telling users to follow the label and veterinarian instructions.

### Scheduling Bias

The scheduler prioritizes high-priority tasks and time budget. This can cause lower-priority enrichment or grooming tasks to be skipped when the day is full. That is intentional for safety, but it may under-schedule quality-of-life tasks if the owner consistently has limited time.

### UI and Persistence Limitations

The app uses Streamlit session state. Data is not persisted to a database, so refreshing or restarting can lose entered pets/tasks unless persistence is added later. The tests focus on backend logic, not full browser-based UI behavior.

## Guardrails

PawPal+ includes several safeguards:

- Medication notes tell users to follow veterinary instructions.
- Unsafe advice patterns such as "skip medication" or "change the dose" are flagged by the reliability tester.
- AI notes are generated from retrieved local guidance rather than unrestricted web content.
- The deterministic scheduler remains the source of truth for what is scheduled.
- High-priority tasks are kept even if they exceed the available time budget.
- Conflicting timed tasks are surfaced to the user.
- AI/retrieval events are logged in `pawpal.log`.

## Testing Results

The project currently has **30 passing tests**.

Command used:

```bash
python -m pytest
```

Latest result:

```text
30 passed
```

Test coverage includes:

- Task completion and undo behavior
- Daily, weekly, biweekly, and as-needed recurrence
- End-time calculation from start time and duration
- Adding and removing pet tasks
- Duplicate task warning behavior
- Sorting tasks by start time
- Filtering by pet, completion status, and category
- Detecting overlapping timed tasks
- Empty owner and empty pet edge cases
- Zero available time behavior
- High-priority urgent scheduling
- Multi-pet task aggregation
- Upcoming calendar occurrence generation
- RAG retrieval from the local knowledge base
- AI Care Notes generation using schedule context
- Reliability checks for unsafe medication advice and missing retrieved context

## What Worked

The strongest part of the project is the separation between deterministic scheduling and AI-generated explanation. The scheduler can be tested independently, while the RAG system adds context and user-friendly reasoning.

The local knowledge base also worked well because it made the AI feature reproducible. A reviewer can run the project without setting up an API key, and the retrieved content can be inspected directly.

The reliability tester helped make the AI feature more responsible. It checks that the generated note is grounded in retrieved context and avoids unsafe medication advice.

## What Did Not Work or Needs Improvement

The Streamlit UI itself is not fully covered by automated tests. Session state behavior, checkbox interactions, and visual layout still require manual verification.

The AI Care Notes are retrieval-grounded but template-based. A future version could connect to a hosted language model while keeping the same retriever, evaluator, and guardrails.

The knowledge base is intentionally small. It should be expanded before the app is used for a wider range of species, medical conditions, or accessibility needs.

The calendar is useful but simple. A production version would benefit from persistent storage, editing tasks from the calendar, and reminders that can be sent by email, SMS, or browser push notifications.

## Reflection on AI and Problem-Solving

This project taught me that AI is most useful when it is part of a larger engineered system. A generic chatbot response would not be enough for PawPal+ because users need reliable schedules, reminders, and safe handling of care tasks. The best design was to let deterministic code make scheduling decisions and let RAG-based AI explain those decisions with supporting context.

I also learned that AI transparency has to be designed for the audience. Developers and graders need logs, tests, and reliability checks, but regular users need a clean answer. Showing raw retrieved sources and PASS/FAIL checks made the UI feel confusing, so those details were moved behind the scenes.

The biggest takeaway is that responsible AI work requires constraints. Retrieval, guardrails, tests, and human review all made the final app more trustworthy than an unrestricted AI assistant.
