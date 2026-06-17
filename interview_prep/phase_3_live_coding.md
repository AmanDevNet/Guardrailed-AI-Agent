# Phase 3: Live Coding & Modification Scenarios

This document prepares you for live coding tasks. The interviewer might share their screen or ask you to share yours, modify the codebase, and verify the changes by running the test suite.

---

## Scenario A: Add a New Allowed Topic
**Prompt:** *"We want to allow our agent to answer questions about 'Scraping dynamic HTML tables' as a 6th allowed topic. Make the necessary changes and add a test case."*

### Step 1: Update Scope and Rules in `app/guardrails.py`
1. Add the topic to the `ALLOWED_TOPICS` list so it shows in the `/agent/scope` endpoint:
   ```python
   ALLOWED_TOPICS = [
       ...
       "Ethical and legal considerations of web scraping",
       "Scraping dynamic HTML tables",  # <-- Add this line
   ]
   ```
2. Create or extend positive keywords to permit the query programmatically. Add `"table"`, `"tables"`, `"dynamic table"`, `"html table"` to `_JS_RENDERED_TERMS` or create a new set:
   ```python
   _TABLE_TERMS = {"table", "tables", "dataframe", "html table"}
   ```
   And add it to the positive keyword checks in `validate_scope_programmatic`:
   ```python
   allowed = any(
       [
           _contains_any(text, _SCRAPING_TERMS),
           _contains_any(text, _JS_RENDERED_TERMS),
           _contains_any(text, _CAPTCHA_TERMS),
           _contains_any(text, _HEADLESS_TERMS),
           _contains_any(text, _ETHICS_TERMS),
           _contains_any(text, _TABLE_TERMS),  # <-- Add this check
       ]
   )
   ```
3. Update the LLM system prompt `GUARDRAIL_PROMPT` in `app/guardrails.py`:
   ```text
   6. Scraping dynamic HTML tables
   ```

### Step 2: Update Fallback Responder in `app/responder.py`
To support offline testing, add a local template to `_build_answer_fallback` and update the LLM prompt `RESPONDER_PROMPT` with the new topic:
```python
if "table" in text or "dataframe" in text:
    return (
        "Scraping dynamic HTML tables involves identifying table tags (<table>, <tr>, <td>), "
        "waiting for elements to render in dynamic tables, and parsing row data into structured formats "
        "like lists or pandas DataFrames. Avoid downloading tables in tight loops to prevent rate limits."
    )
```

### Step 3: Add a Test in `tests/test_agent_api.py`
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
Run the test suite to ensure the new test passes and no regression is introduced:
```powershell
$env:PYTHONPATH="."
.venv\Scripts\pytest
```

---

## Scenario B: Customize Rejection Reasons
**Prompt:** *"Currently, all rejections return the same generic message. Change the codebase so that programmatic checks return a specific reason (e.g., 'Programming request blocked' or 'Ethical violation blocked') instead of the default scope rejection reason."*

### Step 1: Modify `validate_scope_programmatic` in `app/guardrails.py`
Instead of returning `REJECTION_REASON` for every failure, change the return values:
```python
def validate_scope_programmatic(query: str) -> GuardrailDecision:
    text = " ".join(query.lower().split())

    if not text:
        return GuardrailDecision(False, "Query cannot be empty")

    if _matches_any(text, _ILLEGAL_INTENT_PATTERNS):
        return GuardrailDecision(False, "Request violates ethical policies or scraping safety constraints")

    if _matches_any(text, _CASUAL_PATTERNS):
        return GuardrailDecision(False, "Chit-chat and casual greetings are out-of-scope. Please ask a web scraping question.")

    if _matches_any(text, _SENSITIVE_OUT_OF_SCOPE_PATTERNS):
        return GuardrailDecision(False, "Sensitive domain questions (legal, medical, political) are out-of-scope")

    if _matches_any(text, _GENERAL_PROGRAMMING_PATTERNS):
        return GuardrailDecision(False, "Writing code, scripts, or debugging is out-of-scope. I only provide educational explanations.")
    
    # ... (rest of the checks)
```

### Step 2: Verify and Update Tests
If you run `pytest` now, several tests (like `test_out_of_scope_query_is_rejected`) will fail because they assert `assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}`.
You would explain this to the interviewer and show how you update the assertions to match the new granular messages, or change the API layer to map granular reasons.

---

## Scenario C: Force LLM Evaluation
**Prompt:** *"What if we want to run the LLM check on every single request, even if programmatic rules fail, so that we can log and analyze discrepancies between regex checks and LLM semantic decisions?"*

### Step 1: Modify `validate_scope` in `app/guardrails.py`
Change the entry point coordination function:
```python
def validate_scope(query: str) -> GuardrailDecision:
    # 1. Run programmatic check
    prog_decision = validate_scope_programmatic(query)
    
    # 2. Run LLM semantic check if credentials exist (do not early return)
    llm_decision = GuardrailDecision(True)
    if has_llm_credentials():
        llm_decision = validate_scope_llm(query)
        
    # Log the comparison (simulate logging)
    print(f"DEBUG: Programmatic allowed={prog_decision.allowed} | LLM allowed={llm_decision.allowed}")
    
    # Still enforce fail-closed: if either layer rejects, block the request
    if not prog_decision.allowed:
        return prog_decision
    if not llm_decision.allowed:
        return llm_decision
        
    return GuardrailDecision(True)
```

---

## Scenario D: Bypass Guardrails Node Entirely
**Prompt:** *"For debugging purposes, how would you configure the graph to bypass the guardrail node entirely so that we can directly test the responder node's answers on any raw inputs?"*

### Option 1: Modify the Entry Point in `app/graph.py`
Change the starting node of the StateGraph:
```python
def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("respond", answer_node)
    
    # Change entry point from "guardrail" to "respond"
    graph.set_entry_point("respond") 
    
    graph.add_conditional_edges("guardrail", route_after_guardrail, {"respond": "respond", END: END})
    graph.add_edge("respond", END)
    return graph.compile()
```

### Option 2: Modify the Conditional Router in `app/graph.py`
Force the routing logic to always return `"respond"`:
```python
def route_after_guardrail(state: AgentState) -> Literal["respond", "__end__"]:
    # return "respond" if state.get("allowed") else END
    return "respond" # <-- Force routing to responder node
```
