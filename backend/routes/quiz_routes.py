from flask import Blueprint, jsonify, request
import data_manager
from logic import quiz_selector
from cache import get_word_to_level_map

quiz_bp = Blueprint('quiz_bp', __name__)

@quiz_bp.route('/api/words/details/<level>', methods=['GET'])
def get_word_details(level):
    if level != "mix" and level not in data_manager.LEVELS:
        return jsonify({"error": "Invalid level specified"}), 400

    word_map = get_word_to_level_map()
    
    # Call the refactored selection logic which now returns a dictionary
    selection_result = quiz_selector.select_quiz_words(level, word_map)
    
    # The quiz is empty if there are no more due words
    if not selection_result["quiz_words"]:
        # Still return the session info so the frontend knows the level context
        return jsonify(selection_result), 200

    return jsonify(selection_result)

@quiz_bp.route('/api/stats', methods=['POST'])
def get_stats():
    data = request.json
    words_to_lookup = data.get('words', [])
    level = data.get('level')

    if not words_to_lookup or not level:
        return jsonify({"error": "Missing 'words' or 'level' in request"}), 400

    all_repetition_stats = {}
    levels_to_load = data_manager.LEVELS if level == "mix" else [level]

    for lvl in levels_to_load:
        all_repetition_stats.update(data_manager.load_repetition_stats(lvl))
        
    stats_to_return = {word: all_repetition_stats[word] for word in words_to_lookup if word in all_repetition_stats}
            
    return jsonify(stats_to_return)