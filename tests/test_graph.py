from unittest.mock import MagicMock, patch

from agent.graph import (
    MAX_ITERATIONS,
    critique,
    plan_search,
    route_after_critique,
    scrape,
    search,
    synthesize,
)


def _mock_model_response(text: str) -> MagicMock:
    response = MagicMock()
    response.content = text
    model = MagicMock()
    model.invoke.return_value = response
    return model


def test_plan_search_parses_queries_from_model_output():
    state = {"topic": "quantum computing", "refinement": ""}
    with patch("agent.graph._get_model") as mock_get_model:
        mock_get_model.return_value = _mock_model_response(
            "- query one\n- query two\nquery three"
        )
        result = plan_search(state)

    assert result["queries"] == ["query one", "query two", "query three"]


def test_search_deduplicates_against_existing_sources():
    state = {
        "queries": ["q1"],
        "sources": [{"title": "old", "url": "https://old.example", "text": "..."}],
    }
    fake_results = [
        {"title": "old", "url": "https://old.example", "snippet": ""},
        {"title": "new", "url": "https://new.example", "snippet": ""},
    ]
    with patch("agent.graph.web_search", return_value=fake_results):
        result = search(state)

    assert result["pending_urls"] == [{"title": "new", "url": "https://new.example", "snippet": ""}]


def test_scrape_appends_only_successfully_fetched_sources():
    state = {
        "sources": [],
        "pending_urls": [
            {"title": "ok", "url": "https://ok.example", "snippet": ""},
            {"title": "fail", "url": "https://fail.example", "snippet": ""},
        ],
    }

    def fake_fetch(url):
        return "fetched text" if url == "https://ok.example" else None

    with patch("agent.graph.fetch_and_clean", side_effect=fake_fetch):
        result = scrape(state)

    assert result["sources"] == [{"title": "ok", "url": "https://ok.example", "text": "fetched text"}]


def test_synthesize_builds_draft_from_model():
    state = {
        "topic": "quantum computing",
        "sources": [{"title": "Src", "url": "https://s.example", "text": "some facts"}],
    }
    with patch("agent.graph._get_model") as mock_get_model:
        mock_get_model.return_value = _mock_model_response("# Report\n...")
        result = synthesize(state)

    assert result["draft"] == "# Report\n..."


def test_critique_stops_at_max_iterations_without_calling_model():
    state = {"topic": "t", "draft": "d", "iteration": MAX_ITERATIONS - 1}
    with patch("agent.graph._get_model") as mock_get_model:
        result = critique(state)

    mock_get_model.assert_not_called()
    assert result == {"done": True, "iteration": MAX_ITERATIONS}


def test_critique_parses_done_response():
    state = {"topic": "t", "draft": "d", "iteration": 0}
    with patch("agent.graph._get_model") as mock_get_model:
        mock_get_model.return_value = _mock_model_response("DONE")
        result = critique(state)

    assert result == {"done": True, "iteration": 1}


def test_critique_parses_continue_response_with_refinement():
    state = {"topic": "t", "draft": "d", "iteration": 0}
    with patch("agent.graph._get_model") as mock_get_model:
        mock_get_model.return_value = _mock_model_response("CONTINUE: missing recent data")
        result = critique(state)

    assert result == {"done": False, "refinement": "missing recent data", "iteration": 1}


def test_route_after_critique():
    assert route_after_critique({"done": True}) == "done"
    assert route_after_critique({"done": False}) == "continue"
