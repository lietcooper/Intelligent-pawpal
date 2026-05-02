# PawPal+ RAG Care Assistant

**Base project:** PawPal+, the original Modules 1-3 Streamlit pet-care scheduler.

PawPal+ helps pet owners organize daily care tasks across multiple pets. The original project let users add pets, create tasks, detect time conflicts, auto-schedule recurring tasks, and generate a conflict-aware daily plan.

This version adds a RAG Care Assistant. After a schedule is generated, the assistant retrieves local pet-care guidance, combines it with the current pets, tasks, schedule, and conflicts, then explains risks and recommends improvements. This makes the planner more useful because it does not only arrange tasks; it helps owners understand the quality of the plan.

## Architecture Overview

The system diagram is in [assets/rag_architecture.md](assets/rag_architecture.md).

The data flow is:

1. A human user adds pets and care tasks in `app.py`.
2. `pawpal_system.py` generates a daily schedule and conflict report.
3. `ScheduleContext` converts the current app state into text.
4. `KnowledgeBase` retrieves relevant Markdown guidance from `knowledge/`.
5. The user selects `Local fallback`, `OpenAI`, or `Gemini` in the assistant panel.
6. `CareAssistant` sends the grounded prompt to the selected model when the matching API key is set.
7. If no key exists or the model call fails, the assistant returns a deterministic local fallback.
8. The user reviews the answer and source filenames in Streamlit.

Tests check retrieval, fallback behavior, mocked model calls, and the original planner logic.

## Setup Instructions

Requirements:

- Python 3.10+
- Dependencies in `requirements.txt`
- Optional OpenAI or Gemini API key for model-generated responses

Install and run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Optional OpenAI setup:

```bash
export OPENAI_API_KEY="your-api-key"
streamlit run app.py
```

Optional Gemini setup:

```bash
export GEMINI_API_KEY="your-api-key"
streamlit run app.py
```

In the app, choose `OpenAI`, `Gemini`, or `Local fallback` from the AI Care Assistant provider menu. You can also edit the model name, such as `gpt-4o-mini` or `gemini-2.5-flash`.

Run tests:

```bash
pytest -v
```

## Sample Interactions

### Example 1: Dog schedule with no conflicts

Input schedule:

- Mochi, dog
- 8:00 AM Walk, high priority
- 9:00 AM Breakfast, medium priority

Sample AI output:

```text
Summary: Mochi has 2 scheduled tasks: Walk, Breakfast.

Risk check: I did not find schedule conflicts in the generated plan.

Recommendation: Dogs benefit from predictable routines for feeding, walks, medication, hydration, and rest.

Sources used: dog_care.md, schedule_guidelines.md
```

### Example 2: Crowded schedule with overlapping preferred times

Input schedule:

- Mochi, dog
- Luna, cat
- Walk and Feed both requested around 9:00 AM

Sample AI output:

```text
Summary: Mochi, Luna has 2 scheduled tasks: Walk, Feed.

Risk check: I found 1 conflict(s). Move flexible or lower-priority tasks first, and keep high-priority care in place.

Recommendation: Protect high-priority tasks first, especially medication, meals, vet care, and time-sensitive routines.

Sources used: schedule_guidelines.md, dog_care.md, cat_care.md
```

### Example 3: No model API key

Input:

- User clicks `Explain and improve schedule` with `Local fallback`, or selects OpenAI/Gemini without setting the matching API key.

Result:

```text
The app still returns a local fallback response with retrieved source filenames.
```

## Design Decisions

- Local Markdown RAG keeps the project easy to run and inspect.
- Keyword retrieval was chosen over a vector database because the knowledge base is small.
- OpenAI and Gemini are optional so graders and contributors can run the app without credentials.
- Provider selection is exposed in the UI so users can compare model output or stay fully local.
- The AI logic lives in `ai_assistant.py` instead of `app.py` so it can be tested directly.
- Tests mock the model path to avoid network calls and keep results reproducible.

## Testing Summary

The test suite covers:

- Knowledge loading from Markdown files
- Species-aware retrieval ranking
- Scheduling guidance retrieval for conflicts
- Schedule context formatting
- Local fallback output without an API key
- Mocked OpenAI and Gemini model calls
- Model error fallback behavior
- Existing task lifecycle, recurrence, conflict detection, sorting, and scheduling behavior

What worked well: service-layer testing made the RAG feature easy to verify before UI integration. The fallback path also made the app reliable when credentials are missing.

What was limited: keyword retrieval is simple and transparent, but it is less flexible than embeddings for larger knowledge bases.

## Reliability and Evaluation

The RAG Care Assistant is evaluated with automated tests, logging, error handling, and human review in the Streamlit UI.

- Automated tests: `pytest -v` currently runs 28 tests. The AI-specific tests check Markdown loading, species-aware retrieval, conflict-guidance retrieval, schedule context formatting, local fallback output, mocked OpenAI output, mocked Gemini output, and model-error fallback.
- Logging and error handling: `ai_assistant.py` logs loaded knowledge, retrieved source files, and model-call failures. If the selected provider is unavailable or returns an error, the app falls back to a deterministic local response instead of crashing.
- Human evaluation: the Streamlit UI shows the answer and source filenames, so a reviewer can check whether the recommendation is grounded in retrieved guidance and the actual schedule.

Latest evaluation summary:

```text
28 out of 28 automated tests passed.
The assistant handled missing API keys, OpenAI/Gemini provider selection, and mocked model failures with fallback responses.
The main limitation is retrieval quality: keyword scoring works for this small knowledge base, but may miss nuanced questions if the knowledge files grow.
```

## Reflection

This project showed that useful AI features do not have to start with a large system. A small RAG layer can make an existing planner more helpful by grounding advice in both app state and curated guidance.

The full AI reflection, ethics review, bias discussion, collaboration notes, and testing results are documented in [model_card.md](model_card.md).
