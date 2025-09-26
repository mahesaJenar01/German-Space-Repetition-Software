import json
from pathlib import Path

# Centralized configuration
REPORT_FOLDER = Path("performance-report")
REPORT_FILE = REPORT_FOLDER / "repetition_report.json"
LEVELS = ["a1", "a2", "b1"]

# The structure of the report file
# --- SCHEMA UPDATED ---
DEFAULT_REPORT_SCHEMA = {
    "word_learned": {level: {} for level in LEVELS},
    "daily_seen_words": {},
    "daily_wrong_counts": {},
    "daily_article_wrong_counts": {},
    "daily_level_correct_counts": {},
    "daily_level_wrong_counts": {},
    "daily_level_article_wrong_counts": {},
    "category_performance": {},
}

def load_report_data():
    """Loads the performance report data from its JSON file."""
    REPORT_FOLDER.mkdir(exist_ok=True)
    if not REPORT_FILE.exists():
        return DEFAULT_REPORT_SCHEMA.copy()
    try:
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # --- VALIDATION LOGIC UPDATED ---
            # Simple validation/migration to ensure all new keys exist
            if "word_learned" not in data:
                data["word_learned"] = {level: {} for level in LEVELS}
            if "daily_seen_words" not in data:
                data["daily_seen_words"] = {}
            if "daily_wrong_counts" not in data:
                data["daily_wrong_counts"] = {}
            if "daily_article_wrong_counts" not in data:
                data["daily_article_wrong_counts"] = {}
            if "daily_level_correct_counts" not in data:
                data["daily_level_correct_counts"] = {}
            if "daily_level_wrong_counts" not in data:
                data["daily_level_wrong_counts"] = {}
            if "category_performance" not in data:
                data["category_performance"] = {}
            if "daily_level_article_wrong_counts" not in data:
                data["daily_level_article_wrong_counts"] = {}

            # --- NEW: Migrate old wrong_counts format to new flattened format ---
            for key_to_migrate in ["daily_wrong_counts", "daily_article_wrong_counts"]:
                if key_to_migrate in data:
                    for date_str, word_entries in data[key_to_migrate].items():
                        # Check if any entry follows the old format. If so, migrate the whole day's data.
                        if any(isinstance(v, dict) and 'total' in v for v in word_entries.values()):
                            migrated_entries = {}
                            for base_word, value in word_entries.items():
                                if isinstance(value, dict) and 'details' in value:
                                    for item_key, count in value.get('details', {}).items():
                                        migrated_entries[item_key] = migrated_entries.get(item_key, 0) + count
                            data[key_to_migrate][date_str] = migrated_entries

            # Clean up the old, unused key if it exists
            if "daily_correct_counts" in data:
                del data["daily_correct_counts"]
            return data
    except (json.JSONDecodeError, IOError):
        return DEFAULT_REPORT_SCHEMA.copy()

def save_report_data(data):
    """Saves the performance report data to its JSON file."""
    REPORT_FOLDER.mkdir(exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)