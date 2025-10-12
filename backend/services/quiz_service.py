from datetime import datetime
import data_manager
import report_manager
from cache import get_word_to_level_map, get_word_details_map
from logic import word_updater, report_updater

def process_quiz_results(results):
    """
    Handles the core business logic of processing quiz results.
    This function is self-contained and can be tested independently of the web server.
    """
    # 1. Load all necessary data and state
    all_level_data = {lvl: data_manager.load_repetition_stats(lvl) for lvl in data_manager.LEVELS}
    report_data = report_manager.load_report_data()
    today_str = datetime.now().strftime('%Y-%m-%d')
    report_data['today_str'] = today_str # Add temporarily for processing

    # 2. Access cached data for efficient lookups
    word_level_map = get_word_to_level_map()
    word_details_map = get_word_details_map()

    daily_wrong_counts_today = report_data.get('daily_wrong_counts', {}).get(today_str, {})

    # 3. Process each result from the quiz
    for result in results:
        item_key = result.get('word')
        if not item_key or '#' not in item_key:
            continue

        base_word, meaning_str = item_key.split('#', 1)
        
        # Determine the correct level for the specific word-meaning pair
        word_lvl = None
        meanings_array = word_details_map.get(base_word)
        if meanings_array:
            meaning_str_stripped = meaning_str.strip()
            correct_meaning_obj = next((m for m in meanings_array if m['meaning'].strip() == meaning_str_stripped), None)
            if correct_meaning_obj:
                word_lvl = correct_meaning_obj.get('level', '').lower()

        if not word_lvl:
            print(f"WARNING: Could not determine level for item_key '{item_key}'. Skipping update.")
            continue

        # Get or create the statistics for this specific item
        stats = all_level_data[word_lvl].setdefault(item_key, data_manager.get_new_repetition_schema())
        
        daily_wrong_count_for_item = daily_wrong_counts_today.get(item_key, 0)
        
        # Update the item's repetition stats
        final_stats, was_just_learned = word_updater.process_quiz_result(stats, result, daily_wrong_count_for_item)
        all_level_data[word_lvl][item_key] = final_stats

        # --- ADD THIS BLOCK ---
        # If the word was just learned, add it to the report.
        if was_just_learned:
            print(f"INFO: Word '{item_key}' has been learned!")
            learned_words_for_level = report_data['word_learned'].setdefault(word_lvl, {})
            # We store the date it was learned.
            learned_words_for_level[item_key] = today_str

    # 4. Update aggregate reports
    report_data = report_updater.update_reports_from_results(
        report_data, results, word_level_map, word_details_map
    )

    # 5. Persist all changes to the filesystem
    for lvl, data_to_save in all_level_data.items():
        data_manager.save_repetition_stats(lvl, data_to_save)
    
    # Clean up the temporary key before saving
    if 'today_str' in report_data:
        del report_data['today_str']
    report_manager.save_report_data(report_data)

    print(f"Successfully processed and saved {len(results)} quiz results.")