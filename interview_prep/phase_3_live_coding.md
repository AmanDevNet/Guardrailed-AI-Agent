# Phase 3: Live Coding Scenarios (Exactly What to Copy and Paste)

This guide shows you the exact files, code blocks to search for, code modifications, and commands to run. Follow these steps if you are asked to share your screen and write code.

---

## Scenario A: Add a New Allowed Topic (e.g., HTML Tables)
**Interviewer says:** *"Can you add a 6th topic, 'Scraping dynamic HTML tables', and write a test for it?"*

### Step 1: Open [guardrails.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/guardrails.py)
1. **Search (Ctrl+F) for:** `ALLOWED_TOPICS = [` (around lines 8–15).
   * **Replace it with:**
     ```python
     ALLOWED_TOPICS = [
         "Web scraping concepts",
         "JavaScript-rendered websites",
         "CAPTCHA detection and high-level handling strategies without bypass instructions",
         "Headless browsers used for scraping",
         "Ethical and legal considerations of web scraping",
         "Scraping dynamic HTML tables",  # <-- Add this line
     ]
     ```
2. **Search (Ctrl+F) for:** `_ETHICS_TERMS = {` (around lines 60–71).
   * **Add below it:**
     ```python
     _TABLE_TERMS = {"table", "tables", "dataframe", "html table"}
     ```
3. **Search (Ctrl+F) for:** `allowed = any(` inside the `validate_scope_programmatic` function (around lines 250–265).
   * **Replace the block with:**
     ```python
         allowed = any(
             [
                 _contains_any(text, _SCRAPING_TERMS),
                 _contains_any(text, _JS_RENDERED_TERMS),
                 _contains_any(text, _CAPTCHA_TERMS),
                 _contains_any(text, _HEADLESS_TERMS),
                 _contains_any(text, _ETHICS_TERMS),
                 _contains_any(text, _TABLE_TERMS),  # <-- Add this line
             ]
         )
     ```
4. **Search (Ctrl+F) for:** `GUARDRAIL_PROMPT = ChatPromptTemplate.from_messages([` (around lines 170–190).
   * **Add below item 5** in the string prompt:
     ```text
     6. Scraping dynamic HTML tables
     ```

### Step 2: Open [responder.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/responder.py)
1. **Search (Ctrl+F) for:** `def _build_answer_fallback` (around line 8).
   * **Add at the beginning of the checks** (right below `text = query.lower()` around line 10):
     ```python
         if "table" in text or "dataframe" in text:
             return (
                 "Scraping dynamic HTML tables involves identifying table tags (<table>, <tr>, <td>), "
                 "waiting for elements to render in dynamic tables, and parsing row data into structured formats "
                 "like lists or pandas DataFrames. Avoid downloading tables in tight loops to prevent rate limits."
             )
     ```

### Step 3: Open [test_agent_api.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/tests/test_agent_api.py)
1. **Go to the very bottom of the file** and paste this new test:
     ```python
     def test_table_scraping_query_is_allowed():
         response = client.post(
             "/agent/query",
             json={"query": "How can I scrape dynamic HTML tables safely?"},
         )
         assert response.status_code == 200
         body = response.json()
         assert body["status"] == "success"
         assert "tables" in body["response"]["answer"].lower()
     ```

### Step 4: Verify
Open your PowerShell terminal and run:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\pytest
```

---

## Scenario B: Customize Rejection Reasons
**Interviewer says:** *"Can you change the guardrail so that general coding queries return 'Writing code is not allowed' instead of the generic error?"*

### Step 1: Open [guardrails.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/guardrails.py)
1. **Search (Ctrl+F) for:** `if _matches_any(text, _GENERAL_PROGRAMMING_PATTERNS):` inside the `validate_scope_programmatic` function (around line 250).
   * **Replace that return statement:**
     ```python
     if _matches_any(text, _GENERAL_PROGRAMMING_PATTERNS):
         return GuardrailDecision(False, "Writing code, scripts, or debugging is out-of-scope. I only provide educational explanations.")
     ```

### Step 2: Open [test_agent_api.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/tests/test_agent_api.py)
1. **Search (Ctrl+F) for:** `test_out_of_scope_query_is_rejected` (around line 37).
   * **Update the expected string in the assert line:**
     ```python
     def test_out_of_scope_query_is_rejected():
         response = client.post("/agent/query", json={"query": "Write a Python function to sort an array"})

         assert response.status_code == 200
         assert response.json() == {
             "status": "rejected", 
             "reason": "Writing code, scripts, or debugging is out-of-scope. I only provide educational explanations."
         }
     ```

### Step 3: Verify
Run:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\pytest
```

---

## Scenario C: Force LLM Evaluation (No Early Exit)
**Interviewer says:** *"Can we run the LLM check on every single request, even if programmatic rules fail, so we can log comparisons?"*

### Step 1: Open [guardrails.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/guardrails.py)
1. **Search (Ctrl+F) for:** `def validate_scope(query: str) -> GuardrailDecision:` (around lines 250–260).
   * **Replace the entire function code with this:**
     ```python
     def validate_scope(query: str) -> GuardrailDecision:
         # 1. Run programmatic check
         prog_decision = validate_scope_programmatic(query)
         
         # 2. Run LLM semantic check if keys exist (do not early return)
         llm_decision = GuardrailDecision(True)
         if has_llm_credentials():
             llm_decision = validate_scope_llm(query)
             
         # Log comparison
         print(f"Programmatic allowed={prog_decision.allowed} | LLM allowed={llm_decision.allowed}")
         
         # Fail-closed: block if EITHER rejects
         if not prog_decision.allowed:
             return prog_decision
         if not llm_decision.allowed:
             return llm_decision
             
         return GuardrailDecision(True)
     ```

### Step 2: Verify
Run:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\pytest
```

---

## Scenario D: Bypass Guardrail Node in LangGraph
**Interviewer says:** *"How can we bypass the guardrail step in our graph blueprint for testing?"*

### Step 1: Open [graph.py](file:///d:/AI%20Projects/PROJECTS/ML%20Projects/guardrailed-ai-agent-assignment/app/graph.py)
1. **Search (Ctrl+F) for:** `def build_graph():` (around line 41).
   * **Look for:** `graph.set_entry_point("guardrail")` (around line 45).
   * **Change it to:**
     ```python
     graph.set_entry_point("respond")
     ```
   * *This forces LangGraph to skip the guardrail step and go straight to the answer generator.*

### Step 2: Verify
Run:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\pytest
```
*(Note: Out-of-scope tests will fail because they are no longer blocked).*
