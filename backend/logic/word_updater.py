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


def process_confusions(results, all_level_data, word_level_map):
    """Detects and records word confusions from a batch of results."""
    changed_files = set()
    incorrect_m2w_items = []
    
    for result in results:
        if result.get('direction') == 'meaningToWord' and result.get('result_type') == 'NO_MATCH':
            incorrect_m2w_items.append(result)

    for incorrect_item in incorrect_m2w_items:
        user_answer = incorrect_item.get('user_answer', '').strip()
        
        # Confusion is between BASE words.
        if user_answer in word_level_map:
            item_key_A = incorrect_item.get('word') # The correct item (e.g., "legen#meletakkan")
            if '#' not in item_key_A: continue
            
            base_word_A = item_key_A.split('#')[0]
            base_word_B = user_answer # The confused word (e.g., "liegen")
            if base_word_A == base_word_B: continue

            level_A = word_level_map.get(base_word_A)
            level_B = word_level_map.get(base_word_B)

            if level_A and level_B:
                # Find any item_key for word_A to update its confusion stats
                # This assumes confusion is tracked on the first meaning's stats, which is a reasonable simplification.
                stats_A = next((s for k, s in all_level_data[level_A].items() if k.startswith(f"{base_word_A}#")), None)
                if stats_A is None:
                    stats_A = all_level_data[level_A].setdefault(item_key_A, data_manager.get_new_repetition_schema())

                confusions_A = stats_A.setdefault('confused_with', {})
                confusions_A[base_word_B] = confusions_A.get(base_word_B, 0) + 1
                
                # Do the same for word_B
                stats_B = next((s for k, s in all_level_data[level_B].items() if k.startswith(f"{base_word_B}#")), None)
                if stats_B is None: # Create stats if rival has never been seen
                    # We need to find a valid item_key for word B to create stats
                    word_B_details = data_manager.load_output_words(level_B).get(base_word_B)
                    if word_B_details:
                         item_key_B = f"{word_B_details[0]['word']}#{word_B_details[0]['meaning']}"
                         stats_B = all_level_data[level_B].setdefault(item_key_B, data_manager.get_new_repetition_schema())
                
                if stats_B:
                    confusions_B = stats_B.setdefault('confused_with', {})
                    confusions_B[base_word_A] = confusions_B.get(base_word_A, 0) + 1
                
                changed_files.add(level_A)
                changed_files.add(level_B)
                
    return all_level_data, changed_files

def process_rival_mastery(results, all_level_data, word_level_map):
    """
    Checks if a known rival pair was answered correctly. If so, resets their
    confusion count to resolve the link. Operates on base words.
    """
    changed_files = set()
    # Map base_word to its result for easy lookup
    base_word_results_map = {r['word'].split('#')[0]: r for r in results if '#' in r['word']}

    for item_key, result in [(r['word'], r) for r in results if '#' in r['word']]:
        base_word_A = item_key.split('#')[0]
        level_A = word_level_map.get(base_word_A)
        if not level_A: continue

        stats_A = next((s for k, s in all_level_data[level_A].items() if k.startswith(f"{base_word_A}#")), None)
        if not stats_A: continue
        
        confusions_A = stats_A.get('confused_with', {})

        for base_word_B, count in list(confusions_A.items()):
            if base_word_B in base_word_results_map:
                result_A = base_word_results_map[base_word_A]
                result_B = base_word_results_map[base_word_B]
                level_B = word_level_map.get(base_word_B)
                if not level_B: continue

                if result_A.get('result_type') == 'PERFECT_MATCH' and \
                   result_B.get('result_type') == 'PERFECT_MATCH':
                    
                    # Reset confusion count for Word A
                    if base_word_B in stats_A['confused_with']:
                        stats_A['confused_with'][base_word_B] = 0

                    # Reset confusion count for Word B
                    stats_B = next((s for k, s in all_level_data[level_B].items() if k.startswith(f"{base_word_B}#")), None)
                    if stats_B and 'confused_with' in stats_B and base_word_A in stats_B['confused_with']:
                        stats_B['confused_with'][base_word_A] = 0

                    print(f"Rivalry mastered between '{base_word_A}' and '{base_word_B}'. Resetting confusion count.")
                    changed_files.add(level_A)
                    changed_files.add(level_B)

    return all_level_data, changed_files

def adjust_schedule_for_forced_word(stats, result, original_next_show_date_str):
    """
    If a word was not due but was forced into a quiz (as a rival) and answered
    correctly, this function adjusts its schedule to prevent it from showing again
    too soon.
    """
    if result.get('result_type') != 'PERFECT_MATCH' or not original_next_show_date_str:
        return stats

    today = datetime.now().date()
    original_next_show_date = datetime.fromisoformat(original_next_show_date_str).date()

    if original_next_show_date > today:
        new_next_show_date = datetime.now() + timedelta(days=1)
        stats['next_show_date'] = new_next_show_date.isoformat()
        print(f"Adjusted schedule for forced word '{result.get('word')}' to tomorrow.")

    return stats