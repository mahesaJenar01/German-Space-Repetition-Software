import data_manager

# --- The single source for the word-to-level mapping cache ---
_word_level_map = None
# --- NEW: The single source for the word-to-details mapping cache ---
_word_details_map = None


def get_word_to_level_map():
    """
    Creates and caches a mapping from each base word to its CEFR level.
    This avoids reading multiple files on every API call.
    """
    global _word_level_map
    if _word_level_map is None:
        print("Initializing word-to-level map cache...")
        _word_level_map = {}
        for lvl in data_manager.LEVELS:
            # load_output_words now returns { word: [details_array] }
            words_data = data_manager.load_output_words(lvl)
            for word_key in words_data.keys():
                _word_level_map[word_key] = lvl
        print(f"Cache initialized with {len(_word_level_map)} words.")
    return _word_level_map

def get_word_details_map():
    """
    Creates and caches a mapping from each base word to its full array of meaning objects.
    This avoids reading files to look up word metadata during updates.
    """
    global _word_details_map
    if _word_details_map is None:
        print("Initializing word-to-details map cache...")
        _word_details_map = {}
        for lvl in data_manager.LEVELS:
            level_words_data = data_manager.load_output_words(lvl)
            _word_details_map.update(level_words_data)
        print(f"Details cache initialized with {len(_word_details_map)} words.")
    return _word_details_map