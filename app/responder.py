import os
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def _build_answer_fallback(query: str) -> str:
    text = query.lower()

    if "captcha" in text or "recaptcha" in text or "hcaptcha" in text:
        return (
            "CAPTCHAs should be treated as an access-control signal. A compliant scraper should detect their presence, "
            "pause automated collection, reduce request pressure, review permission and terms, and use approved access "
            "paths such as official APIs or human-in-the-loop review. The agent will not provide bypass instructions."
        )

    if "headless" in text or "playwright" in text or "puppeteer" in text or "selenium" in text:
        return (
            "Headless browsers help scraping workflows by loading pages like a real browser, executing JavaScript, "
            "waiting for dynamic content, and exposing the final DOM for extraction. They are useful for JS-heavy sites "
            "but should be used with rate limits, robots.txt awareness, and respect for site terms."
        )

    if "javascript" in text or "js" in text or "dynamic" in text or "spa" in text:
        return (
            "JavaScript-rendered websites often deliver minimal initial HTML and populate content after client-side "
            "scripts run. High-level scraping strategies include checking for official APIs, inspecting network calls, "
            "waiting for stable rendered content, and avoiding excessive automated traffic."
        )

    if "legal" in text or "ethical" in text or "terms" in text or "robots" in text or "permission" in text:
        return (
            "Ethical scraping starts with permission, transparency, and restraint. Review robots.txt, terms of service, "
            "copyright and privacy obligations, avoid personal or sensitive data collection, identify your traffic where "
            "appropriate, and prefer official APIs when available."
        )

    return (
        "Web scraping is the process of collecting information from web pages in a structured way. At a high level, "
        "a responsible workflow identifies permitted sources, retrieves pages carefully, parses relevant public data, "
        "handles errors and rate limits, and documents compliance boundaries."
    )


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
    llm = get_llm()
    if not llm:
        return _build_answer_fallback(query)
    try:
        chain = RESPONDER_PROMPT | llm | StrOutputParser()
        return chain.invoke({"query": query})
    except Exception:
        return _build_answer_fallback(query)


# Fallback to the local generator using a RunnableLambda
response_chain = RunnableLambda(
    lambda inputs: _llm_responder(inputs["query"])
    if isinstance(inputs, dict) and "query" in inputs
    else _llm_responder(inputs)
)


def generate_answer(query: str) -> str:
    return response_chain.invoke(query)
