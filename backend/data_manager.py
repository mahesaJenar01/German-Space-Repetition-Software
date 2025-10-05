import json
from pathlib import Path
import copy # <-- IMPORT THE COPY MODULE

# Centralized configuration for file paths
OUTPUT_FOLDER = Path("output")
REPETITION_FOLDER = Path("repetition-list")
LEVELS = ["a1", "a2", "b1"]

# --- NEW: Centralized gameplay configuration ---
DAILY_NEW_WORD_LIMIT = 100
MASTERY_GOAL = 3           # 3 consecutive correct answers for mastery
FAILURE_THRESHOLD = 3      # 3 total wrong answers for failure

# The single source of truth for a new word's repetition stats.
REPETITION_SCHEMA = {
    "right": 0,
    "wrong": 0,
    "article_wrong": 0,
    "total_encountered": 0,
    "last_seen": None,
    "last_correct": None,
    "consecutive_correct": 0,
    "streak_level": 0,
    "current_delay_days": 0,
    "next_show_date": None,
    "recent_history": [],
    "failed_first_encounter": False,
    "last_result_was_wrong": False,
    "successful_corrections": 0,
    "is_starred": False, # <-- NEW FIELD
}

# --- NEW FUNCTION TO FIX THE BUG ---
def get_new_repetition_schema():
    """
    Returns a deep copy of the repetition schema to ensure mutable objects
    like lists and dicts are not shared between different word stats.
    """
    return copy.deepcopy(REPETITION_SCHEMA)

def load_repetition_stats(level):
    """Loads user repetition stats from a specific level's JSON file."""
    REPETITION_FOLDER.mkdir(exist_ok=True)
    file_path = REPETITION_FOLDER / f"{level}_repetition.json"
    if not file_path.exists():
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_repetition_stats(level, data):
    """Saves the repetition stats data for a specific level."""
    REPETITION_FOLDER.mkdir(exist_ok=True)
    file_path = REPETITION_FOLDER / f"{level}_repetition.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_output_words(level):
    """
    Loads all word data from a specific output file.
    The new structure is { "word": [ {meaning_obj_1}, {meaning_obj_2} ] }.
    """
    file_path = OUTPUT_FOLDER / f"output_{level}.json"
    if not file_path.exists():
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # The new structure is already { word: [details_array] }.
        # We need to handle the old numeric key format if it exists.
        if all(key.isdigit() for key in data.keys()):
            print(f"INFO: Detected old numeric key format in {file_path}. Converting to word-based keys.")
            word_based_data = {}
            for key, value_array in data.items():
                if value_array and 'word' in value_array[0]:
                    word_key = value_array[0]['word']
                    if word_key in word_based_data:
                         word_based_data[word_key].extend(value_array)
                    else:
                         word_based_data[word_key] = value_array
            return word_based_data
        
        return data

    except (json.JSONDecodeError, IOError):
        return {}