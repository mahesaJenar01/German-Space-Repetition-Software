from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import data_manager
import report_manager
from cache import get_word_to_level_map

update_bp = Blueprint('update_bp', __name__)
HARD_WORD_THRESHOLD = 3 # Must match the value in teacher_logic

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

    daily_seen = report_data.setdefault('daily_seen_words', {}).setdefault(today_str, {})
    daily_wrong_per_word = report_data.setdefault('daily_wrong_counts', {}).setdefault(today_str, {})
    daily_level_correct = report_data.setdefault('daily_level_correct_counts', {}).setdefault(today_str, {lvl: 0 for lvl in data_manager.LEVELS})
    daily_level_wrong = report_data.setdefault('daily_level_wrong_counts', {}).setdefault(today_str, {lvl: 0 for lvl in data_manager.LEVELS})
    word_learned_counts = report_data.setdefault('word_learned', {})

    for result in results:
        word_to_update = result.get('word')
        result_type = result.get('result_type')
        
        word_lvl = word_level_map.get(word_to_update)

        if not word_lvl:
            print(f"WARNING: Could not find level for word '{word_to_update}'. Skipping update.")
            continue

        repetition_data_for_level = all_level_data[word_lvl]
        stats = repetition_data_for_level.setdefault(word_to_update, data_manager.REPETITION_SCHEMA.copy())

        # --- THIS IS THE IMPROVED LOGIC ---

        # Metric 1: Track all unique words PRACTICED today (new or old).
        # This now runs for EVERY word.
        seen_today_for_level = daily_seen.setdefault(word_lvl, [])
        if word_to_update not in seen_today_for_level:
            seen_today_for_level.append(word_to_update)

        # Metric 2: Track brand new words LEARNED today (first time ever).
        # This only runs if the word has never been encountered before.
        if stats['total_encountered'] == 0:
            level_counts = word_learned_counts.setdefault(word_lvl, {})
            level_counts[today_str] = level_counts.get(today_str, 0) + 1
        
        # --- END of improved logic section ---
        
        stats['total_encountered'] += 1
        stats['last_seen'] = today.isoformat()

        if result_type == "PERFECT_MATCH":
            stats['right'] += 1
            daily_level_correct[word_lvl] += 1
            stats['last_correct'] = today.isoformat()
            stats['consecutive_correct'] += 1
            stats['article_wrong'] = 0
            if stats['consecutive_correct'] >= 3:
                stats['streak_level'] += 1
                new_delay = stats['current_delay_days'] + stats['streak_level']
                stats['current_delay_days'] = new_delay
                stats['next_show_date'] = (today + timedelta(days=new_delay)).isoformat()
                stats['consecutive_correct'] = 0
        elif "PARTIAL_MATCH" in result_type:
            stats['article_wrong'] += 1
            daily_level_wrong[word_lvl] += 1
        else: # NO_MATCH
            stats['wrong'] += 1
            daily_wrong_per_word[word_to_update] = daily_wrong_per_word.get(word_to_update, 0) + 1
            daily_level_wrong[word_lvl] += 1
            
            if daily_wrong_per_word[word_to_update] >= HARD_WORD_THRESHOLD:
                print(f"INFO: Word '{word_to_update}' marked as hard for today.")
                stats['wrong'] += 2
                stats['streak_level'] = 0
                stats['consecutive_correct'] = 0
                stats['current_delay_days'] = 1 
                stats['next_show_date'] = (today + timedelta(days=1)).isoformat()
            else:
                new_delay = max(0, stats['current_delay_days'] - stats['streak_level'])
                stats['current_delay_days'] = new_delay
                stats['next_show_date'] = (today + timedelta(days=new_delay)).isoformat()
                stats['consecutive_correct'] = 0
                stats['streak_level'] = 0
        
        changed_files.add(word_lvl)

    for lvl in changed_files:
        data_manager.save_repetition_stats(lvl, all_level_data[lvl])

    report_manager.save_report_data(report_data)

    return jsonify({"status": "success", "message": f"Updated {len(results)} words."})