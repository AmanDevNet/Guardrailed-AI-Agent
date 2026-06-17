# Phase 5: Quick Cheat Sheet & Reminders (Before the Call)

Read this in the final 15 minutes before the interview. It has the commands you'll need, file roles, and simple phrases to use.

---

## 1. Quick Commands to Run

### Run tests to verify code edits:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\pytest
```

### Start the server locally:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\uvicorn app.main:app --reload
```
*Server runs at `http://127.0.0.1:8000`*

### Run with Docker Compose:
```bash
docker-compose up --build
docker-compose run --rm guardrailed-agent python -m pytest
```

---

## 2. File Roles at a Glance

- **schemas.py**: Checking inputs/outputs using Pydantic.
- **main.py**: Starting the server, routing paths, and turning off Swagger/docs endpoints.
- **graph.py**: Defining our nodes and routing edges using LangGraph.
- **guardrails.py**: Doing the programmatic regex checks and semantic LLM checks.
- **responder.py**: Generating the final educational response (or fallback offline replies).
- **test_agent_api.py**: Running integration tests with `TestClient`.

---

## 3. High-Impact Terms (Use them naturally)

- **"Fail-closed"**: "It means if the query is ambiguous, we reject it. Better to block a safe request than to risk code leaks or bypass instructions."
- **"State machine flow"**: "We model the system in LangGraph as nodes and edges. It keeps routing logic clean and makes it easy to add memory or loops later."
- **"Pydantic Validation"**: "We use Pydantic to validate data contracts. If a query is bad or empty, FastAPI catches it at the door and throws a 422 automatically."
- **"Footprint Reduction"**: "We turned off `/docs` and `/openapi.json` to keep our API schema private from potential scanners."
- **"Structured LLM Output"**: "We bind our LLM check to a Pydantic schema using `with_structured_output`. This keeps responses formatted exactly as JSON and stops prompt injection."
- **"Offline Fallback"**: "If there are no API keys, the system downgrades to regex checks and static responses. It lets our tests run instantly offline."
