from flask import Blueprint, jsonify
from datetime import datetime
import data_manager
import report_manager

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