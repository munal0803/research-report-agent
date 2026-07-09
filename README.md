# research-report-agent

An agentic research assistant. Give it a topic; it plans search queries, searches the web,
reads the sources, drafts a cited report, critiques its own draft, and — if the draft has
real gaps — loops back to research further before finishing.

```
$ research-agent "the current state of solid-state batteries" -o report.md
Researching: the current state of solid-state batteries
Report written to report.md
```

See [examples/sample_report.md](examples/sample_report.md) for sample output.

## Why this exists

Most "agent" demos are a single LLM call with a tool bolted on. This one has an actual
decision loop: after drafting, a critique step decides whether the report is thorough enough
or whether to go back and research a specific gap, bounded to a couple of rounds so it can't
loop forever. That loop — plan → act → reflect → repeat-or-stop — is the core pattern most
useful task-automation agents are built on.

## How it works

```
plan_search -> search -> scrape -> synthesize -> critique --done--> END
                  ^                                  |
                  |________________continue___________|
```

- **plan_search** — the LLM turns the topic (plus any refinement note from a prior critique)
  into a handful of specific search queries.
- **search** — runs each query against DuckDuckGo (no API key required), dedupes against
  sources already collected.
- **scrape** — fetches each new result and strips it down to clean body text.
- **synthesize** — the LLM writes a structured markdown report, citing sources by number.
- **critique** — the LLM reviews its own draft and returns either `DONE` or
  `CONTINUE: <what's missing>`. On continue, that note flows back into the next `plan_search`
  call. Capped at `MAX_ITERATIONS` (default 2) so it always terminates.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) for the state machine and
[Claude](https://www.anthropic.com) as the model.

## Setup

```bash
git clone <this-repo-url>
cd research-report-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # add your ANTHROPIC_API_KEY
```

## Usage

```bash
research-agent "your topic here"
research-agent "your topic here" -o custom-name.md
```

## Tests

```bash
pytest
```

Every node in the graph is unit-tested in isolation (model and network calls mocked) — see
[tests/](tests/).

## Project layout

```
agent/
  graph.py     LangGraph state machine and node functions
  tools.py     web_search / fetch_and_clean
  prompts.py   prompt templates
  cli.py       CLI entrypoint
tests/         unit tests per node/tool
examples/      sample report output
```

## License

MIT
