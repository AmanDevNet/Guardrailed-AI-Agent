import os
# pyrefly: ignore [missing-import]
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# =====================================================================
# LOCAL RULE-BASED FALLBACK GENERATOR
# =====================================================================
# This function generates high-level educational explanations when running 
# offline (without LLM API keys). It scans the lowercase query for key concepts 
# and returns predefined responses matching the scope topics.

def _build_answer_fallback(query: str) -> str:
    text = query.lower()

    # Topic 3: CAPTCHAs
    if "captcha" in text or "recaptcha" in text or "hcaptcha" in text:
        return (
            "CAPTCHAs should be treated as an access-control signal. A compliant scraper should detect their presence, "
            "pause automated collection, reduce request pressure, review permission and terms, and use approved access "
            "paths such as official APIs or human-in-the-loop review. The agent will not provide bypass instructions."
        )

    # Topic 4: Headless Browsers
    if "headless" in text or "playwright" in text or "puppeteer" in text or "selenium" in text:
        return (
            "Headless browsers help scraping workflows by loading pages like a real browser, executing JavaScript, "
            "waiting for dynamic content, and exposing the final DOM for extraction. They are useful for JS-heavy sites "
            "but should be used with rate limits, robots.txt awareness, and respect for site terms."
        )

    # Topic 2: JS Rendering / Dynamic Pages
    if "javascript" in text or "js" in text or "dynamic" in text or "spa" in text:
        return (
            "JavaScript-rendered websites often deliver minimal initial HTML and populate content after client-side "
            "scripts run. High-level scraping strategies include checking for official APIs, inspecting network calls, "
            "waiting for stable rendered content, and avoiding excessive automated traffic."
        )

    # Topic 5: Legal and Ethical scraping
    if "legal" in text or "ethical" in text or "terms" in text or "robots" in text or "permission" in text:
        return (
            "Ethical scraping starts with permission, transparency, and restraint. Review robots.txt, terms of service, "
            "copyright and privacy obligations, avoid personal or sensitive data collection, identify your traffic where "
            "appropriate, and prefer official APIs when available."
        )

    # Topic 1: General Web Scraping Concepts (Fallback default)
    return (
        "Web scraping is the process of collecting information from web pages in a structured way. At a high level, "
        "a responsible workflow identifies permitted sources, retrieves pages carefully, parses relevant public data, "
        "handles errors and rate limits, and documents compliance boundaries."
    )


# =====================================================================
# LLM INSTANTIATION LOGIC
# =====================================================================

def has_llm_credentials() -> bool:
    """Detects presence of model provider API keys."""
    return bool(
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )


def get_llm():
    """
    Creates LLM clients. 
    Prefers OpenAI ChatOpenAI (gpt-4o-mini) and falls back to Google's 
    ChatGoogleGenerativeAI (gemini-2.5-flash). Sets temperature to 0.0.
    """
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


# =====================================================================
# ANSWER GENERATION PROMPT (LLM Constraints)
# =====================================================================
# The prompt restricts the LLM to explanatory, high-level answers.
# It explicitly forbids generating code snippets, implementation scripts, 
# or bypass guides. It also enforces plain-text outputs (no Markdown bolding 
# or lists) to ensure the client receives clean, unstyled text.
RESPONDER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a helpful AI assistant specialized in web scraping.\n"
        "You only answer questions about web scraping concepts, JavaScript-rendered websites, "
        "CAPTCHA detection and high-level handling strategies, headless browsers, and ethical/legal considerations.\n"
        "Your answers must remain high-level and explanatory. Do not provide code implementations, script snippets, or bypass instructions.\n"
        "Keep your response strictly plain text. Do not use markdown formatting (such as bolding, lists, headers, or bullet points)."
    )),
    ("user", "{query}")
])


def _llm_responder(query: str) -> str:
    """
    Connects prompt templates with the target LLM and parses the 
    result as plain string. If API errors or import issues occur, 
    falls back to the static keyword templates.
    """
    llm = get_llm()
    if not llm:
        return _build_answer_fallback(query)
    try:
        # LangChain expression: Prompt | Model | Parser
        chain = RESPONDER_PROMPT | llm | StrOutputParser()
        return chain.invoke({"query": query})
    except Exception:
        return _build_answer_fallback(query)


# =====================================================================
# RUNNABLE COMPATIBILITY WRAPPER
# =====================================================================
# We wrap our logic inside a RunnableLambda. This is a LangChain abstraction 
# that converts standard Python functions into runnable chains, making them 
# compatible with other chains, inputs, and LangGraph node executions.
response_chain = RunnableLambda(
    lambda inputs: _llm_responder(inputs["query"])
    if isinstance(inputs, dict) and "query" in inputs
    else _llm_responder(inputs)
)


def generate_answer(query: str) -> str:
    """
    The main interface for generating answers. Invokes our wrapped 
    runnable chain and returns the final string response.
    """
    return response_chain.invoke(query)
