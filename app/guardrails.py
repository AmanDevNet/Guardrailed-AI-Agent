from dataclasses import dataclass
import os
import re
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

ALLOWED_TOPICS = [
    "Web scraping concepts",
    "JavaScript-rendered websites",
    "CAPTCHA detection and high-level handling strategies without bypass instructions",
    "Headless browsers used for scraping",
    "Ethical and legal considerations of web scraping",
]

REJECTION_REASON = "Request is outside the agent's allowed scope"

_SCRAPING_TERMS = {
    "scrape",
    "scraping",
    "crawler",
    "crawling",
    "spider",
    "parse html",
    "html parsing",
    "extract data",
    "web data extraction",
    "robots.txt",
    "rate limit",
    "user agent",
}

_JS_RENDERED_TERMS = {
    "javascript-rendered",
    "javascript rendered",
    "js-rendered",
    "js rendered",
    "spa",
    "single page app",
    "dynamic website",
    "dynamic page",
    "client-side rendering",
    "client side rendering",
}

_CAPTCHA_TERMS = {
    "captcha",
    "recaptcha",
    "hcaptcha",
}

_HEADLESS_TERMS = {
    "headless browser",
    "playwright",
    "puppeteer",
    "selenium",
    "browser automation",
}

_ETHICS_TERMS = {
    "ethical scraping",
    "ethics",
    "legal scraping",
    "legal considerations",
    "terms of service",
    "tos",
    "permission",
    "consent",
    "compliance",
}

_ILLEGAL_INTENT_PATTERNS = [
    r"\bbypass\b.*\b(captcha|recaptcha|hcaptcha|rate limit|block|paywall|login)\b",
    r"\b(captcha|recaptcha|hcaptcha)\b.*\b(bypass|solve automatically|evade|crack|defeat)\b",
    r"\bstealth\b.*\b(scrap|crawl|bot|captcha)\b",
    r"\bavoid detection\b",
    r"\bevade detection\b",
    r"\bhack\b",
    r"\bcredential\b",
    r"\bwithout permission\b",
]

_GENERAL_PROGRAMMING_PATTERNS = [
    r"\bwrite (a )?(python|javascript|java|c\+\+|go|rust|sql)\b",
    r"\bwrite\b.*\b(code|script|function|class|program|scraper|crawler|parser|spider)\b",
    r"\bgenerate\b.*\b(code|script|function|class|program|scraper|crawler|parser|spider)\b",
    r"\bimplement\b.*\b(code|script|function|class|program|scraper|crawler|parser|spider)\b",
    r"\bbuild\b.*\b(code|script|function|class|program|scraper|crawler|parser|spider)\b",
    r"\bcreate\b.*\b(code|script|function|class|program|scraper|crawler|parser|spider)\b",
    r"\bmake\b.*\b(code|script|function|class|program|scraper|crawler|parser|spider)\b",
    r"\bdevelop\b.*\b(code|script|function|class|program|scraper|crawler|parser|spider)\b",
    r"\bshow me\b.*\b(code|script|function|scraper|crawler)\b",
    r"\bprovide\b.*\b(code|script|function|scraper|crawler|parser|spider)\b",
    r"\bgive me\b.*\b(code|script|function|scraper|crawler|parser|spider)\b",
    r"\bcode example\b",
    r"\bexample code\b",
    r"\bsample code\b",
    r"\bcode snippet\b",
    r"\bhow to code\b",
    r"\bhow to program\b",
    r"\bhow to write\b.*\b(scraper|crawler|parser|spider)\b",
    r"\bdebug\b",
    r"\bfix my code\b",
    r"\bapi endpoint\b",
    r"\bsort (an )?array\b",
]

_CASUAL_PATTERNS = [
    r"^\s*(hi|hello|hey|good morning|good evening|thanks|thank you)\s*[!.?]*\s*$",
    r"\bhow are you\b",
    r"\btell me a joke\b",
]

_SENSITIVE_OUT_OF_SCOPE_PATTERNS = [
    r"\bmedical\b",
    r"\bdoctor\b",
    r"\bdiagnos",
    r"\blawyer\b",
    r"\blegal advice\b",
    r"\bpolitic",
    r"\belection\b",
    r"\bpersonal\b",
    r"\brelationship\b",
]


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    reason: str | None = None


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def has_llm_credentials() -> bool:
    return bool(
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )


def get_llm():
    if os.environ.get("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        except ImportError:
            pass
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=key, temperature=0.0)
        except ImportError:
            pass
    return None


class GuardrailOutput(BaseModel):
    allowed: bool = Field(description="Whether the query is strictly within the allowed scope of the agent.")
    reason: str = Field(description="The rejection reason if not allowed. Must be 'Request is outside the agent's allowed scope'. Otherwise leave empty.")


GUARDRAIL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an AI guardrail validator for a web scraping agent.\n"
        "Your task is to determine if the user query is strictly within the allowed scope.\n\n"
        "Allowed Scope (Only These Topics):\n"
        "1. Web scraping concepts\n"
        "2. JavaScript-rendered websites\n"
        "3. CAPTCHA detection and high-level handling strategies (no illegal bypass)\n"
        "4. Headless browsers used for scraping\n"
        "5. Ethical and legal considerations of web scraping\n"
        "Responses must remain high-level and explanatory.\n\n"
        "Out of Scope (Must Be Rejected):\n"
        "1. Any topic unrelated to web scraping\n"
        "2. General programming questions (including writing/generating/implementing/building/creating code, scripts, scrapers, crawlers, or debugging)\n"
        "3. Casual conversation or greetings (like hi, hello, how are you)\n"
        "4. Requests for illegal scraping or CAPTCHA bypass\n"
        "5. Personal, political, medical, or legal questions\n"
        "6. Any request that does not clearly fall within the allowed scope\n\n"
        "Fail closed: if you are unsure or if the request is ambiguous, reject it."
    )),
    ("user", "{query}")
])


def validate_scope_llm(query: str) -> GuardrailDecision:
    llm = get_llm()
    if not llm:
        return GuardrailDecision(True)
    try:
        structured_llm = llm.with_structured_output(GuardrailOutput)
        chain = GUARDRAIL_PROMPT | structured_llm
        result = chain.invoke({"query": query})
        if not result.allowed:
            return GuardrailDecision(False, REJECTION_REASON)
        return GuardrailDecision(True)
    except Exception:
        # Fallback to True since programmatic validation already passed
        return GuardrailDecision(True)


def validate_scope_programmatic(query: str) -> GuardrailDecision:
    text = " ".join(query.lower().split())

    if not text:
        return GuardrailDecision(False, REJECTION_REASON)

    if _matches_any(text, _ILLEGAL_INTENT_PATTERNS):
        return GuardrailDecision(False, REJECTION_REASON)

    if _matches_any(text, _CASUAL_PATTERNS):
        return GuardrailDecision(False, REJECTION_REASON)

    if _matches_any(text, _SENSITIVE_OUT_OF_SCOPE_PATTERNS):
        return GuardrailDecision(False, REJECTION_REASON)

    if _matches_any(text, _GENERAL_PROGRAMMING_PATTERNS):
        return GuardrailDecision(False, REJECTION_REASON)

    allowed = any(
        [
            _contains_any(text, _SCRAPING_TERMS),
            _contains_any(text, _JS_RENDERED_TERMS),
            _contains_any(text, _CAPTCHA_TERMS),
            _contains_any(text, _HEADLESS_TERMS),
            _contains_any(text, _ETHICS_TERMS),
        ]
    )

    if not allowed:
        return GuardrailDecision(False, REJECTION_REASON)

    if _contains_any(text, _CAPTCHA_TERMS):
        high_level_terms = {"detect", "detection", "identify", "handle", "handling", "strategy", "ethical", "legal"}
        if not any(term in text for term in high_level_terms):
            return GuardrailDecision(False, REJECTION_REASON)

    return GuardrailDecision(True)


def validate_scope(query: str) -> GuardrailDecision:
    # 1. Programmatic guardrail check (first line of defense)
    decision = validate_scope_programmatic(query)
    if not decision.allowed:
        return decision

    # 2. Semantic guardrail check via LLM (optional, only runs if API keys are available)
    if has_llm_credentials():
        return validate_scope_llm(query)

    return GuardrailDecision(True)
