from datetime import datetime

def calculate_recency_score(stats):
    """
    Calculates a score based on how long it has been since the word was last seen.
    """
    last_seen_str = stats.get('last_seen')
    if not last_seen_str:
        return 0

    try:
        days_since = (datetime.now() - datetime.fromisoformat(last_seen_str)).days
        # The score increases by 1 for each day, capped at 10.
        return min(days_since, 10)
    except (ValueError, TypeError):
        return 0