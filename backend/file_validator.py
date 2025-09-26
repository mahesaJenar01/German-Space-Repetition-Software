import json
from pathlib import Path

# --- Configuration ---
OUTPUT_FOLDER = Path("output")
LEVELS = ["a1", "a2", "b1"]

def validate_and_standardize_files():
    """
    Validates and standardizes vocabulary files for the "word-keyed" data structure.

    This script performs two main actions:
    1.  Relocates words that are in the wrong level file (e.g., a word with an
        "A2" level property found in the a1_output.json file).
    2.  Standardizes ALL files by sorting their entries alphabetically by the
        word key, ensuring a consistent and predictable file structure.

    The script will always rewrite the files to enforce the alphabetical sorting.
    """
    print("--- Starting Vocabulary File Validator & Standardizer ---")
    
    # Step 1: Load all data from all level files into memory
    all_data = {}
    for level in LEVELS:
        file_path = OUTPUT_FOLDER / f"output_{level}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_data[level] = json.load(f)
                print(f"✅ Loaded {file_path} ({len(all_data[level])} word entries)")
            except json.JSONDecodeError:
                print(f"⚠️  Error: Could not parse {file_path}. Treating as empty.")
                all_data[level] = {}
        else:
            print(f"ℹ️  Info: File {file_path} not found. Will create if needed.")
            all_data[level] = {}

    # Step 2: Identify and prepare misplaced words for relocation
    words_to_move = {level: {} for level in LEVELS} # Store as {dest_level: {word: meanings_array}}
    total_misplaced = 0

    print("\n--- Phase 1: Checking for misplaced words... ---")
    for source_level, word_dict in all_data.items():
        # Use list(word_dict.items()) to create a copy, allowing safe deletion during iteration
        for word_key, meanings_array in list(word_dict.items()):
            if not meanings_array or not isinstance(meanings_array, list):
                print(f"   - ⚠️  Warning: Invalid entry for word '{word_key}' in {source_level}.json. Skipping.")
                continue
                
            first_meaning_obj = meanings_array[0]
            actual_level = first_meaning_obj.get("level", "").strip().lower()

            if not actual_level or actual_level not in LEVELS:
                print(f"   - ⚠️  Warning: Word '{word_key}' in {source_level}.json has an invalid or missing level: '{actual_level}'. Skipping.")
                continue

            if actual_level != source_level:
                print(f"   - ➡️  Relocating '{word_key}' from {source_level}.json to {actual_level}.json.")
                # Add the entire entry (key and value) to the move list for the correct destination
                words_to_move[actual_level][word_key] = meanings_array
                # Remove the entry from the original, incorrect location
                del all_data[source_level][word_key]
                total_misplaced += 1

    # Step 3: Execute the relocation by merging the moved words into the main data
    if total_misplaced == 0:
        print("✅ No misplaced words found.")
    else:
        for dest_level, words_to_add_dict in words_to_move.items():
            if words_to_add_dict:
                all_data[dest_level].update(words_to_add_dict)
        print(f"✅ Relocated {total_misplaced} word entries successfully.")

    # Step 4: Standardize ALL files by sorting and rewriting them
    print("\n--- Phase 2: Standardizing all files by sorting alphabetically... ---")
    for level, data_dict in all_data.items():
        # Sort the dictionary items by key (the word) case-insensitively
        sorted_items = sorted(data_dict.items(), key=lambda item: item[0].lower())
        
        # Create a new dictionary from the sorted items.
        # In Python 3.7+, dicts preserve insertion order, so this will be sorted.
        standardized_dict = dict(sorted_items)
        
        output_path = OUTPUT_FOLDER / f"output_{level}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(standardized_dict, f, ensure_ascii=False, indent=2)
        print(f"   - ✅ Wrote {output_path} with {len(standardized_dict)} sorted word entries.")

    print("\n--- Validator & Standardizer Finished Successfully ---")

if __name__ == "__main__":
    validate_and_standardize_files()