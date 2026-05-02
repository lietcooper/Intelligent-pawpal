# Repository Guidelines

## Project Structure & Module Organization

PawPal+ is a small Python/Streamlit app for pet care scheduling.

- `app.py` contains the Streamlit UI and session state flow.
- `pawpal_system.py` contains the core domain model and scheduling logic.
- `ai_assistant.py` contains RAG retrieval, schedule context formatting, OpenAI integration, and fallback responses.
- `main.py` provides a script-style entry point/demo flow.
- `tests/` contains pytest coverage for tasks, recurrence, conflicts, sorting, and planning.
- `knowledge/` contains local Markdown files used by the RAG assistant.
- `README.md` is the user manual. `class_diagram.md` and `class_diagram.png` document the design.
- `demo.png` and `assets/` hold visual assets and architecture diagrams.

Keep scheduling logic in `pawpal_system.py`, AI logic in `ai_assistant.py`, and UI-only code in `app.py`.

## Build, Test, and Development Commands

Create and activate a local environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app locally:

```bash
streamlit run app.py
```

Run tests:

```bash
pytest -v
```

Optional model output requires `OPENAI_API_KEY`. Without it, the assistant uses local fallback output.

## Coding Style & Naming Conventions

Use standard Python style with 4-space indentation. Prefer clear names such as `scheduled_start`, `preferred_time`, and `duration_minutes`. Classes use `PascalCase`; functions, methods, and variables use `snake_case`.

Write short comments only where they clarify non-obvious scheduling behavior. Keep UI labels concise and user-facing. Avoid mixing Streamlit code into domain classes.

## Testing Guidelines

Tests use `pytest`. Add or update tests in `tests/test_pawpal.py` when changing task state, recurrence, conflict detection, sorting, or scheduling behavior. Add or update `tests/test_ai_assistant.py` when changing retrieval, prompt context, model calls, or fallback behavior.

Name tests with `test_` plus the expected behavior, for example `test_no_conflict_adjacent_tasks`. Cover edge cases such as date rollover, same-pet conflicts, cross-pet conflicts, and day-boundary overflow.

For AI changes, keep reliability measurable. Test retrieval ranking, fallback behavior, mocked model calls, and error handling. Keep model tests network-free and include source filenames in assistant responses so humans can evaluate grounding.

## Commit & Pull Request Guidelines

Recent commits use short imperative messages, sometimes with a prefix such as `feat:` or `test:`. Examples:

- `feat: implement sorting, filtering, and conflict detection`
- `test: add automated test suite for PawPal+ system`
- `finalized design and polished UI`

Keep commits focused on one change. Pull requests should include a brief summary, tests run, and screenshots or notes for visible Streamlit UI changes. Link related issues or assignment tasks when available.

## Security & Configuration Tips

Do not commit virtual environments, caches, or local secrets. Keep dependencies in `requirements.txt`. Do not hard-code `OPENAI_API_KEY`; read it from the environment.
