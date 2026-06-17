# Phase 5: Quick Revision Cheat Sheet & Setup Guide

Use this cheat sheet in the final 30 minutes before your interview. It contains quick-access commands, codebase file roles, and key terms to mention during the interview.

---

## 1. Quick Commands Cheat Sheet

### Run the Test Suite (Local PowerShell)
Always use these commands to verify code changes immediately during screen sharing:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\pytest
```

### Start the FastAPI Dev Server
```powershell
$env:PYTHONPATH="."
.venv\Scripts\uvicorn app.main:app --reload
```
*Serves locally at `http://127.0.0.1:8000`*

### Query the API via PowerShell (Open a second terminal window)
- **Allowed Query Example:**
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/agent/query" -Method Post -ContentType "application/json" -Body '{"query": "How do headless browsers help scrape websites?"}' | ConvertTo-Json
  ```
- **Rejected Query Example:**
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/agent/query" -Method Post -ContentType "application/json" -Body '{"query": "Write a python script to sort an array"}' | ConvertTo-Json
  ```

### Run using Docker Compose
```bash
# Build and run the app container
docker-compose up --build

# Run tests inside Docker
docker-compose run --rm guardrailed-agent python -m pytest
```

---

## 2. Codebase Files & Roles at a Glance

- [schemas.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/schemas.py): Pydantic input/output schemas (`QueryRequest`, `SuccessResponse`, `RejectionResponse`, `GuardrailOutput`).
- [main.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/main.py): FastAPI app, custom exception handlers, routes (`/health`, `/agent/scope`, `/agent/query`), and security settings (disabled Swagger docs).
- [graph.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/graph.py): LangGraph state machine configuration (`AgentState`), nodes (`guardrail_node`, `answer_node`), conditional routing logic (`route_after_guardrail`), and execution trigger (`run_agent`).
- [guardrails.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/guardrails.py): Double-layer guardrail validation logic (regex + keywords positive/negative filters first, LLM semantic checks second, fail-closed handling).
- [responder.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/responder.py): Answer generation logic (LLM invocation chain + offline fallback text template generator).
- [test_agent_api.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/tests/test_agent_api.py): Pytest integration tests covering 10 critical security, compliance, and functional scenarios.

---

## 3. High-Impact Terms to Drop in the Interview
Dropping these terms naturally in your explanations will demonstrate senior-level engineering understanding:

- **"Fail-Closed Design Pattern"**: Explain that you prioritize system security and compliance by rejecting queries by default if they are ambiguous or fail validation.
- **"State Machine Routing"**: Mention that LangGraph allows modeling agent execution flows as state machines where transitions are directed and state updates are merged automatically.
- **"Deterministic vs. Semantic Guardrails"**: Mention that the dual-layer approach uses deterministic regex first to cut latency/costs, and semantic LLMs second to check intent.
- **"Swagger/Footprint Reduction"**: Explain that you set `docs_url=None` and `openapi_url=None` in production to prevent malicious third parties from performing endpoint reconnaissance.
- **"Tool/Structured Output Coercion"**: Mention that you use LangChain's `with_structured_output` to bind the LLM response to a Pydantic class. This forces the model to adhere to the schema and blocks prompt injection attempts from altering the output format.
- **"RunnableLambda Abstraction"**: Explain that wrapping functions in LangChain's `RunnableLambda` standardizes inputs/outputs so they integrate with other chains and graph nodes natively.
- **"Offline Resiliency"**: Mention that the system automatically degrades to offline mode if API keys are missing, allowing local development and CI/CD pipelines to run test suites mock-free without external network dependency.
