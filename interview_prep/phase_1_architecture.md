# Phase 1: What the Project is and How it Works (Explained Simply)

Use this guide to explain the project setup in a simple, natural way during the interview. No complicated terms—just clear, human explanations.

---

## 1. What does this project do?
"Basically, this is a web scraping Q&A assistant. It answers general questions about web scraping—like how to deal with JavaScript websites, headless browsers, or legal stuff—but it blocks users from asking for actual code, scripts, or instructions to hack and bypass CAPTCHAs. 

If someone asks a question that is borderline or confusing, the system plays it safe and blocks it. We call this a 'fail-closed' setup—if we aren't sure, we just reject it."

---

## 2. Why we chose these tools (In simple words)

* **FastAPI**: "It's my go-to for building small APIs in Python. It's super fast, supports async out of the box, and uses Pydantic to check if incoming data is correct before we run it. Django is way too big for this, and Flask doesn't have native type-checking."
* **LangGraph**: "This handles the step-by-step flow. Instead of writing a messy pile of `if/else` checks in python, LangGraph let us build a state machine. First, it goes to the guardrail check node. If that's good, it goes to the responder node. If not, it stops early. It keeps our code neat and ready to scale."
* **LangChain**: "This is just our helper library to talk to the LLMs. It lets us write prompts and format the outputs easily, so we can swap between OpenAI and Gemini without changing our main code."
* **Pytest**: "It's just the easiest and cleanest way to write Python tests. We can mock requests and check if our guardrails are actually blocking bad queries in milliseconds."

---

## 3. How a query flows through the code (Step-by-Step)
1. **User asks a question**: The client sends a query to our FastAPI server (`POST /agent/query`).
2. **First Check (Basic Rules)**: The query goes to our guardrail node. We check it using simple python code (regex and keywords) to catch obvious code requests or bad words. If it fails, we block it immediately.
3. **Second Check (Smart LLM Check)**: If the query looks safe and we have LLM API keys set up, we ask the LLM to read it. The LLM decides if the query is genuinely safe or if it's a clever prompt injection. If the LLM says no, we block it.
4. **Router Decision**: Our code checks if the query passed both layers. If it did, it routes the query to the responder node. If not, it terminates early and returns a rejected JSON.
5. **Answer Generation**: If it's safe, the responder node runs the LLM (or a local template if we are offline) to write a high-level plain text answer.
6. **Result**: FastAPI returns the JSON response (either success with the answer, or rejected with the reason).
