def calculate_volatility_score(stats):
    """
    Calculates a score based on how often the user's answers flip
    between right and wrong in recent history. High volatility indicates instability.
    """
    history = stats.get('recent_history', [])
    if len(history) <= 3:
        return 0

    flips = 0
    for i in range(len(history) - 1):
        if history[i] != history[i+1]:
            flips += 1
            
    # Each flip adds 7 to the priority, capped at 35
    return min(flips * 7, 35)