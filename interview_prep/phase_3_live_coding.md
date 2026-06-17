# Phase 3: Live Coding Scenarios (Explained Simply)

This guide shows you how to explain your code edits to an interviewer in a simple, natural way if they ask you to make live changes on a call.

---

## Scenario A: Add a new topic (e.g., Scraping HTML Tables)
**Interviewer says:** *"Can you add a 6th topic, 'Scraping dynamic HTML tables', and write a test for it?"*

### How to explain what you're doing:
1. "First, I'll go to `app/guardrails.py`. I need to add the new topic to `ALLOWED_TOPICS` so it shows up in the scope endpoint. I'll also add it to the LLM system prompt so the model knows it's allowed."
2. "Next, I need to make sure our regex/programmatic check doesn't block it. I'll add table-related terms—like 'table' or 'dataframe'—to our check list in `validate_scope_programmatic`."
3. "Then, in `app/responder.py`, I'll update the offline fallback responder so that if we test offline, it has a pre-written response for table scraping."
4. "Finally, I'll open `tests/test_agent_api.py`, add a test case that queries 'how to scrape tables safely', run `pytest` in the terminal, and verify it passes."

---

## Scenario B: Change the rejection reason to be specific
**Interviewer says:** *"Right now, every rejection says the same thing. Can you make it return a specific reason, like 'Writing code is not allowed'?"*

### How to explain what you're doing:
1. "I'll go to `app/guardrails.py` and modify `validate_scope_programmatic`. 
2. Currently, we return `REJECTION_REASON` for every check. I'll change each return block to have its own message. E.g., for `_GENERAL_PROGRAMMING_PATTERNS`, I'll return `GuardrailDecision(False, 'Writing code or debugging is out-of-scope')`."
3. "Note that this will break some of our unit tests because they check for the exact default message. I'll need to go to `tests/test_agent_api.py` and update the expected response strings in our assertions."

---

## Scenario C: Always run the LLM check (No early exit)
**Interviewer says:** *"What if we want to run the LLM check on every single request, even if the regex checks fail, so we can log comparisons?"*

### How to explain what you're doing:
1. "I'll go to `app/guardrails.py` and look at the `validate_scope` coordinator function.
2. Currently, if programmatic checks fail, we return immediately. I'll change it to run the programmatic check, run the LLM check, and then evaluate both.
3. If either check fails, we return `allowed=False`. This lets us run both checks for every query and print/log the results without changing the fail-closed behavior."

---

## Scenario D: Bypass the guardrail check node
**Interviewer says:** *"How can we test the responder node's answers on any raw inputs without the guardrail blocking them?"*

### How to explain what you're doing:
1. "I'll go to `app/graph.py` where the LangGraph is defined.
2. The easiest way is to change the starting node of our graph. I can change `graph.set_entry_point('guardrail')` to `graph.set_entry_point('respond')`.
3. Alternatively, I can go to the router function `route_after_guardrail` and just force it to return `'respond'` instead of checking `state.get('allowed')`."
