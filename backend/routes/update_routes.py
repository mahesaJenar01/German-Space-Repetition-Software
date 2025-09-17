from flask import Blueprint, jsonify, request
from datetime import datetime
import data_manager
import report_manager
from cache import get_word_to_level_map, get_word_details_map
from logic import word_updater, report_updater # <-- NEW IMPORTS

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
    report_data['today_str'] = datetime.now().strftime('%Y-%m-%d') # Add today's date for helpers
    
    word_level_map = get_word_to_level_map()
    word_details_map = get_word_details_map()

    # 2. Process confusions first (as it might update stats for words not in this quiz)
    all_level_data, changed_files = word_updater.process_confusions(results, all_level_data, word_level_map)

    # 3. Process each quiz result to update word repetition stats
    daily_wrong_counts_today = report_data.get('daily_wrong_counts', {}).get(report_data['today_str'], {})
    for result in results:
        word = result.get('word')
        word_lvl = word_level_map.get(word)
        if not word_lvl: continue

        # Get the word's current stats
        stats = all_level_data[word_lvl].setdefault(word, data_manager.REPETITION_SCHEMA.copy())
        
        # Get how many times this specific word was wrong today
        daily_wrong_count = daily_wrong_counts_today.get(word, 0)
        
        # Call the pure update function to get the new state
        updated_stats = word_updater.process_quiz_result(stats, result, daily_wrong_count)
        
        # Place the new state back into our main data object
        all_level_data[word_lvl][word] = updated_stats
        changed_files.add(word_lvl)

    # 4. Update the performance reports in a single, separate step
    report_data = report_updater.update_reports_from_results(
        report_data, results, word_level_map, word_details_map
    )

    # 5. Save all changes to disk
    for lvl in changed_files:
        data_manager.save_repetition_stats(lvl, all_level_data[lvl])
    
    if 'today_str' in report_data: del report_data['today_str'] # Clean up temporary key
    report_manager.save_report_data(report_data)

    return jsonify({"status": "success", "message": f"Updated {len(results)} words."})