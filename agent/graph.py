"""LangGraph state machine for the research agent.

The loop: plan search queries -> search -> scrape sources -> synthesize a
draft report -> critique the draft -> either loop back to planning with a
refinement note, or finish.
"""

from __future__ import annotations

from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, StateGraph

from agent.prompts import CRITIQUE_PROMPT, PLAN_SEARCH_PROMPT, SYNTHESIZE_PROMPT
from agent.tools import fetch_and_clean, web_search

QUERIES_PER_ROUND = 4
RESULTS_PER_QUERY = 3
MAX_ITERATIONS = 2


class Source(TypedDict):
    title: str
    url: str
    text: str


class AgentState(TypedDict):
    topic: str
    refinement: str
    queries: list[str]
    pending_urls: list[dict]
    sources: list[Source]
    draft: str
    iteration: int
    done: bool


def _get_model() -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-4-5", temperature=0)


def plan_search(state: AgentState) -> dict:
    model = _get_model()
    prompt = PLAN_SEARCH_PROMPT.format(
        n=QUERIES_PER_ROUND,
        topic=state["topic"],
        refinement=f"Focus this round on: {state['refinement']}" if state["refinement"] else "",
    )
    response = model.invoke(prompt)
    queries = [q.strip("- ").strip() for q in response.content.strip().splitlines() if q.strip()]
    return {"queries": queries}


def search(state: AgentState) -> dict:
    seen_urls = {s["url"] for s in state["sources"]}
    new_urls: list[dict] = []
    for query in state["queries"]:
        for result in web_search(query, max_results=RESULTS_PER_QUERY):
            if result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                new_urls.append(result)
    return {"pending_urls": new_urls}


def scrape(state: AgentState) -> dict:
    pending = state.get("pending_urls", [])
    new_sources: list[Source] = list(state["sources"])
    for result in pending:
        text = fetch_and_clean(result["url"])
        if text:
            new_sources.append({"title": result["title"], "url": result["url"], "text": text})
    return {"sources": new_sources}


def synthesize(state: AgentState) -> dict:
    model = _get_model()
    sources_block = "\n\n".join(
        f"[{i + 1}] {s['title']} ({s['url']})\n{s['text'][:3000]}"
        for i, s in enumerate(state["sources"])
    )
    prompt = SYNTHESIZE_PROMPT.format(topic=state["topic"], sources_block=sources_block)
    response = model.invoke(prompt)
    return {"draft": response.content}


def critique(state: AgentState) -> dict:
    if state["iteration"] + 1 >= MAX_ITERATIONS:
        return {"done": True, "iteration": state["iteration"] + 1}

    model = _get_model()
    prompt = CRITIQUE_PROMPT.format(topic=state["topic"], draft=state["draft"])
    response = model.invoke(prompt).content.strip()

    if response.upper().startswith("DONE"):
        return {"done": True, "iteration": state["iteration"] + 1}

    refinement = response.split(":", 1)[1].strip() if ":" in response else response
    return {"done": False, "refinement": refinement, "iteration": state["iteration"] + 1}


def route_after_critique(state: AgentState) -> str:
    return "done" if state["done"] else "continue"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("plan_search", plan_search)
    graph.add_node("search", search)
    graph.add_node("scrape", scrape)
    graph.add_node("synthesize", synthesize)
    graph.add_node("critique", critique)

    graph.set_entry_point("plan_search")
    graph.add_edge("plan_search", "search")
    graph.add_edge("search", "scrape")
    graph.add_edge("scrape", "synthesize")
    graph.add_edge("synthesize", "critique")
    graph.add_conditional_edges(
        "critique", route_after_critique, {"continue": "plan_search", "done": END}
    )

    return graph.compile()


def run_research(topic: str) -> str:
    app = build_graph()
    initial_state: AgentState = {
        "topic": topic,
        "refinement": "",
        "queries": [],
        "pending_urls": [],
        "sources": [],
        "draft": "",
        "iteration": 0,
        "done": False,
    }
    final_state = app.invoke(initial_state)
    return final_state["draft"]
