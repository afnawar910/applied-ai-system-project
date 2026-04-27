"""
Tests for PawPal+'s RAG care-note system.
"""

from care_ai import CareCoach, CareNoteReliabilityTester, PetCareKnowledgeBase
from pawpal_system import Owner, Pet, Scheduler, Task


def _owner_with_schedule(available_time=20):
    owner = Owner(name="Jordan", available_time=available_time)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task(name="Medication", category="meds", duration=10, priority="high"))
    pet.add_task(Task(name="Fetch", category="enrichment", duration=30, priority="low"))
    return owner, Scheduler(owner).generate()


def test_knowledge_base_retrieves_relevant_pet_care_guidance():
    """RAG should retrieve local care guidance before generating notes."""
    kb = PetCareKnowledgeBase()
    results = kb.retrieve("dog medication enrichment time budget", limit=3)

    assert results
    sources = {result.document.source for result in results}
    assert "medication_safety.md" in sources or "dog_care.md" in sources


def test_care_coach_generates_note_with_sources_and_schedule_context():
    """Generated notes should combine retrieved guidance with the actual schedule."""
    owner, schedule = _owner_with_schedule()
    note = CareCoach().generate(owner, schedule)

    assert note.retrieved
    assert note.sources
    assert "Medication" in note.text
    assert "Skipped" in note.text
    assert "Care tips for this plan:" in note.text
    assert note.reliability.passed


def test_reliability_tester_flags_unsafe_medication_advice():
    """The reliability system should catch unsafe generated advice."""
    _, schedule = _owner_with_schedule()
    tester = CareNoteReliabilityTester()

    report = tester.evaluate(
        "You can skip medication and change the dose if the day is busy. Sources used: medication_safety.md",
        schedule,
        retrieved=[],
    )

    assert report.passed is False
    assert report.checks["avoids_unsafe_advice"] is False
    assert report.checks["has_retrieved_context"] is False
