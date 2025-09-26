from datetime import datetime, timedelta
import data_manager

HISTORY_MAX_LENGTH = 10
HARD_WORD_THRESHOLD = 3

def _update_stickiness_score(stats, is_correct):
    """Updates metrics related to "sticky correction"."""
    last_attempt_was_wrong = stats.get('last_result_was_wrong', False)
    if last_attempt_was_wrong and is_correct:
        stats['successful_corrections'] = stats.get('successful_corrections', 0) + 1
    stats['last_result_was_wrong'] = not is_correct
    return stats

def _update_scheduling(stats, is_correct, is_partial, daily_wrong_count):
    """Handles the spaced repetition scheduling logic."""
    today = datetime.now()
    if is_correct:
        stats['right'] += 1
        stats['consecutive_correct'] += 1
        stats['last_correct'] = today.isoformat()
        stats['article_wrong'] = 0 
        
        if stats['consecutive_correct'] >= 3:
            stats['streak_level'] += 1
            new_delay = stats['current_delay_days'] + stats['streak_level']
            stats['current_delay_days'] = new_delay
            stats['next_show_date'] = (today + timedelta(days=new_delay)).isoformat()
            stats['consecutive_correct'] = 0
    
    elif is_partial:
        stats['article_wrong'] += 1
    
    else: # Incorrect (NO_MATCH)
        stats['wrong'] += 1
        stats['consecutive_correct'] = 0
        stats['streak_level'] = 0

        if daily_wrong_count >= HARD_WORD_THRESHOLD - 1:
            stats['wrong'] += 2
            stats['current_delay_days'] = 1
            stats['next_show_date'] = (today + timedelta(days=1)).isoformat()
        else:
            new_delay = max(0, stats['current_delay_days'] - stats['streak_level'])
            stats['current_delay_days'] = new_delay
            stats['next_show_date'] = (today + timedelta(days=new_delay)).isoformat()
    return stats


def process_quiz_result(stats, result, daily_wrong_count):
    """
    Updates a single item's stats based on a quiz result.
    This is a pure function: it receives state and returns new state.
    """
    result_type = result.get('result_type')
    is_correct = result_type == "PERFECT_MATCH"
    is_partial = "PARTIAL_MATCH" in result_type

    stats['total_encountered'] += 1
    stats['last_seen'] = datetime.now().isoformat()
    if stats.get('total_encountered') == 1 and not is_correct:
        stats['failed_first_encounter'] = True

    history = stats.setdefault('recent_history', [])
    history.append(1 if is_correct else 0)
    if len(history) > HISTORY_MAX_LENGTH:
        stats['recent_history'] = history[-HISTORY_MAX_LENGTH:]
    
    stats = _update_stickiness_score(stats, is_correct)
    stats = _update_scheduling(stats, is_correct, is_partial, daily_wrong_count)

    return stats