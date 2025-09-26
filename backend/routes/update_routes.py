from flask import Blueprint, jsonify, request
from datetime import datetime
import data_manager
import report_manager
from cache import get_word_to_level_map, get_word_details_map
from logic import word_updater, report_updater

update_bp = Blueprint('update_bp', __name__)

@update_bp.route('/api/update', methods=['POST'])
def update_words():
    data = request.json
    results = data.get('results', [])
    level = data.get('level')
    
    if not level or (level != "mix" and level not in data_manager.LEVELS):
        return jsonify({"error": "Invalid or missing level"}), 400
    
    # 1. Load all necessary data and caches
    all_level_data = {lvl: data_manager.load_repetition_stats(lvl) for lvl in data_manager.LEVELS}
    report_data = report_manager.load_report_data()
    report_data['today_str'] = datetime.now().strftime('%Y-%m-%d')
    
    word_level_map = get_word_to_level_map()
    word_details_map = get_word_details_map()

    # Process individual quiz results (operates on item_key)
    daily_wrong_counts_today = report_data.get('daily_wrong_counts', {}).get(report_data['today_str'], {})
    
    for result in results:
        item_key = result.get('word')
        if not item_key or '#' not in item_key: continue

        base_word, meaning_str = item_key.split('#', 1)
        
        word_lvl = None
        meanings_array = word_details_map.get(base_word)
        if meanings_array:
            correct_meaning_obj = next((m for m in meanings_array if m['meaning'] == meaning_str), None)
            if correct_meaning_obj:
                word_lvl = correct_meaning_obj.get('level', '').lower()

        if not word_lvl:
            print(f"WARNING: Could not determine level for item_key '{item_key}'. Skipping update.")
            continue

        stats = all_level_data[word_lvl].setdefault(item_key, data_manager.get_new_repetition_schema())
        original_next_show_date = stats.get('next_show_date')
        
        daily_wrong_count = daily_wrong_counts_today.get(base_word, {}).get('total', 0)
        
        updated_stats = word_updater.process_quiz_result(stats, result, daily_wrong_count)
        final_stats = word_updater.adjust_schedule_for_forced_word(
            updated_stats, result, original_next_show_date
        )
        all_level_data[word_lvl][item_key] = final_stats

    # Update performance reports
    report_data = report_updater.update_reports_from_results(
        report_data, results, word_level_map, word_details_map
    )

    # Save ALL level data changes to disk
    for lvl, data_to_save in all_level_data.items():
        data_manager.save_repetition_stats(lvl, data_to_save)
    
    if 'today_str' in report_data: del report_data['today_str']
    report_manager.save_report_data(report_data)

    return jsonify({"status": "success", "message": f"Updated {len(results)} words."})