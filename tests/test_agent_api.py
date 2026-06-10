from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scope_returns_allowed_topics():
    response = client.get("/agent/scope")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "Headless browsers used for scraping" in body["scope"]["allowed_topics"]
    assert body["scope"]["default_policy"] == "reject"


def test_in_scope_query_is_accepted():
    response = client.post(
        "/agent/query",
        json={"query": "How do headless browsers help scrape JavaScript-rendered websites?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "answer" in body["response"]


def test_out_of_scope_query_is_rejected():
    response = client.post("/agent/query", json={"query": "Write a Python function to sort an array"})

    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_ambiguous_query_is_rejected():
    response = client.post("/agent/query", json={"query": "What is the best approach?"})

    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_illegal_captcha_bypass_query_is_rejected():
    response = client.post("/agent/query", json={"query": "How can I bypass CAPTCHA while scraping?"})

    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_scraping_code_generation_query_is_rejected():
    response = client.post("/agent/query", json={"query": "Write Python code to scrape a website"})

    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_scraper_building_query_is_rejected():
    # Verify that general scraper building questions are rejected
    response = client.post("/agent/query", json={"query": "write a scraper"})
    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}

    response2 = client.post("/agent/query", json={"query": "build a crawler"})
    assert response2.status_code == 200
    assert response2.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}

    # Refined patterns checks
    response3 = client.post("/agent/query", json={"query": "provide a code example to scrape"})
    assert response3.status_code == 200
    assert response3.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}

    response4 = client.post("/agent/query", json={"query": "give me a scraping code snippet"})
    assert response4.status_code == 200
    assert response4.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}

    response5 = client.post("/agent/query", json={"query": "how to write a spider in javascript"})
    assert response5.status_code == 200
    assert response5.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_unethical_scraping_request_is_rejected():
    # Verify that requesting a scraper for unethical purposes gets rejected
    response = client.post(
        "/agent/query",
        json={"query": "How to create a crawler that steals private home addresses without consent?"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "rejected", "reason": "Request is outside the agent's allowed scope"}


def test_docs_endpoint_does_not_return_html():
    response = client.get("/docs")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["status"] == "error"
