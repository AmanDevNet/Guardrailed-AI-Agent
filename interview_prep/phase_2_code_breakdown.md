# Phase 2: Codebase Breakdown (Explain It Simply)

This guide breaks down every file in the codebase in plain, conversational English, exactly how you would explain it to an interviewer during a screen-share.

---

## 1. [schemas.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/schemas.py) – Input/Output Validation
* **What is it?**  
  This file defines the data contracts of our API. We use Pydantic (v2) models to validate incoming requests and structure outgoing responses.
* **Key Components:**
  - `QueryRequest`: Validates the client's input. The `min_length=1` ensures the query isn't empty. If it is empty, FastAPI rejects it instantly with a 422 error.
  - `SuccessResponse` & `RejectionResponse`: Force the API to output a standardized JSON format. If it's a success, it returns status and the answer. If it's a rejection, it returns status and the reason.
  - `GuardrailOutput`: A schema used specifically by our LLM guardrail. We force the LLM to reply with a JSON matching this structure (`allowed: bool`, `reason: str`).

---

## 2. [main.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/main.py) – FastAPI Setup & Endpoints
* **What is it?**  
  The entry point of our API server. It sets up FastAPI, configures custom exception handlers, and exposes the HTTP endpoints.
* **Key Components:**
  - `app = FastAPI(...)`: Initializes the app. Notice we set `docs_url=None`, `redoc_url=None`, and `openapi_url=None`. This disables the default Swagger documentation endpoints to prevent potential attackers from scanning our API schema.
  - `exception_handler` decorators: Capture errors globally. If there's a validation error, we return a 422 JSON. If there's an internal crash, we catch it and return a 500 JSON without exposing raw tracebacks.
  - `/agent/query` route: Accepts the validated query payload and calls `run_agent()`, which runs the query through our LangGraph state machine.

---

## 3. [graph.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/graph.py) – LangGraph Workflow Orchestrator
* **What is it?**  
  This file configures the execution flow of our agent using a state machine graph.
* **Key Components:**
  - `AgentState`: A TypedDict that tracks state variables (`query`, `allowed`, `answer`, `reason`, `status`) as they flow through nodes.
  - `guardrail_node`: Runs our safety validation checks on the query. If the query fails, it flags `allowed=False` and sets the rejection reason.
  - `answer_node`: Runs only if the query is safe. It calls the responder module to generate the answer.
  - `route_after_guardrail`: A conditional routing function. It reads `allowed` from the state. If true, it directs execution to the `respond` node. If false, it routes straight to the `END` node.
  - `build_graph()`: Constructs the graph nodes, entry point, conditional edge routing, and compiles it.

---

## 4. [guardrails.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/guardrails.py) – Dual-Layer Security
* **What is it?**  
  The security heart of the project. It verifies if the query is in-scope or out-of-scope using two layers: regex lists first, and LLM checks second.
* **Key Components:**
  - **Programmatic check (`validate_scope_programmatic`)**: Runs regex checks against negative patterns (like writing code, bypass captcha, greetings, legal/medical questions). If the query passes, it checks for positive keywords (like scrape, headless, ethical).
  - **LLM check (`validate_scope_llm`)**: Runs if API keys are available. It sends the query to the LLM alongside `GUARDRAIL_PROMPT` and utilizes `with_structured_output(GuardrailOutput)` to parse the response into structured JSON.
  - `validate_scope`: Coordinates the two. It runs programmatic first. If that allows the query, and LLM keys exist, it runs the semantic LLM check.

---

## 5. [responder.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/responder.py) – Response Generation
* **What is it?**  
  Generates the final high-level educational response once the query has been cleared by the guardrail.
* **Key Components:**
  - `_build_answer_fallback`: Our local keyword-matching database. If no API keys are present (offline testing), it scans the query for words like "captcha", "headless", or "legal" and returns a pre-configured, professional, static answer.
  - `RESPONDER_PROMPT`: Directs the LLM to answer in high-level educational terms, strictly forbids code writing or bypass instructions, and explicitly requests plain text (no markdown headings or bolding).
  - `response_chain`: Uses LangChain's `RunnableLambda` to wrap the generation logic so it is compatible with other chains and executes cleanly as a graph node.

---

## 6. [test_agent_api.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/tests/test_agent_api.py) – Integration Tests
* **What is it?**  
  Our test suite using Pytest and FastAPI's `TestClient` to verify endpoints and security rules.
* **Key Components:**
  - `client = TestClient(app)`: Simulates requests directly to the FastAPI server code without needing a live network port.
  - Test cases: Verify that health check works, scope works, safe queries are allowed, and invalid queries (writing code, hacking, casual chat) are rejected with a `"rejected"` status.
