import json
import logging
import config
from models import Article

log = logging.getLogger(__name__)

TOPICS = [
    "Technology", "Science", "Politics", "Business", "Finance",
    "Sports", "Entertainment", "Celebrity", "Health", "Environment",
    "Education", "Crime", "Military", "World", "Local",
    "Opinion", "Culture", "Food", "Travel", "Automotive",
    "Space", "AI", "Crypto", "Gaming", "Media",
]

SYSTEM_PROMPT = f"""You are a news article topic classifier. Given a list of articles (title + summary), assign 1-3 topic labels to each from this fixed set:

{', '.join(TOPICS)}

Respond with a JSON array where each element has "index" (0-based position) and "topics" (array of topic strings). Only use topics from the list above. Be concise and accurate.

Example response:
[{{"index": 0, "topics": ["Technology", "AI"]}}, {{"index": 1, "topics": ["Politics", "World"]}}]"""


def classify_articles(articles: list[Article]) -> dict[int, list[str]]:
    """Classify articles by topic using Claude. Returns {article.id: [topics]}."""
    if not articles:
        return {}

    try:
        import anthropic
    except ImportError:
        log.warning("anthropic package not installed, skipping classification")
        return {}

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    results = {}
    for batch_start in range(0, len(articles), 20):
        batch = articles[batch_start:batch_start + 20]
        batch_results = _classify_batch(client, batch)
        results.update(batch_results)

    return results


def _classify_batch(client, articles: list[Article]) -> dict[int, list[str]]:
    """Classify a single batch of articles."""
    lines = []
    for i, a in enumerate(articles):
        summary_snippet = (a.summary or "")[:200]
        lines.append(f"[{i}] {a.title}\n{summary_snippet}")

    user_msg = "\n\n".join(lines)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )

        text = response.content[0].text.strip()
        # Extract JSON from response (handle markdown code blocks)
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        parsed = json.loads(text)
        results = {}
        valid_topics = set(TOPICS)
        for item in parsed:
            idx = item["index"]
            if 0 <= idx < len(articles):
                topics = [t for t in item["topics"] if t in valid_topics]
                if topics:
                    results[articles[idx].id] = topics
        return results

    except Exception as e:
        log.error(f"Classification failed: {e}")
        return {}


def store_topics(db, topic_map: dict[int, list[str]]):
    """Write classified topics back to the database."""
    if not topic_map:
        return
    mappings = [{"id": aid, "topics": ",".join(topics)} for aid, topics in topic_map.items()]
    db.bulk_update_mappings(Article, mappings)
    db.commit()
    log.info(f"Stored topics for {len(topic_map)} articles")
