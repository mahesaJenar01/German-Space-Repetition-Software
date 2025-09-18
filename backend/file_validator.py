import json
from pathlib import Path

# --- Configuration ---
# Point this to the folder containing your output_*.json files
OUTPUT_FOLDER = Path("output")
# Define the levels you want to process
LEVELS = ["a1", "a2", "b1"]

def validate_and_standardize_files():
    """
    Validates vocabulary files for two issues:
    1.  Relocates words that are in the wrong level file (e.g., an "A2" word in the A1 file).
    2.  Standardizes ALL files by sorting them alphabetically by word and re-indexing them
        with sequential numerical keys (e.g., "1", "2", "3", ...), ensuring perfect
        structural integrity.
    This script will always rewrite the files to enforce sorting and indexing.
    """
    print("--- Starting Vocabulary File Validator & Standardizer ---")
    
    # Step 1: Load all data from all level files into memory
    all_data = {}
    for level in LEVELS:
        file_path = OUTPUT_FOLDER / f"output_{level}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Load and store the original dictionary
                    all_data[level] = json.load(f)
                print(f"✅ Loaded {file_path} ({len(all_data[level])} entries)")
            except json.JSONDecodeError:
                print(f"⚠️  Error: Could not parse {file_path}. Treating as empty.")
                all_data[level] = {}
        else:
            print(f"ℹ️  Info: File {file_path} not found. Will create if needed.")
            all_data[level] = {}

    # Step 2: Identify and relocate misplaced words
    words_to_move = {level: [] for level in LEVELS}
    total_misplaced = 0

    print("\n--- Phase 1: Checking for misplaced words... ---")
    for source_level, word_dict in all_data.items():
        # Iterate over a copy of the items because we might delete from the original dict
        for original_id, word_obj in list(word_dict.items()):
            actual_level = word_obj.get("level", "").strip().lower()

            if not actual_level or actual_level not in LEVELS:
                print(f"   - ⚠️  Warning: Word '{word_obj.get('word')}' in {source_level}.json has an invalid or missing level: '{actual_level}'. Skipping.")
                continue

            if actual_level != source_level:
                print(f"   - ➡️  Relocating '{word_obj.get('word')}' from {source_level}.json to {actual_level}.json.")
                # Add the word object to the correct destination list
                words_to_move[actual_level].append(word_obj)
                # Remove the word from its incorrect source
                del all_data[source_level][original_id]
                total_misplaced += 1

    if total_misplaced == 0:
        print("✅ No misplaced words found.")
    else:
        print(f"✅ Relocated {total_misplaced} words successfully.")
        # Add the moved words to their new destination dictionaries in memory
        for dest_level, words_list in words_to_move.items():
            if not words_list:
                continue
            
            # Add the word objects to the end of the list for now. Sorting will handle order.
            # We convert the existing dict values to a list and extend it.
            existing_words = list(all_data[dest_level].values())
            existing_words.extend(words_list)
            # Temporarily store as a list of objects. We'll build the dict from this list.
            all_data[dest_level] = existing_words


    # Step 3: Re-index and standardize ALL files
    print("\n--- Phase 2: Standardizing all files (Sorting & Re-indexing)... ---")
    for level, data in all_data.items():
        # Ensure the data is a list of dictionary objects for sorting
        if isinstance(data, dict):
            word_objects = list(data.values())
        elif isinstance(data, list): # This handles the case where words were moved
            word_objects = data
        else: # Should not happen, but good for safety
            word_objects = []

        # Sort the words alphabetically to ensure a consistent order every time
        word_objects.sort(key=lambda x: x.get('word', '').lower())
        
        # Create a new, clean dictionary with sequential integer keys starting from "1"
        reindexed_dict = {str(i + 1): word_obj for i, word_obj in enumerate(word_objects)}
        
        # Save the cleaned and re-indexed data
        output_path = OUTPUT_FOLDER / f"output_{level}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(reindexed_dict, f, ensure_ascii=False, indent=2)
        print(f"   - ✅ Wrote {output_path} with {len(reindexed_dict)} standardized entries.")

    print("\n--- Validator & Standardizer Finished Successfully ---")

# This allows the script to be run from the command line
if __name__ == "__main__":
    validate_and_standardize_files()