# PawPal+ RAG Care Assistant Architecture

```text
Human user
  |
  | adds pets, tasks, preferred times, recurrence
  v
Streamlit app.py
  |
  | Generate schedule
  v
Planner in pawpal_system.py
  |
  | scheduled tasks, explanations, conflicts
  v
ScheduleContext builder
  |
  | query from pets + tasks + conflicts
  v
KnowledgeBase retriever
  |
  | relevant snippets from knowledge/*.md
  v
CareAssistant
  |
  | provider = OpenAI + OPENAI_API_KEY
  | provider = Gemini + GEMINI_API_KEY or GOOGLE_API_KEY
  | provider = Local fallback, missing key, or model error
  v
Selected LLM provider or deterministic fallback
  |
                  |
                  v
Grounded schedule explanation with source filenames
                  |
                  v
Human reviews recommendations in Streamlit

Testing loop:
pytest -> retrieval ranking, context formatting, fallback output,
mocked OpenAI/Gemini calls, and existing scheduling behavior.
```
