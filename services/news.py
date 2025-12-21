async def fetch_news_digest(entities):
    if not entities:
        return "No recent entities detected."

    return f"Recent news summary for: {', '.join(entities)}"
