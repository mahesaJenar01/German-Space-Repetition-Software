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
    
    selection_result = quiz_selector.select_quiz_words(level, word_map)
    
    if not selection_result["quiz_words"]:
        return jsonify(selection_result), 200

    return jsonify(selection_result)

@quiz_bp.route('/api/stats', methods=['POST'])
def get_stats():
    data = request.json
    # The frontend will now send a list of item_keys
    item_keys_to_lookup = data.get('words', [])
    level = data.get('level') # level is still useful for 'mix' mode

    if not item_keys_to_lookup or not level:
        return jsonify({"error": "Missing 'words' (item_keys) or 'level' in request"}), 400

    all_repetition_stats = {}
    levels_to_load = data_manager.LEVELS if level == "mix" else [level]

    for lvl in levels_to_load:
        all_repetition_stats.update(data_manager.load_repetition_stats(lvl))
        
    stats_to_return = {key: all_repetition_stats.get(key, {}) for key in item_keys_to_lookup}
            
    return jsonify(stats_to_return)