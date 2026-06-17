# Phase 4: Mock Interview & Grill Session (Theoretical/Architectural)

This document contains core technical and architectural questions. The answers are written in a **natural, concise, and conversational human tone**—exactly how you should speak in a live call to show confidence and expertise.

---

## 1. Tech Stack Justifications (FastAPI, LangChain, LangGraph)

### Q1: What is the difference between LangChain and LangGraph? For what do we use each?
* **Answer:**  
  "LangChain is our wrapper for interacting with the LLM. We use it to set up prompt templates, manage provider classes like OpenAI or Gemini, and enforce structured JSON outputs. 
  
  LangGraph is our state machine. We use it to coordinate the execution flow. It lets us define steps as nodes—like running the guardrail first, and then generating the response—and route between them using conditional logic. Basically, LangChain handles the LLM logic, and LangGraph manages the workflow."

### Q2: Why use LangGraph for a simple app like this? Couldn't we just write a standard Python `if/else` script?
* **Answer:**  
  "For this simple version, yes, standard `if/else` checks would work. But in production, agents are rarely linear. They require multi-turn memory, human approval steps, or recovery loops if the model outputs bad formatting. 
  
  Writing that in sequential Python quickly turns into unmaintainable spaghetti code. LangGraph keeps the codebase clean and modular as the agent scales, modeling the system as a clean state machine."

### Q3: Why FastAPI? Why not Flask or Django?
* **Answer:**  
  "FastAPI is my default for building AI microservices. It's incredibly fast, supports asynchronous requests natively, and uses Pydantic for automatic data validation. 
  
  Django is too heavy and bloated for a simple microservice, and Flask doesn't support async routing or native Pydantic validation without adding a bunch of extra packages."

### Q4: Why Pydantic? Why not just use Python dictionaries?
* **Answer:**  
  "Pydantic handles our request validation automatically. If a user sends an empty query or bad JSON, Pydantic catches it at the API entry point and returns a 422 validation error. 
  
  If we used normal dictionaries, I'd have to write manual boilerplate checks for key presence, length, and types, which is messy and prone to bugs."

### Q5: Why did you choose Pytest instead of Python's built-in `unittest`?
* **Answer:**  
  "Pytest is just cleaner and more pythonic. It uses plain `assert` statements instead of verbose ones like `self.assertEqual`. It also integrates perfectly with FastAPI's `TestClient`, letting us write and run integration tests in milliseconds with very little boilerplate."

---

## 2. Guardrails, Security, & Production Scaling

### Q6: Why did you combine programmatic (regex) and semantic (LLM) guardrails?
* **Answer:**  
  "It's about speed and budget. The programmatic regex checks are deterministic, instant, and cost nothing—they immediately catch obvious stuff like 'write a python scraper'. 
  
  The semantic LLM layer only runs if the query passes the regex checks. It catches sophisticated prompt injections or paraphrased requests. This keeps our token bill low and keeps the API fast for basic inputs."

### Q7: What does "fail-closed" mean in this system?
* **Answer:**  
  "It means if a query is ambiguous, empty, or borderline, we default to rejecting it. For a scoped scraping agent, it's much better to reject a safe query by mistake than to allow a query that bypasses CAPTCHAs or violates site terms, which could expose us to legal risks."

### Q8: In production, calling the LLM twice (once for guardrail, once for answer) doubles latency. How would you optimize this?
* **Answer:**  
  "I'd do three things:
  1. **Semantic Cache**: Use a vector DB like Redis to cache past query decisions. If a new query is highly similar, return the cached result instantly.
  2. **Async Parallel Tasks**: Trigger the guardrail check and responder generation at the same time using `asyncio`. If the guardrail rejects the request, we just cancel the responder task.
  3. **Model Tiering**: Use a small, cheap local model like Llama 3 8B for the guardrail classification, and save the larger model for writing the actual response."

### Q9: How does this system protect against prompt injection?
* **Answer:**  
  "First, the regex layer blocks common override patterns. Second, we use LangChain's `with_structured_output` to force the LLM to output to our Pydantic schema (`GuardrailOutput`). By binding the output to a strict JSON structure, it's very difficult for a user's input prompt to hijack the model's behavior and bypass the validation flag."
