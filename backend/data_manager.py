import json
from pathlib import Path

# Centralized configuration for file paths
OUTPUT_FOLDER = Path("output")
REPETITION_FOLDER = Path("repetition-list")
LEVELS = ["a1", "a2", "b1"]

# The single source of truth for a new word's repetition stats.
# --- THIS SCHEMA IS NOW UPGRADED FOR THE NEW SCHEDULING LOGIC ---
REPETITION_SCHEMA = {
    "right": 0,
    "wrong": 0,
    "article_wrong": 0, # <-- NEW FIELD
    "total_encountered": 0,
    "last_seen": None,
    "last_correct": None,
    # NEW FIELDS FOR SCHEDULED REPETITION:
    "consecutive_correct": 0,   # Tracks the 3-in-a-row streak.
    "streak_level": 0,          # This is your 'n', the number of times a streak was achieved.
    "current_delay_days": 0,    # Stores the last calculated delay.
    "next_show_date": None,     # ISO Date string for when the word is "unlocked".
    "confused_with": {},        # <-- NEW: Tracks word-swap confusions.
}

def load_repetition_stats(level):
    """Loads user repetition stats from a specific level's JSON file."""
    REPETITION_FOLDER.mkdir(exist_ok=True) # Ensure folder exists
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
    REPETITION_FOLDER.mkdir(exist_ok=True) # Ensure folder exists
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