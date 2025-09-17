def calculate_accuracy_score(stats):
    """
    Calculates a score based on general accuracy and number of mistakes.
    A higher score means higher priority (i.e., the word is problematic).
    """
    right = stats.get('right', 0)
    wrong = stats.get('wrong', 0)
    total = stats.get('total_encountered', 0)
    
    if total == 0:
        return 100 # Highest priority for new words

    # Weight based on inverse accuracy
    accuracy = right / total
    accuracy_weight = (1 - accuracy) * 50
    
    # Weight based on the raw number of mistakes
    mistake_weight = min(wrong * 5, 40)
    
    return accuracy_weight + mistake_weight