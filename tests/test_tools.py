from unittest.mock import MagicMock, patch

import requests

from agent.tools import fetch_and_clean, web_search


def test_web_search_maps_ddgs_results():
    fake_results = [
        {"title": "A", "href": "https://a.example", "body": "snippet a"},
        {"title": "B", "href": "https://b.example", "body": "snippet b"},
        {"title": "no url", "body": "should be dropped"},
    ]
    with patch("agent.tools.DDGS") as mock_ddgs_cls:
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__.return_value = mock_ddgs
        mock_ddgs.text.return_value = fake_results
        mock_ddgs_cls.return_value = mock_ddgs

        results = web_search("test query", max_results=3)

    assert results == [
        {"title": "A", "url": "https://a.example", "snippet": "snippet a"},
        {"title": "B", "url": "https://b.example", "snippet": "snippet b"},
    ]


def test_fetch_and_clean_strips_boilerplate():
    html = """
    <html><body>
      <nav>navigation</nav>
      <p>Real   content   here.</p>
      <script>console.log("ignore me")</script>
    </body></html>
    """
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.text = html
    mock_resp.raise_for_status.return_value = None

    with patch("agent.tools.requests.get", return_value=mock_resp):
        text = fetch_and_clean("https://example.com")

    assert text is not None
    assert "Real content here." in text
    assert "navigation" not in text
    assert "ignore me" not in text


def test_fetch_and_clean_returns_none_on_request_error():
    with patch("agent.tools.requests.get", side_effect=requests.RequestException("boom")):
        assert fetch_and_clean("https://example.com") is None


def test_fetch_and_clean_skips_non_html():
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_resp.raise_for_status.return_value = None

    with patch("agent.tools.requests.get", return_value=mock_resp):
        assert fetch_and_clean("https://example.com/file.pdf") is None
