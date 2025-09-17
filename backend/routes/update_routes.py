from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import data_manager
import report_manager
from cache import get_word_to_level_map, get_word_details_map

update_bp = Blueprint('update_bp', __name__)
HARD_WORD_THRESHOLD = 3 
HISTORY_MAX_LENGTH = 10 

@update_bp.route('/api/update', methods=['POST'])
def update_words():
    data = request.json
    results = data.get('results', [])
    level = data.get('level')
    
    if not level or (level != "mix" and level not in data_manager.LEVELS):
        return jsonify({"error": "Invalid or missing level"}), 400
    
    all_level_data = {lvl: data_manager.load_repetition_stats(lvl) for lvl in data_manager.LEVELS}

    changed_files = set()
    today = datetime.now()
    report_data = report_manager.load_report_data()
    today_str = today.strftime('%Y-%m-%d')
    word_level_map = get_word_to_level_map()
    word_details_map = get_word_details_map()

    daily_seen = report_data.setdefault('daily_seen_words', {}).setdefault(today_str, {})
    daily_wrong_per_word = report_data.setdefault('daily_wrong_counts', {}).setdefault(today_str, {})
    daily_level_correct = report_data.setdefault('daily_level_correct_counts', {}).setdefault(today_str, {lvl: 0 for lvl in data_manager.LEVELS})
    daily_level_wrong = report_data.setdefault('daily_level_wrong_counts', {}).setdefault(today_str, {lvl: 0 for lvl in data_manager.LEVELS})
    word_learned_counts = report_data.setdefault('word_learned', {})
    category_performance = report_data.setdefault('category_performance', {})

    # ... (Confusion detection logic is unchanged) ...
    incorrect_m2w_items = []
    correct_m2w_word_map = {}
    for result in results:
        if result.get('direction') == 'meaningToWord':
            correct_word = result.get('word')
            correct_m2w_word_map[correct_word] = result
            if result.get('result_type') == 'NO_MATCH': incorrect_m2w_items.append(result)
    for incorrect_item in incorrect_m2w_items:
        user_answer = incorrect_item.get('user_answer', '').strip()
        if user_answer in correct_m2w_word_map:
            word_A = incorrect_item.get('word'); word_B = user_answer
            if word_A == word_B: continue
            level_A = word_level_map.get(word_A); level_B = word_level_map.get(word_B)
            if level_A and level_B:
                stats_A = all_level_data[level_A].setdefault(word_A, data_manager.REPETITION_SCHEMA.copy())
                confusions_A = stats_A.setdefault('confused_with', {}); confusions_A[word_B] = confusions_A.get(word_B, 0) + 1
                stats_B = all_level_data[level_B].setdefault(word_B, data_manager.REPETITION_SCHEMA.copy())
                confusions_B = stats_B.setdefault('confused_with', {}); confusions_B[word_A] = confusions_B.get(word_A, 0) + 1
                changed_files.add(level_A); changed_files.add(level_B)

    for result in results:
        word_to_update = result.get('word')
        result_type = result.get('result_type')
        
        word_lvl = word_level_map.get(word_to_update)
        word_details = word_details_map.get(word_to_update)

        if not word_lvl or not word_details:
            print(f"WARNING: Could not find metadata for word '{word_to_update}'. Skipping update.")
            continue

        repetition_data_for_level = all_level_data[word_lvl]
        stats = repetition_data_for_level.setdefault(word_to_update, data_manager.REPETITION_SCHEMA.copy())
        
        is_correct = result_type == "PERFECT_MATCH"

        # --- NEW: "Unintuitive Word" Flag Logic ---
        # This check runs ONLY on the very first encounter with a word.
        if stats.get('total_encountered', 0) == 0:
            # If the first attempt is anything other than perfect, flag it permanently.
            if not is_correct:
                stats['failed_first_encounter'] = True
        # --- END OF NEW LOGIC ---

        word_type = word_details.get('type')
        if word_type:
            type_stats = category_performance.setdefault(word_type, {'right': 0, 'wrong': 0})
            if is_correct: type_stats['right'] += 1
            else: type_stats['wrong'] += 1

        history = stats.setdefault('recent_history', [])
        history.append(1 if is_correct else 0)
        if len(history) > HISTORY_MAX_LENGTH: stats['recent_history'] = history[-HISTORY_MAX_LENGTH:]
        
        seen_today_for_level = daily_seen.setdefault(word_lvl, [])
        if word_to_update not in seen_today_for_level: seen_today_for_level.append(word_to_update)
        
        # This counter must be incremented AFTER the first-encounter check.
        stats['total_encountered'] += 1
        stats['last_seen'] = today.isoformat()

        if is_correct:
            stats['right'] += 1; daily_level_correct[word_lvl] += 1; stats['last_correct'] = today.isoformat()
            stats['consecutive_correct'] += 1; stats['article_wrong'] = 0
            if stats['consecutive_correct'] >= 3:
                stats['streak_level'] += 1; new_delay = stats['current_delay_days'] + stats['streak_level']
                stats['current_delay_days'] = new_delay; stats['next_show_date'] = (today + timedelta(days=new_delay)).isoformat()
                stats['consecutive_correct'] = 0
        elif "PARTIAL_MATCH" in result_type:
            stats['article_wrong'] += 1; daily_level_wrong[word_lvl] += 1
        else: # NO_MATCH
            stats['wrong'] += 1
            daily_wrong_per_word[word_to_update] = daily_wrong_per_word.get(word_to_update, 0) + 1
            daily_level_wrong[word_lvl] += 1
            if daily_wrong_per_word[word_to_update] >= HARD_WORD_THRESHOLD:
                stats['wrong'] += 2; stats['streak_level'] = 0; stats['consecutive_correct'] = 0; stats['current_delay_days'] = 1; stats['next_show_date'] = (today + timedelta(days=1)).isoformat()
            else:
                new_delay = max(0, stats['current_delay_days'] - stats['streak_level']); stats['current_delay_days'] = new_delay; stats['next_show_date'] = (today + timedelta(days=new_delay)).isoformat(); stats['consecutive_correct'] = 0; stats['streak_level'] = 0
        
        changed_files.add(word_lvl)

    for lvl in changed_files:
        data_manager.save_repetition_stats(lvl, all_level_data[lvl])

    report_manager.save_report_data(report_data)

    return jsonify({"status": "success", "message": f"Updated {len(results)} words."})