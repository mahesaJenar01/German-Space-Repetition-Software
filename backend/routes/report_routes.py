from flask import Blueprint, jsonify
from datetime import datetime
import data_manager
import report_manager
from cache import get_word_details_map

report_bp = Blueprint('report_bp', __name__)

# --- THIS ENDPOINT IS NOW MODIFIED ---
@report_bp.route('/api/report/today', methods=['GET'])
def get_today_practiced_count():
    """
    Calculates the total number of UNIQUE words (new or review)
    that the user has practiced today.
    """
    report_data = report_manager.load_report_data()
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # Get the dictionary for today, which looks like: {"a1": ["word1"], "b1": ["word2", "word3"]}
    seen_today_data = report_data.get('daily_seen_words', {}).get(today_str, {})
    
    # Sum the number of words in each level's list
    total_practiced = sum(len(words) for words in seen_today_data.values())
        
    # Return with a more descriptive key
    return jsonify({"practiced_today": total_practiced})


@report_bp.route('/api/report/today_stats', methods=['GET'])
def get_today_accuracy_stats():
    """Returns today's correct and wrong counts, broken down by level."""
    report_data = report_manager.load_report_data()
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    correct_by_level = report_data.get('daily_level_correct_counts', {}).get(today_str, {})
    wrong_by_level = report_data.get('daily_level_wrong_counts', {}).get(today_str, {})
    
    return jsonify({
        "correct_by_level": correct_by_level,
        "wrong_by_level": wrong_by_level
    })

# --- NEW ENDPOINT FOR THE DAILY DEBRIEF ---
@report_bp.route('/api/report/daily_debrief/<level>', methods=['GET'])
def get_daily_debrief(level):
    """
    Analyzes all words practiced today for a given level and categorizes them
    based on performance: mastered, making progress, or tricky.
    """
    if level not in data_manager.LEVELS:
        return jsonify({"error": "Invalid level specified"}), 400

    # 1. Load all necessary data
    report_data = report_manager.load_report_data()
    repetition_stats = data_manager.load_repetition_stats(level)
    word_details_map = get_word_details_map()
    today_str = datetime.now().strftime('%Y-%m-%d')

    # 2. Get the list of item_keys seen today for this level
    seen_today_by_level = report_data.get('daily_seen_words', {}).get(today_str, {})
    item_keys_for_level = seen_today_by_level.get(level, [])

    if not item_keys_for_level:
        return jsonify({"mastered": [], "progress": [], "tricky": []})

    # 3. Get today's error records for efficient lookup
    wrong_counts_today = report_data.get('daily_wrong_counts', {}).get(today_str, {})
    article_wrong_counts_today = report_data.get('daily_article_wrong_counts', {}).get(today_str, {})

    # 4. Initialize result lists
    mastered_today = []
    making_progress = []
    tricky_words = []

    # 5. Categorize each word
    for item_key in item_keys_for_level:
        base_word = item_key.split('#')[0]
        
        # Combine word details with its current repetition stats
        details = next((m for m in word_details_map.get(base_word, []) if f"{base_word}#{m['meaning']}" == item_key), None)
        stats = repetition_stats.get(item_key, {})
        
        if not details:
            continue

        # Merge details and stats for the frontend. Most importantly, 'is_starred'.
        full_word_data = {**details, **stats, "item_key": item_key}

        # Check if the word had any errors today
        had_error_today = item_key in wrong_counts_today or item_key in article_wrong_counts_today

        if not had_error_today:
            mastered_today.append(full_word_data)
        else:
            # The word had an error. Check if the *last* attempt was wrong.
            if stats.get('last_result_was_wrong', False):
                tricky_words.append(full_word_data)
            else:
                # Had an error, but the last attempt was correct -> making progress!
                making_progress.append(full_word_data)
    
    return jsonify({
        "mastered": mastered_today,
        "progress": making_progress,
        "tricky": tricky_words
    })