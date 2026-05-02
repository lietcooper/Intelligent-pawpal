# PawPal+ RAG Care Assistant Model Card

## System Overview

**Base project:** PawPal+, the original Modules 1-3 Streamlit pet-care scheduler.

**AI feature:** RAG Care Assistant.

**Purpose:** Explain and improve a generated pet-care schedule by retrieving local guidance, combining it with current pets/tasks/conflicts, and returning grounded recommendations.

**Intended users:** Pet owners planning routine care and students reviewing RAG, reliability, and human-in-the-loop AI design.

## How It Works

1. The user adds pets and care tasks in Streamlit.
2. `pawpal_system.py` generates a daily schedule and conflict report.
3. `ScheduleContext` formats pets, tasks, schedule notes, and conflicts.
4. `KnowledgeBase` retrieves relevant Markdown guidance from `knowledge/`.
5. `CareAssistant` builds a grounded prompt.
6. The selected provider runs:
   - `Local fallback`: deterministic response, no API key.
   - `OpenAI`: uses `OPENAI_API_KEY`.
   - `Gemini`: uses `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
7. The app shows the answer, source filenames, provider status, and fallback warnings.

## Inputs and Outputs

**Inputs:**

- Pet profiles: name, species, breed, age.
- Care tasks: title, duration, priority, recurrence, preferred time.
- Generated schedule: scheduled start/end times and planner explanations.
- Conflict report: same-pet or cross-pet overlaps.
- Retrieved guidance: local Markdown snippets from `knowledge/`.

**Outputs:**

- Schedule summary.
- Risk or conflict explanation.
- Practical next actions.
- Source filenames used by retrieval.
- Provider status: OpenAI, Gemini, or local fallback.

## Base Models and Dependencies

The app does not fine-tune a model. It uses retrieval over local Markdown files and optionally calls hosted LLMs:

- OpenAI default model: `gpt-4o-mini`
- Gemini default model: `gemini-2.5-flash`
- Local fallback: deterministic template response

Users can edit the model name in the Streamlit UI.

## Reliability and Testing Results

Reliability is measured with automated tests, mocked model clients, fallback behavior, logging, and human review.

Latest test result:

```text
28 out of 28 automated tests passed.
```

Test coverage includes:

- Markdown knowledge loading.
- Species-aware retrieval ranking.
- Scheduling guidance retrieval for conflict queries.
- Schedule context formatting.
- Local fallback without API keys.
- Mocked OpenAI model calls.
- Mocked Gemini model calls.
- Model-error fallback behavior.
- Existing planner behavior: task lifecycle, recurrence, conflicts, sorting, and scheduling.

The assistant improved after adding validation around missing API keys and model failures. The main remaining weakness is retrieval quality: keyword scoring works for a small knowledge base but may miss nuanced questions as the content grows.

## Reliability and Safety Rules

- **No required hosted model:** If the selected provider lacks an API key or fails, the assistant returns local fallback output instead of crashing.
- **Grounded source display:** Responses include source filenames so humans can check whether advice came from relevant guidance.
- **Network-free tests:** Model calls are mocked in tests, so reliability checks are reproducible.
- **UI guardrails:** The assistant asks users to add pets, add tasks, and generate a schedule before requesting AI output.
- **Logging:** The assistant logs loaded knowledge, retrieved sources, unknown providers, and model-call failures.

## Limitations and Biases

The assistant depends on a small local knowledge base. Its guidance reflects the content in `knowledge/`, which currently focuses on general dog, cat, and scheduling advice. It may underrepresent unusual pets, medical conditions, disabilities, breed-specific risks, emergency care, and region-specific pet-care norms.

The LLM providers may also produce confident wording even when the retrieved context is limited. The app reduces this by showing sources and falling back safely, but users still need to review recommendations critically.

## Misuse Risks and Prevention

The assistant could be misused if someone treats it as veterinary or medical authority. It is designed for routine schedule explanation, not diagnosis, medication decisions, emergency triage, or professional care replacement.

Current prevention steps:

- Keep advice general and schedule-focused.
- Show source filenames for human review.
- Use fallback behavior instead of inventing output when model calls fail.
- Require an existing schedule context before generating advice.

Future prevention steps:

- Add explicit warnings for medication, injury, illness, and emergency questions.
- Add a refusal/redirect rule for veterinary diagnosis requests.
- Add richer human evaluation examples for unsafe or unsupported prompts.

## What Surprised Me While Testing Reliability

The most surprising result was that reliability depended as much on non-AI code as on the model. Retrieval ranking, context formatting, provider selection, missing-key handling, and fallback behavior controlled whether the model received useful information and whether the app stayed usable when a model was unavailable.

The tests showed that mocked model clients are essential. They let the project verify OpenAI and Gemini paths without relying on network access, API quota, or model variability.

## Human-in-the-Loop Evaluation

Humans review the assistant output in Streamlit. The UI displays the generated answer and retrieved source filenames, so reviewers can check:

- Did the answer mention the actual pets and tasks?
- Did it correctly identify conflicts or no-conflict schedules?
- Are the recommendations supported by the displayed sources?
- Did fallback mode behave clearly when credentials were missing?

## AI Collaboration Reflection

AI was helpful in suggesting a RAG approach instead of fine-tuning. That suggestion matched the project size, kept the feature explainable, and made the AI behavior easier to test.

A flawed or risky suggestion would be making one hosted provider mandatory for every answer. That would make the project harder to grade and less reproducible for employers or reviewers without API credentials. The final design uses selectable OpenAI, Gemini, and local fallback modes.

Another useful AI-assisted idea was separating `ai_assistant.py` from `app.py`. That made the service layer testable before UI integration.

## Improvement Ideas

- Replace keyword retrieval with embeddings if the knowledge base grows.
- Add a confidence score based on retrieval score, source count, and whether fallback mode was used.
- Add an explicit veterinary-safety guardrail for health, medication, injury, or emergency prompts.
- Add a small human evaluation checklist with pass/fail examples for generated schedule advice.
