def calculate_article_weakness_score(stats, word_details):
    """
    Adds a priority score if the user consistently gets the article wrong for a noun.
    """
    if word_details.get('type') != 'Nomen':
        return 0

    article_errors = stats.get('article_wrong', 0)
    noun_errors = stats.get('wrong', 0) # Non-article related errors for this noun
    total_errors = article_errors + noun_errors
    
    # Only apply this penalty if there's a history of errors
    if total_errors > 0:
        # If more than 60% of errors are article-related, it's a specific weakness.
        article_error_ratio = article_errors / total_errors
        if article_error_ratio > 0.6:
            return 20 # Add a significant boost to the priority
            
    return 0