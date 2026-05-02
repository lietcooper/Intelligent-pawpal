import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "in", "is", "it", "of", "on", "or", "that", "the", "to",
    "with", "your",
}


@dataclass
class KnowledgeSnippet:
    source: str
    title: str
    content: str
    score: int = 0


@dataclass
class CareAssistantResponse:
    answer: str
    sources: list
    used_model: bool
    provider: str = "local"
    model: str | None = None
    error: str | None = None


@dataclass
class ScheduleContext:
    pets: list
    tasks: list
    scheduled_tasks: list
    explanations: list
    conflicts: list

    @classmethod
    def from_user(cls, user, scheduled, explanations, conflicts):
        return cls(
            pets=list(user.pets),
            tasks=list(user.planner.tasks),
            scheduled_tasks=list(scheduled),
            explanations=list(explanations),
            conflicts=list(conflicts),
        )

    def species(self):
        return sorted({p.species for p in self.pets if getattr(p, "species", None)})

    def to_text(self):
        lines = ["Pets:"]
        if self.pets:
            for pet in self.pets:
                lines.append(
                    f"- {pet.pet_name}: {pet.age}-year-old {pet.species}, breed {pet.breed}"
                )
        else:
            lines.append("- None")

        lines.append("Tasks:")
        if self.tasks:
            for task in self.tasks:
                pet_name = getattr(task.pet, "pet_name", "Unknown pet")
                lines.append(
                    f"- {task.name} for {pet_name}: {task.duration_minutes} min, "
                    f"{task.priority} priority, status {task.status}"
                )
        else:
            lines.append("- None")

        lines.append("Generated schedule:")
        if self.scheduled_tasks:
            for task in self.scheduled_tasks:
                start = task.scheduled_start.strftime("%I:%M %p") if task.scheduled_start else "unscheduled"
                end = task.scheduled_end.strftime("%I:%M %p") if task.scheduled_end else "unscheduled"
                lines.append(f"- {start}-{end}: {task.name} for {task.pet.pet_name}")
        else:
            lines.append("- No scheduled tasks")

        lines.append("Planner notes:")
        if self.explanations:
            lines.extend(f"- {item}" for item in self.explanations)
        else:
            lines.append("- None")

        lines.append("Conflicts:")
        if self.conflicts:
            for conflict in self.conflicts:
                a = conflict["task_a"]
                b = conflict["task_b"]
                lines.append(
                    f"- {conflict['overlap']}: {a.name} for {a.pet.pet_name} overlaps "
                    f"{b.name} for {b.pet.pet_name}"
                )
        else:
            lines.append("- No conflicts")

        return "\n".join(lines)


class KnowledgeBase:
    def __init__(self, knowledge_dir="knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.snippets = self._load_snippets()

    def _load_snippets(self):
        if not self.knowledge_dir.exists():
            logger.warning("Knowledge directory not found: %s", self.knowledge_dir)
            return []

        snippets = []
        for path in sorted(self.knowledge_dir.glob("*.md")):
            content = path.read_text(encoding="utf-8").strip()
            if not content:
                continue
            title = path.stem.replace("_", " ").title()
            first_line = content.splitlines()[0].strip()
            if first_line.startswith("#"):
                title = first_line.lstrip("#").strip()
            snippets.append(KnowledgeSnippet(path.name, title, content))

        logger.info("Loaded %s knowledge snippets", len(snippets))
        return snippets

    def retrieve(self, query, species=None, limit=3):
        query_terms = _tokenize(query)
        if species:
            query_terms.extend(_tokenize(species))

        ranked = []
        for snippet in self.snippets:
            text = f"{snippet.source} {snippet.title} {snippet.content}"
            terms = _tokenize(text)
            score = sum(terms.count(term) for term in query_terms)
            if species and species.lower() in text.lower():
                score += 3
            ranked.append(KnowledgeSnippet(
                source=snippet.source,
                title=snippet.title,
                content=snippet.content,
                score=score,
            ))

        ranked.sort(key=lambda item: (item.score, item.source), reverse=True)
        return [item for item in ranked if item.score > 0][:limit]


class CareAssistant:
    def __init__(
        self,
        knowledge_base=None,
        provider="openai",
        model=None,
        openai_client=None,
        gemini_client=None,
    ):
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.provider = provider
        self.model = model or self._default_model(provider)
        self.openai_client = openai_client
        self.gemini_client = gemini_client

    def explain_schedule(self, context):
        query = self._query_from_context(context)
        species = context.species()[0] if context.species() else None
        snippets = self.knowledge_base.retrieve(query, species=species, limit=3)
        prompt = self._build_prompt(context, snippets)
        sources = [snippet.source for snippet in snippets]

        logger.info("Care assistant retrieved sources: %s", sources)

        if self.provider == "local":
            fallback = self._fallback_response(context, snippets)
            return CareAssistantResponse(fallback, sources, used_model=False, provider="local")

        if self.provider == "openai" and os.getenv("OPENAI_API_KEY"):
            try:
                answer = self._call_openai(prompt)
                if answer:
                    return CareAssistantResponse(
                        answer, sources, used_model=True,
                        provider="openai", model=self.model,
                    )
                raise RuntimeError("OpenAI response was empty")
            except Exception as exc:
                logger.exception("Model call failed; using fallback response")
                fallback = self._fallback_response(context, snippets)
                return CareAssistantResponse(
                    fallback, sources, used_model=False,
                    provider="local", model=self.model, error=str(exc),
                )

        if self.provider == "gemini" and (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            try:
                answer = self._call_gemini(prompt)
                if answer:
                    return CareAssistantResponse(
                        answer, sources, used_model=True,
                        provider="gemini", model=self.model,
                    )
                raise RuntimeError("Gemini response was empty")
            except Exception as exc:
                logger.exception("Gemini call failed; using fallback response")
                fallback = self._fallback_response(context, snippets)
                return CareAssistantResponse(
                    fallback, sources, used_model=False,
                    provider="local", model=self.model, error=str(exc),
                )

        if self.provider not in ("openai", "gemini", "local"):
            logger.warning("Unknown provider '%s'; using fallback response", self.provider)

        fallback = self._fallback_response(context, snippets)
        return CareAssistantResponse(fallback, sources, used_model=False, provider="local")

    def _default_model(self, provider):
        if provider == "gemini":
            return "gemini-2.5-flash"
        if provider == "local":
            return None
        return "gpt-4o-mini"

    def _call_openai(self, prompt):
        client = self.openai_client or self._make_openai_client()
        result = client.responses.create(model=self.model, input=prompt)
        return getattr(result, "output_text", "").strip()

    def _call_gemini(self, prompt):
        client = self.gemini_client or self._make_gemini_client()
        result = client.models.generate_content(model=self.model, contents=prompt)
        return getattr(result, "text", "").strip()

    def _make_openai_client(self):
        from openai import OpenAI

        return OpenAI()

    def _make_gemini_client(self):
        from google import genai

        return genai.Client()

    def _query_from_context(self, context):
        parts = ["pet care schedule conflict priority routine"]
        parts.extend(context.species())
        parts.extend(task.name for task in context.tasks)
        if context.conflicts:
            parts.append("conflict overlap reschedule")
        return " ".join(parts)

    def _build_prompt(self, context, snippets):
        guidance = "\n\n".join(
            f"Source: {snippet.source}\n{snippet.content}" for snippet in snippets
        )
        return (
            "You are PawPal+'s RAG Care Assistant. Use only the schedule context "
            "and retrieved guidance below. Give concise, practical recommendations.\n\n"
            f"Schedule context:\n{context.to_text()}\n\n"
            f"Retrieved guidance:\n{guidance or 'No guidance retrieved.'}\n\n"
            "Answer with: 1) summary, 2) risks or conflicts, 3) next best actions."
        )

    def _fallback_response(self, context, snippets):
        scheduled_count = len(context.scheduled_tasks)
        task_names = ", ".join(task.name for task in context.scheduled_tasks[:4]) or "no scheduled tasks"
        pet_names = ", ".join(pet.pet_name for pet in context.pets) or "your pets"
        sources = ", ".join(snippet.source for snippet in snippets) or "local schedule context"

        if context.conflicts:
            conflict_note = (
                f"I found {len(context.conflicts)} conflict(s). Move flexible or lower-priority "
                "tasks first, and keep high-priority care in place."
            )
        else:
            conflict_note = "I did not find schedule conflicts in the generated plan."

        guidance_note = "Use steady routines, protect high-priority care, and leave rest gaps."
        if snippets:
            guidance_note = _first_sentence(snippets[0].content)

        return (
            f"Summary: {pet_names} has {scheduled_count} scheduled task(s): {task_names}.\n\n"
            f"Risk check: {conflict_note}\n\n"
            f"Recommendation: {guidance_note}\n\n"
            f"Sources used: {sources}"
        )


def _tokenize(text):
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if token not in STOP_WORDS and len(token) > 1]


def _first_sentence(text):
    clean = re.sub(r"#+\s*", "", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", clean)
    return parts[0] if parts else clean
