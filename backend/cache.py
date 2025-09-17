import data_manager

# --- The single source for the word-to-level mapping cache ---
_word_level_map = None

def get_word_to_level_map():
    """
    Creates and caches a mapping from each word to its CEFR level.
    This avoids reading multiple files on every API call.
    """
    global _word_level_map
    if _word_level_map is None:
        print("Initializing word-to-level map cache...")
        _word_level_map = {}
        for lvl in data_manager.LEVELS:
            words_data = data_manager.load_output_words(lvl)
            for word_key in words_data.keys():
                _word_level_map[word_key] = lvl
        print(f"Cache initialized with {len(_word_level_map)} words.")
    return _word_level_map