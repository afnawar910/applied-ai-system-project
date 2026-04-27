"""
RAG-powered care notes for PawPal+.

This module keeps the AI feature local and reproducible: it retrieves relevant
pet-care guidance from markdown files, uses that context to generate schedule
notes, and runs simple reliability checks before the app displays the result.
"""

from dataclasses import dataclass
import logging
from pathlib import Path
import re

from pawpal_system import Owner, Pet, Schedule, Task


LOGGER = logging.getLogger("pawpal.care_ai")
if not LOGGER.handlers:
    logging.basicConfig(
        filename="pawpal.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@dataclass
class CareDocument:
    """One retrievable chunk from the local knowledge base."""

    source: str
    title: str
    text: str


@dataclass
class RetrievalResult:
    """A retrieved document plus its keyword score."""

    document: CareDocument
    score: int


@dataclass
class ReliabilityReport:
    """Result of checking whether generated care notes meet safety rules."""

    passed: bool
    checks: dict[str, bool]
    warnings: list[str]


@dataclass
class CareNote:
    """The final RAG output shown in the app."""

    text: str
    sources: list[str]
    retrieved: list[RetrievalResult]
    reliability: ReliabilityReport


class PetCareKnowledgeBase:
    """Loads and retrieves pet-care guidance from local markdown files."""

    def __init__(self, base_path: str | Path = "knowledge_base") -> None:
        self.base_path = Path(base_path)
        self._documents: list[CareDocument] | None = None

    def load_documents(self) -> list[CareDocument]:
        """Read markdown files and split them into retrievable sections."""
        if self._documents is not None:
            return self._documents

        documents: list[CareDocument] = []
        if not self.base_path.exists():
            LOGGER.warning("Knowledge base path does not exist: %s", self.base_path)
            self._documents = []
            return []

        for path in sorted(self.base_path.glob("*.md")):
            title = path.stem.replace("_", " ").title()
            current_heading = title
            buffer: list[str] = []
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if line.startswith("#"):
                    if buffer:
                        documents.append(CareDocument(path.name, current_heading, " ".join(buffer)))
                        buffer = []
                    current_heading = line.lstrip("#").strip() or title
                elif line:
                    buffer.append(line)
            if buffer:
                documents.append(CareDocument(path.name, current_heading, " ".join(buffer)))

        self._documents = documents
        LOGGER.info("Loaded %s care knowledge documents", len(documents))
        return documents

    def retrieve(self, query: str, limit: int = 5) -> list[RetrievalResult]:
        """Return the most relevant knowledge chunks for the schedule context."""
        query_terms = _tokens(query)
        scored: list[RetrievalResult] = []

        for document in self.load_documents():
            haystack = f"{document.title} {document.text} {document.source}"
            doc_terms = _tokens(haystack)
            score = len(query_terms & doc_terms)
            if score:
                scored.append(RetrievalResult(document=document, score=score))

        scored.sort(key=lambda result: (-result.score, result.document.source, result.document.title))
        LOGGER.info("Retrieved %s care documents for query terms=%s", len(scored[:limit]), sorted(query_terms))
        return scored[:limit]


class CareNoteReliabilityTester:
    """Small reliability system for generated RAG care notes."""

    unsafe_patterns = [
        "change medication dose",
        "change the dose",
        "skip medication",
        "ignore symptoms",
        "diagnose at home",
    ]

    def evaluate(
        self,
        note_text: str,
        schedule: Schedule,
        retrieved: list[RetrievalResult],
    ) -> ReliabilityReport:
        scheduled = schedule.get_checklist()
        skipped = schedule.get_skipped()
        urgent_tasks = [task.name.lower() for _, task in scheduled if task.is_urgent]
        has_med_task = any(task.category == "meds" for _, task in scheduled)

        lower_text = note_text.lower()
        checks = {
            "has_retrieved_context": bool(retrieved),
            "has_source_list": bool(retrieved),
            "mentions_urgent_tasks": all(name in lower_text for name in urgent_tasks),
            "mentions_skipped_tasks": not skipped or "skipped" in lower_text,
            "medication_guardrail": not has_med_task or "veterinarian" in lower_text,
            "avoids_unsafe_advice": not any(pattern in lower_text for pattern in self.unsafe_patterns),
        }
        warnings = [name.replace("_", " ") for name, passed in checks.items() if not passed]
        return ReliabilityReport(passed=all(checks.values()), checks=checks, warnings=warnings)


class CareCoach:
    """Generates schedule-specific care notes using retrieved guidance."""

    def __init__(
        self,
        knowledge_base: PetCareKnowledgeBase | None = None,
        tester: CareNoteReliabilityTester | None = None,
    ) -> None:
        self.knowledge_base = knowledge_base or PetCareKnowledgeBase()
        self.tester = tester or CareNoteReliabilityTester()

    def generate(self, owner: Owner, schedule: Schedule) -> CareNote:
        """Retrieve relevant guidance, generate notes, and run reliability checks."""
        query = self._build_query(owner, schedule)
        retrieved = self.knowledge_base.retrieve(query)
        note_text = self._compose_note(owner, schedule, retrieved)
        reliability = self.tester.evaluate(note_text, schedule, retrieved)

        if not reliability.passed:
            note_text += (
                "\n\nReliability note: Some checks need review: "
                + ", ".join(reliability.warnings)
                + ". Use the schedule as a planning aid, not as medical advice."
            )

        LOGGER.info(
            "Generated care note: sources=%s reliability_passed=%s warnings=%s",
            [result.document.source for result in retrieved],
            reliability.passed,
            reliability.warnings,
        )
        return CareNote(
            text=note_text,
            sources=sorted({result.document.source for result in retrieved}),
            retrieved=retrieved,
            reliability=reliability,
        )

    def _build_query(self, owner: Owner, schedule: Schedule) -> str:
        parts = [owner.name, str(owner.available_time), "daily schedule"]
        for pet, task in schedule.get_checklist():
            parts.extend(_task_terms(pet, task))
            if task.is_urgent:
                parts.append("urgent time budget")
        for pet, task, reason in schedule.get_skipped():
            parts.extend(_task_terms(pet, task))
            parts.append(reason)
            parts.append("skipped")
        for warning in getattr(schedule, "_conflicts", []):
            parts.extend(["conflict", warning])
        return " ".join(parts)

    def _compose_note(
        self,
        owner: Owner,
        schedule: Schedule,
        retrieved: list[RetrievalResult],
    ) -> str:
        scheduled = schedule.get_checklist()
        skipped = schedule.get_skipped()
        conflicts = getattr(schedule, "_conflicts", [])
        lines = [
            f"AI Care Notes for {owner.name}'s plan",
            "",
            self._schedule_sentence(schedule),
        ]

        if scheduled:
            high_priority = [f"{task.name} for {pet.name}" for pet, task in scheduled if task.priority == "high"]
            if high_priority:
                lines.append(
                    "High-priority care comes first today: "
                    + ", ".join(high_priority)
                    + ". These tasks protect basic health, routine, or safety."
                )

            urgent = [f"{task.name} for {pet.name}" for pet, task in scheduled if task.is_urgent]
            if urgent:
                lines.append(
                    "Urgent over-budget items were kept instead of skipped: "
                    + ", ".join(urgent)
                    + ". Consider freeing extra time or moving lower-priority chores."
                )

        if skipped:
            skipped_names = [f"{task.name} for {pet.name} ({reason})" for pet, task, reason in skipped]
            lines.append("Skipped today: " + "; ".join(skipped_names) + ".")

        if conflicts:
            lines.append("Time conflicts need review before the plan is final: " + "; ".join(conflicts))

        lines.extend(self._guidance_lines(retrieved))

        if any(task.category == "meds" for _, task in scheduled):
            lines.append(
                "Medication guardrail: follow the label and your veterinarian's instructions; "
                "do not change timing or dosage based only on this planner."
            )
        return "\n".join(lines)

    def _schedule_sentence(self, schedule: Schedule) -> str:
        scheduled_count = len(schedule.get_checklist())
        skipped_count = len(schedule.get_skipped())
        return (
            f"The generated plan schedules {scheduled_count} task(s), skips {skipped_count} task(s), "
            f"and uses {schedule.total_time_used} minute(s)."
        )

    def _guidance_lines(self, retrieved: list[RetrievalResult]) -> list[str]:
        if not retrieved:
            return [
                "No local care guidance matched this schedule, so the app only used the task data entered by the user."
            ]

        lines = ["Care tips for this plan:"]
        for result in retrieved[:3]:
            snippet = _shorten(result.document.text, 260)
            lines.append(f"- {result.document.title}: {snippet}")
        return lines


def _task_terms(pet: Pet, task: Task) -> list[str]:
    return [
        pet.species,
        pet.name,
        task.name,
        task.category,
        task.priority,
        task.frequency,
        task.notes,
    ]


def _tokens(text: str) -> set[str]:
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "today",
        "task",
        "tasks",
        "care",
        "daily",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in stop_words
    }


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
