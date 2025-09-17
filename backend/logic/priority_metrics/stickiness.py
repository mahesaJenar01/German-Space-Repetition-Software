def calculate_stickiness_score(stats):
    """
    Calculates a "stickiness" score. A high score means the user struggles
    to correct their mistakes for this word (the correction isn't "sticking").
    """
    total_mistakes = stats.get('wrong', 0) + stats.get('article_wrong', 0)
    
    # This metric is only meaningful if the user has made several mistakes.
    if total_mistakes <= 2:
        return 0

    successful_fixes = stats.get('successful_corrections', 0)
    
    # Calculate the rate of successful correction following a mistake.
    # We multiply by 2 to scale the 0-0.5 range to 0-1 for the calculation.
    sticky_rate = successful_fixes / total_mistakes
    
    # If the rate of successfully correcting a mistake is low, the word is "stubborn".
    # Give it a higher priority score.
    if sticky_rate < 0.5:
        # A 0% sticky rate gets a full 30-point boost.
        # A 40% sticky rate gets a (1 - 0.8) * 30 = 6-point boost.
        return (1 - (sticky_rate * 2)) * 30
        
    return 0