"""Prompt templates for each stage of the research loop."""

PLAN_SEARCH_PROMPT = """You are a research planner. Given a topic, produce {n} distinct, \
specific web search queries that together would surface a well-rounded set of sources on it.

Topic: {topic}

{refinement}

Return ONLY the queries, one per line, no numbering or extra text."""

SYNTHESIZE_PROMPT = """You are a research analyst. Write a well-organized markdown report on \
the topic below, using ONLY the information in the provided sources. Cite sources inline using \
[1], [2], etc. matching the numbered source list. Do not fabricate facts not present in the \
sources.

Topic: {topic}

Sources:
{sources_block}

Write the report now. Structure it with a short intro, 2-4 thematic sections with headers, and \
a "Sources" section at the end listing each numbered source's title and URL."""

CRITIQUE_PROMPT = """You are a critical editor reviewing a research report for gaps.

Topic: {topic}

Report:
{draft}

Does this report have significant gaps, unanswered angles, or rely on too few sources to be \
considered thorough? Respond with a single line:
- "DONE" if the report is thorough and well-supported, OR
- "CONTINUE: <one short sentence on what's missing>" if it needs another research pass.
"""
