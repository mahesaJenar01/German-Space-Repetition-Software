from datetime import datetime, timedelta
import data_manager

# Configuration
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
        stats['consecutive_correct'] += 1
        stats['last_correct'] = today.isoformat()
        # Reset article-specific error counter on a perfect match
        stats['article_wrong'] = 0 
        
        # If user reaches a streak, advance the scheduling level
        if stats['consecutive_correct'] >= 3:
            stats['streak_level'] += 1
            new_delay = stats['current_delay_days'] + stats['streak_level']
            stats['current_delay_days'] = new_delay
            stats['next_show_date'] = (today + timedelta(days=new_delay)).isoformat()
            stats['consecutive_correct'] = 0 # Reset for the next streak
    
    elif is_partial:
        # For partial matches (e.g., wrong article), we don't advance but don't severely punish.
        stats['article_wrong'] += 1
    
    else: # Incorrect (NO_MATCH)
        stats['wrong'] += 1
        stats['consecutive_correct'] = 0
        stats['streak_level'] = 0

        # If it's a "hard" word, punish more severely
        if daily_wrong_count >= HARD_WORD_THRESHOLD:
            stats['wrong'] += 2  # Extra penalty
            stats['current_delay_days'] = 1 # Force it to show up tomorrow
            stats['next_show_date'] = (today + timedelta(days=1)).isoformat()
        else:
            # Regress the delay
            new_delay = max(0, stats['current_delay_days'] - stats['streak_level'])
            stats['current_delay_days'] = new_delay
            stats['next_show_date'] = (today + timedelta(days=new_delay)).isoformat()
    return stats


def process_quiz_result(stats, result, daily_wrong_count):
    """
    Updates a single word's stats based on a quiz result.
    This is a pure function: it receives state and returns new state.
    """
    result_type = result.get('result_type')
    is_correct = result_type == "PERFECT_MATCH"
    is_partial = "PARTIAL_MATCH" in result_type

    # Update base stats
    stats['total_encountered'] += 1
    stats['last_seen'] = datetime.now().isoformat()
    if stats.get('total_encountered') == 1 and not is_correct:
        stats['failed_first_encounter'] = True

    # Update history
    history = stats.setdefault('recent_history', [])
    history.append(1 if is_correct else 0)
    if len(history) > HISTORY_MAX_LENGTH:
        stats['recent_history'] = history[-HISTORY_MAX_LENGTH:]
    
    stats = _update_stickiness_score(stats, is_correct)
    stats = _update_scheduling(stats, is_correct, is_partial, daily_wrong_count)

    return stats


def process_confusions(results, all_level_data, word_level_map):
    """Detects and records word confusions from a batch of results."""
    changed_files = set()
    incorrect_m2w_items = []
    correct_m2w_word_map = {}
    
    for result in results:
        if result.get('direction') == 'meaningToWord':
            correct_word = result.get('word')
            correct_m2w_word_map[correct_word] = result
            if result.get('result_type') == 'NO_MATCH':
                incorrect_m2w_items.append(result)

    for incorrect_item in incorrect_m2w_items:
        user_answer = incorrect_item.get('user_answer', '').strip()
        if user_answer in correct_m2w_word_map:
            word_A = incorrect_item.get('word')
            word_B = user_answer
            if word_A == word_B: continue

            level_A = word_level_map.get(word_A)
            level_B = word_level_map.get(word_B)

            if level_A and level_B:
                stats_A = all_level_data[level_A].setdefault(word_A, data_manager.REPETITION_SCHEMA.copy())
                confusions_A = stats_A.setdefault('confused_with', {})
                confusions_A[word_B] = confusions_A.get(word_B, 0) + 1
                
                stats_B = all_level_data[level_B].setdefault(word_B, data_manager.REPETITION_SCHEMA.copy())
                confusions_B = stats_B.setdefault('confused_with', {})
                confusions_B[word_A] = confusions_B.get(word_A, 0) + 1
                
                changed_files.add(level_A)
                changed_files.add(level_B)
                
    return all_level_data, changed_files