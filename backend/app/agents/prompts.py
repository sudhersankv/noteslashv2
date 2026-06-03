"""Shared LLM prompts."""

CATEGORIZE_SYSTEM = """You classify uploaded audio/text content for a personal knowledge library.
Return valid JSON only."""

CATEGORIZE_USER_TEMPLATE = """Classify this content.

Filename: {filename}
Text sample:
{text}

Return JSON:
{{
  "content_type": "podcast|interview|audiobook|lecture|other",
  "title_guess": "short title",
  "tags": ["tag1", "tag2"],
  "summary": "one sentence summary"
}}"""

RESEARCH_INTERVIEW_SYSTEM = """You analyze interview transcripts. Extract themes, pain points, and feature requests.
Every item MUST cite real chunk_ids from the provided context. Return valid JSON only."""

RESEARCH_INTERVIEW_USER = """Analyze these chunks and extract insights.

Chunks (JSON):
{chunks_json}

Return JSON:
{{
  "summary": "2-3 sentence summary",
  "themes": [{{"title": "...", "description": "...", "frequency": 3, "confidence": 0.9, "chunk_ids": ["uuid"]}}],
  "pain_points": [{{"title": "...", "description": "...", "frequency": 2, "confidence": 0.85, "chunk_ids": []}}],
  "feature_requests": [{{"title": "...", "description": "...", "frequency": 1, "confidence": 0.8, "chunk_ids": []}}]
}}
Rules: 3-6 items per category max; chunk_ids must be from input only."""

RESEARCH_GENERAL_SYSTEM = """You analyze audio/text library content (podcasts, audiobooks, lectures).
Extract key topics, notable quotes, and takeaways. Every item MUST cite real chunk_ids. Return valid JSON only."""

RESEARCH_GENERAL_USER = """Analyze these content chunks.

Chunks (JSON):
{chunks_json}

Return JSON:
{{
  "summary": "2-3 sentence summary",
  "themes": [{{"title": "key topic", "description": "...", "frequency": 3, "confidence": 0.9, "chunk_ids": []}}],
  "pain_points": [{{"title": "notable quote or insight", "description": "...", "frequency": 1, "confidence": 0.85, "chunk_ids": []}}],
  "feature_requests": [{{"title": "takeaway or action item", "description": "...", "frequency": 1, "confidence": 0.8, "chunk_ids": []}}]
}}
Map: themes=key topics, pain_points=notable quotes, feature_requests=takeaways. 3-6 per category max."""

SEARCH_SYSTEM = """You answer questions about library content using ONLY the provided quotes.
If insufficient evidence, say so. Return valid JSON only."""

SEARCH_USER_TEMPLATE = """Question: {query}

Quotes (cite by chunk_id):
{quotes_json}

Return JSON:
{{"answer": "2-4 sentences", "cited_chunk_ids": ["uuid"]}}"""

CHAT_SYSTEM = """You are Noteslash, a helpful assistant for the user's audio/text library.
Use provided quotes and conversation history. Cite sources via chunk_ids. Return valid JSON only."""

CHAT_USER_TEMPLATE = """Conversation:
{history}

New message: {message}

Relevant quotes:
{quotes_json}

Return JSON:
{{"answer": "helpful reply", "cited_chunk_ids": ["uuid"]}}"""

REPORT_SYSTEM = """You write clear markdown summaries from indexed library content."""

REPORT_USER_TEMPLATE = """Write a markdown report for library: {project_name}
Content type: {content_type}
Summary: {summary}

Key topics:
{themes_text}

Notable points:
{pains_text}

Takeaways:
{features_text}

Sample quotes:
{quotes_text}

Sections: # Summary, # Key Topics, # Notable Quotes, # Takeaways, # Open Questions
Under 800 words."""

EVAL_JUDGE_SYSTEM = """Verify if an insight is supported by a quote. JSON: {{"supported": true/false, "reason": "..."}}"""

EVAL_JUDGE_USER_TEMPLATE = """Insight: {title}
Description: {description}
Quote: {quote}
Supported?"""

# Legacy aliases
RESEARCH_SYSTEM = RESEARCH_INTERVIEW_SYSTEM
RESEARCH_USER_TEMPLATE = RESEARCH_INTERVIEW_USER
