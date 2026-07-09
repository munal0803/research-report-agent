"""Web search and page-fetching tools used by the research agent."""

from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

USER_AGENT = "Mozilla/5.0 (compatible; research-report-agent/0.1; +https://github.com)"
REQUEST_TIMEOUT = 10
MAX_CHARS_PER_SOURCE = 6000


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Run a web search and return a list of {title, url, snippet} dicts."""
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)
    return [
        {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
        for r in results
        if r.get("href")
    ]


def fetch_and_clean(url: str) -> str | None:
    """Fetch a URL and return its main text content, or None if it can't be read."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    content_type = resp.headers.get("Content-Type", "")
    if "html" not in content_type:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_CHARS_PER_SOURCE] if text else None
