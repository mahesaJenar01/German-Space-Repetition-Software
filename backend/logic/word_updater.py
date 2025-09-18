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
    
    # Find all incorrect meaning-to-word questions
    for result in results:
        if result.get('direction') == 'meaningToWord' and result.get('result_type') == 'NO_MATCH':
            incorrect_m2w_items.append(result)

    for incorrect_item in incorrect_m2w_items:
        user_answer = incorrect_item.get('user_answer', '').strip()
        
        # --- THIS IS THE FIX ---
        # Check if the user's answer is ANY valid word in our entire vocabulary,
        # not just a word from the current quiz batch.
        if user_answer in word_level_map:
            word_A = incorrect_item.get('word') # The correct word (e.g., "legen")
            word_B = user_answer               # The confused word (e.g., "liegen")
            if word_A == word_B: continue

            level_A = word_level_map.get(word_A)
            level_B = word_level_map.get(word_B)

            if level_A and level_B:
                # Update stats for word A
                stats_A = all_level_data[level_A].setdefault(word_A, data_manager.get_new_repetition_schema())
                confusions_A = stats_A.setdefault('confused_with', {})
                confusions_A[word_B] = confusions_A.get(word_B, 0) + 1
                
                # Update stats for word B
                stats_B = all_level_data[level_B].setdefault(word_B, data_manager.get_new_repetition_schema())
                confusions_B = stats_B.setdefault('confused_with', {})
                confusions_B[word_A] = confusions_B.get(word_A, 0) + 1
                
                changed_files.add(level_A)
                changed_files.add(level_B)
                
    return all_level_data, changed_files

# --- NEW FUNCTION FOR RIVAL MASTERY ---
def process_rival_mastery(results, all_level_data, word_level_map):
    """
    Checks if a known rival pair was answered correctly. If so, resets their
    confusion count to resolve the link.
    """
    changed_files = set()
    results_map = {r['word']: r for r in results}

    for result in results:
        word_A_key = result.get('word')
        word_A_level = word_level_map.get(word_A_key)
        if not word_A_level: continue

        stats_A = all_level_data[word_A_level].get(word_A_key, {})
        confusions_A = stats_A.get('confused_with', {})

        # Iterate through known confusions for this word
        for word_B_key, count in confusions_A.items():
            # Check if the rival word was also in this quiz
            if word_B_key in results_map:
                result_A = results_map[word_A_key]
                result_B = results_map[word_B_key]
                word_B_level = word_level_map.get(word_B_key)
                if not word_B_level: continue

                # Check for mastery: both must be a perfect match
                if result_A.get('result_type') == 'PERFECT_MATCH' and \
                   result_B.get('result_type') == 'PERFECT_MATCH':
                    
                    # Reset the confusion count for both words
                    stats_A['confused_with'][word_B_key] = 0
                    
                    stats_B = all_level_data[word_B_level].get(word_B_key, {})
                    if 'confused_with' in stats_B:
                        stats_B['confused_with'][word_A_key] = 0

                    print(f"Rivalry mastered between '{word_A_key}' and '{word_B_key}'. Resetting confusion count.")
                    changed_files.add(word_A_level)
                    changed_files.add(word_B_level)

    return all_level_data, changed_files

def adjust_schedule_for_forced_word(stats, result, original_next_show_date_str):
    """
    If a word was not due but was forced into a quiz (as a rival) and answered
    correctly, this function adjusts its schedule to prevent it from showing again
    too soon.
    """
    if result.get('result_type') != 'PERFECT_MATCH' or not original_next_show_date_str:
        return stats # Only act on perfect matches for words that had a schedule

    today = datetime.now().date()
    original_next_show_date = datetime.fromisoformat(original_next_show_date_str).date()

    # Check if the word was answered correctly *before* it was due
    if original_next_show_date > today:
        # The user mastered a forced, not-due word.
        # Instead of letting the normal logic push its date far into the future,
        # we'll just push it by one day from today as a small reward.
        new_next_show_date = datetime.now() + timedelta(days=1)
        stats['next_show_date'] = new_next_show_date.isoformat()
        print(f"Adjusted schedule for forced word '{result.get('word')}' to tomorrow.")

    return stats