# Phase 2: Walking Through the Files (Explained Simply)

Here is a super simple breakdown of what every file does. Use this if the interviewer asks you to share your screen and explain the files.

---

## 1. schemas.py (Checking the Data)
"This file is where we define what our data looks like. We use Pydantic to validate things. 
For example, `QueryRequest` makes sure the user actually sends a question and doesn't leave it blank. If they leave it blank, the API throws a 422 error automatically. 
`SuccessResponse` and `RejectionResponse` format the output so the client always gets a clean, predictable JSON response. 
`GuardrailOutput` is just a schema that tells the LLM: 'You must reply with JSON that has a true/false flag and a reason string.'"

---

## 2. main.py (The API Server)
"This is the entry point for the API. It starts FastAPI, defines the routes, and catches errors. 
Notice we have `/health` for checking if the server is running, `/agent/scope` to show our allowed topics, and `/agent/query` to run the agent. 
Also, I turned off the default Swagger documentation endpoints (`docs_url=None`) because in production, you don't want random people scanning your API structure. 
We also have global error handlers so that if something breaks, the client gets a clean JSON response instead of a scary python error traceback."

---

## 3. graph.py (The State Machine)
"This is the brain of the flow, built using LangGraph. It sets up the steps and routes. 
We have `AgentState` which holds the query, the true/false check, and the final answer. 
First, we go to `guardrail_node`. It calls our guardrail logic. 
Then, `route_after_guardrail` checks: did the guardrail allow this? If yes, it routes to `answer_node`. If no, it routes to the end (`END`). 
Finally, `run_agent()` compiles the graph and executes it when a request comes in."

---

## 4. guardrails.py (The Security Layer)
"This is where our two-layer check happens. 
First, we run the programmatic checks (`validate_scope_programmatic`). This is just plain Python. It checks regex patterns for bad stuff like 'write a python scraper' or CAPTCHA bypasses. It also checks if the query contains positive keywords about web scraping. 
Second, if that passes and we have an API key, we run the semantic check (`validate_scope_llm`). This asks the LLM: 'Hey, read this query. Is it safe or are they trying to bypass the rules?'
If both checks say yes, the query is allowed."

---

## 5. responder.py (Writing the Answer)
"This generates the actual response once a query is approved. 
If we have API keys, it runs a chain with a prompt that says: 'Answer this question in high-level terms. Do not write code, and keep it plain text (no markdown styling).'
If we are running offline without API keys, it calls `_build_answer_fallback` which uses basic keyword matching to return pre-written educational answers, so the application still works for local testing."

---

## 6. test_agent_api.py (The Test Suite)
"This contains our integration tests using Pytest. 
It uses FastAPI's `TestClient` to make dummy requests to our API. 
We have tests to make sure safe questions are allowed, and out-of-scope questions (like writing code, bypassing captcha, or hacking) are blocked. It makes sure that everything behaves exactly as expected without us needing to spin up a live server."
