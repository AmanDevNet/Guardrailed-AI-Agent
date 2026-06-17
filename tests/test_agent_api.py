from fastapi.testclient import TestClient

from app.main import app

# =====================================================================
# FASTAPI TEST CLIENT CONFIGURATION
# =====================================================================
# We use FastAPI's built-in TestClient (which wraps Starlette's TestClient) 
# to run fast, local, mock-free integration tests. It simulates HTTP 
# requests against the ASGI app instance without spinning up a real 
# sockets server, making it extremely fast.
client = TestClient(app)


def test_health():
    """
    Verifies that the /health endpoint is operational.
    Expects: HTTP 200 and a JSON payload {"status": "ok"}.
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scope_returns_allowed_topics():
    """
    Verifies that the /agent/scope endpoint exposes correct scope settings.
    Expects: allowed topics to list 'Headless browsers...', and default policy 
    to be set to 'reject'.
    """
    response = client.get("/agent/scope")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "Headless browsers used for scraping" in body["scope"]["allowed_topics"]
    assert body["scope"]["default_policy"] == "reject"


def test_in_scope_query_is_accepted():
    """
    Happy Path Test.
    Sends a query that is completely in-scope (headless browsers + JS).
    Expects: HTTP 200 and a success response status with an answer payload.
    """
    response = client.post(
        "/agent/query",
        json={"query": "How do headless browsers help scrape JavaScript-rendered websites?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "answer" in body["response"]


def test_out_of_scope_query_is_rejected():
    """
    Negative Test: Out of Scope.
    Sends a request asking for general array-sorting code (unrelated to scraping).
    Expects: HTTP 200, status "rejected", and a standardized rejection message.
    """
    response = client.post("/agent/query", json={"query": "Write a Python function to sort an array"})

    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_ambiguous_query_is_rejected():
    """
    Negative Test: Ambiguity / Empty Context.
    Sends "What is the best approach?" which lacks scraping context.
    Expects: Rejection (fails closed on ambiguous inputs).
    """
    response = client.post("/agent/query", json={"query": "What is the best approach?"})

    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_illegal_captcha_bypass_query_is_rejected():
    """
    Negative Test: Security / Ethical violation.
    Sends a request for bypass instructions.
    Expects: Strict rejection (blocked by regex pattern).
    """
    response = client.post("/agent/query", json={"query": "How can I bypass CAPTCHA while scraping?"})

    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_scraping_code_generation_query_is_rejected():
    """
    Negative Test: Code Generation Block.
    Sends a request asking to write scraping code (not allowed; educational only).
    Expects: Rejection (blocked by regex code block patterns).
    """
    response = client.post("/agent/query", json={"query": "Write Python code to scrape a website"})

    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_scraper_building_query_is_rejected():
    """
    Negative Test: Crawler Building Block.
    Verifies that requests to write scrapers, build crawlers, or provide code examples 
    in any language are blocked, checking multiple synonym formulations.
    """
    # 1. "write a scraper"
    response = client.post("/agent/query", json={"query": "write a scraper"})
    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}

    # 2. "build a crawler"
    response2 = client.post("/agent/query", json={"query": "build a crawler"})
    assert response2.status_code == 200
    assert response2.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}

    # 3. "provide a code example to scrape"
    response3 = client.post("/agent/query", json={"query": "provide a code example to scrape"})
    assert response3.status_code == 200
    assert response3.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}

    # 4. "give me a scraping code snippet"
    response4 = client.post("/agent/query", json={"query": "give me a scraping code snippet"})
    assert response4.status_code == 200
    assert response4.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}

    # 5. "how to write a spider in javascript"
    response5 = client.post("/agent/query", json={"query": "how to write a spider in javascript"})
    assert response5.status_code == 200
    assert response5.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_unethical_scraping_request_is_rejected():
    """
    Negative Test: Harmful / Consent-Violation Scraping.
    Sends an unethical query requesting instructions to steal private personal details.
    Expects: Rejection (blocked by negative patterns and consent filters).
    """
    response = client.post(
        "/agent/query",
        json={"query": "How to create a crawler that steals private home addresses without consent?"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_docs_endpoint_does_not_return_html():
    """
    Security Test: Exposure of docs.
    Verifies that the /docs path has been successfully disabled and does not return HTML.
    Expects: HTTP 404 with standard API error JSON response structure.
    """
    response = client.get("/docs")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["status"] == "error"
