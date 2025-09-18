import json
from pathlib import Path
import copy # <-- IMPORT THE COPY MODULE

# Centralized configuration for file paths
OUTPUT_FOLDER = Path("output")
REPETITION_FOLDER = Path("repetition-list")
LEVELS = ["a1", "a2", "b1"]

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
    "confused_with": {},
    "recent_history": [],
    "failed_first_encounter": False,
    "last_result_was_wrong": False,
    "successful_corrections": 0,
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
    """Loads all word metrics from a specific output file and maps them by word."""
    file_path = OUTPUT_FOLDER / f"output_{level}.json"
    if not file_path.exists():
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        word_map = {}
        for item in data.values():
            if isinstance(item, dict) and 'word' in item:
                word_map[item['word']] = item
        return word_map
    except (json.JSONDecodeError, IOError):
        return {}