def calculate_confusion_score(stats):
    """
    Boosts priority for words that are frequently confused with others.
    A higher score means the word needs more attention.
    """
    confusions = stats.get('confused_with', {})
    if not confusions:
        return 0
    
    # Add 5 points for each unique word this word is confused with.
    # This rewards the system for identifying multiple points of confusion.
    # We cap the score at 20 to prevent it from overpowering other metrics.
    score = len(confusions.keys()) * 5
    
    return min(score, 20)