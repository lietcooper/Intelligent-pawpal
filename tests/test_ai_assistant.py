from datetime import date, time

from ai_assistant import CareAssistant, KnowledgeBase, ScheduleContext
from pawpal_system import Pet, Task, User


def write_knowledge(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "dog_care.md").write_text(
        "# Dog Care\nDogs need daily walks, hydration, rest breaks, and medication consistency.",
        encoding="utf-8",
    )
    (knowledge_dir / "cat_care.md").write_text(
        "# Cat Care\nCats need predictable feeding, clean litter, quiet rest, and enrichment.",
        encoding="utf-8",
    )
    (knowledge_dir / "schedule_guidelines.md").write_text(
        "# Scheduling\nResolve conflicts by moving flexible low-priority tasks and protecting high-priority care.",
        encoding="utf-8",
    )
    return knowledge_dir


def test_knowledge_base_loads_markdown_files(tmp_path):
    knowledge_dir = write_knowledge(tmp_path)
    kb = KnowledgeBase(knowledge_dir)

    assert len(kb.snippets) == 3
    assert {snippet.source for snippet in kb.snippets} == {
        "dog_care.md",
        "cat_care.md",
        "schedule_guidelines.md",
    }


def test_retrieve_prioritizes_species_guidance(tmp_path):
    knowledge_dir = write_knowledge(tmp_path)
    kb = KnowledgeBase(knowledge_dir)

    dog_results = kb.retrieve("walk hydration schedule", species="dog", limit=2)
    cat_results = kb.retrieve("feeding rest schedule", species="cat", limit=2)

    assert dog_results[0].source == "dog_care.md"
    assert cat_results[0].source == "cat_care.md"


def test_retrieve_finds_scheduling_guidance_for_conflicts(tmp_path):
    knowledge_dir = write_knowledge(tmp_path)
    kb = KnowledgeBase(knowledge_dir)

    results = kb.retrieve("conflict low priority flexible task", limit=2)

    assert results[0].source == "schedule_guidelines.md"


def test_schedule_context_includes_pets_tasks_and_conflicts():
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    user.add_pet(pet)
    task = Task("Walk", "Morning walk", date.today(), pet,
                duration_minutes=30, priority="high", preferred_time=time(8, 0))
    user.schedule_task(task)
    scheduled, explanations = user.planner.make_plan(date.today())
    conflicts = user.planner.find_conflicts(scheduled)

    context = ScheduleContext.from_user(user, scheduled, explanations, conflicts)
    text = context.to_text()

    assert "Mochi" in text
    assert "Walk" in text
    assert "high" in text
    assert "No conflicts" in text


def test_assistant_fallback_works_without_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    knowledge_dir = write_knowledge(tmp_path)
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    user.add_pet(pet)
    task = Task("Walk", "Morning walk", date.today(), pet,
                duration_minutes=30, priority="high", preferred_time=time(8, 0))
    user.schedule_task(task)
    scheduled, explanations = user.planner.make_plan(date.today())
    context = ScheduleContext.from_user(user, scheduled, explanations, [])

    assistant = CareAssistant(KnowledgeBase(knowledge_dir), provider="local")
    response = assistant.explain_schedule(context)

    assert response.used_model is False
    assert response.provider == "local"
    assert response.error is None
    assert "Mochi" in response.answer
    assert "Walk" in response.answer
    assert "dog_care.md" in response.sources


class FakeOpenAIClient:
    def __init__(self):
        self.last_input = None
        self.last_model = None
        self.responses = self

    def create(self, model, input):
        self.last_model = model
        self.last_input = input

        class Result:
            output_text = "Model answer grounded in retrieved pet care guidance."

        return Result()


def test_assistant_openai_path_uses_retrieved_context(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    knowledge_dir = write_knowledge(tmp_path)
    client = FakeOpenAIClient()
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    user.add_pet(pet)
    task = Task("Walk", "Morning walk", date.today(), pet)
    user.schedule_task(task)
    scheduled, explanations = user.planner.make_plan(date.today())
    context = ScheduleContext.from_user(user, scheduled, explanations, [])

    assistant = CareAssistant(
        KnowledgeBase(knowledge_dir),
        provider="openai",
        model="gpt-test",
        openai_client=client,
    )
    response = assistant.explain_schedule(context)

    assert response.used_model is True
    assert response.provider == "openai"
    assert response.answer == "Model answer grounded in retrieved pet care guidance."
    assert client.last_model == "gpt-test"
    assert "Mochi" in client.last_input
    assert "dog_care.md" in client.last_input


class FailingOpenAIClient:
    responses = None

    def __init__(self):
        self.responses = self

    def create(self, model, input):
        raise RuntimeError("model unavailable")


def test_assistant_falls_back_when_model_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    knowledge_dir = write_knowledge(tmp_path)
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    user.add_pet(pet)
    task = Task("Walk", "Morning walk", date.today(), pet)
    user.schedule_task(task)
    scheduled, explanations = user.planner.make_plan(date.today())
    context = ScheduleContext.from_user(user, scheduled, explanations, [])

    assistant = CareAssistant(
        KnowledgeBase(knowledge_dir),
        provider="openai",
        openai_client=FailingOpenAIClient(),
    )
    response = assistant.explain_schedule(context)

    assert response.used_model is False
    assert response.provider == "local"
    assert "model unavailable" in response.error
    assert "Walk" in response.answer


class FakeGeminiClient:
    def __init__(self):
        self.last_contents = None
        self.last_model = None
        self.models = self

    def generate_content(self, model, contents):
        self.last_model = model
        self.last_contents = contents

        class Result:
            text = "Gemini answer grounded in retrieved pet care guidance."

        return Result()


def test_assistant_gemini_path_uses_retrieved_context(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    knowledge_dir = write_knowledge(tmp_path)
    client = FakeGeminiClient()
    user = User("u1", "Jordan")
    pet = Pet("p1", "Mochi", user, "female", 3, "dog", "Shiba Inu")
    user.add_pet(pet)
    task = Task("Walk", "Morning walk", date.today(), pet)
    user.schedule_task(task)
    scheduled, explanations = user.planner.make_plan(date.today())
    context = ScheduleContext.from_user(user, scheduled, explanations, [])

    assistant = CareAssistant(
        KnowledgeBase(knowledge_dir),
        provider="gemini",
        model="gemini-test",
        gemini_client=client,
    )
    response = assistant.explain_schedule(context)

    assert response.used_model is True
    assert response.provider == "gemini"
    assert response.answer == "Gemini answer grounded in retrieved pet care guidance."
    assert client.last_model == "gemini-test"
    assert "Mochi" in client.last_contents
    assert "dog_care.md" in client.last_contents
