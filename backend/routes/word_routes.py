from flask import Blueprint, jsonify, request
import data_manager
from cache import get_word_details_map

word_bp = Blueprint('word_bp', __name__)

@word_bp.route('/api/word/star', methods=['POST'])
def toggle_star_status():
    """
    Toggles the 'is_starred' status for a given word item (item_key).
    """
    data = request.json
    item_key = data.get('item_key')
    new_status = data.get('is_starred')

    # 1. Validate input
    if not item_key or '#' not in item_key or new_status is None:
        return jsonify({"error": "Missing or invalid 'item_key' or 'is_starred' status"}), 400

    # 2. Determine the word's correct level using the cache
    word_details_map = get_word_details_map()
    base_word, meaning_str = item_key.split('#', 1)
    
    word_lvl = None
    meanings_array = word_details_map.get(base_word)
    if meanings_array:
        meaning_str_stripped = meaning_str.strip()
        correct_meaning_obj = next((m for m in meanings_array if m['meaning'].strip() == meaning_str_stripped), None)
        if correct_meaning_obj:
            word_lvl = correct_meaning_obj.get('level', '').lower()

    if not word_lvl or word_lvl not in data_manager.LEVELS:
        return jsonify({"error": f"Could not determine a valid level for item_key '{item_key}'"}), 404

    # 3. Load, update, and save the repetition stats
    try:
        repetition_stats = data_manager.load_repetition_stats(word_lvl)
        
        # Get existing stats or create a new entry if it's the first interaction
        word_data = repetition_stats.setdefault(item_key, data_manager.get_new_repetition_schema())
        
        word_data['is_starred'] = bool(new_status)
        
        data_manager.save_repetition_stats(word_lvl, repetition_stats)
        
        return jsonify({
            "status": "success",
            "item_key": item_key,
            "is_starred": word_data['is_starred']
        })

    except Exception as e:
        print(f"ERROR: Failed to update star status for {item_key}. Reason: {e}")
        return jsonify({"error": "An internal error occurred while updating the word."}), 500