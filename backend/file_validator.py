import json
from pathlib import Path

# --- Configuration ---
OUTPUT_FOLDER = Path("output")
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
        for original_id, meanings_array in list(word_dict.items()):
            # Data is an array; get details from the first object.
            if not meanings_array or not isinstance(meanings_array, list):
                print(f"   - ⚠️  Warning: Invalid entry found for key '{original_id}' in {source_level}.json. Skipping.")
                continue
                
            first_meaning_obj = meanings_array[0]
            actual_level = first_meaning_obj.get("level", "").strip().lower()
            word_str = first_meaning_obj.get('word', 'Unknown Word')

            if not actual_level or actual_level not in LEVELS:
                print(f"   - ⚠️  Warning: Word '{word_str}' in {source_level}.json has an invalid or missing level: '{actual_level}'. Skipping.")
                continue

            if actual_level != source_level:
                print(f"   - ➡️  Relocating '{word_str}' from {source_level}.json to {actual_level}.json.")
                # The item to move is the entire array of meanings.
                words_to_move[actual_level].append(meanings_array)
                del all_data[source_level][original_id]
                total_misplaced += 1

    if total_misplaced == 0:
        print("✅ No misplaced words found.")
    else:
        print(f"✅ Relocated {total_misplaced} words successfully.")
        for dest_level, arrays_list in words_to_move.items():
            if not arrays_list: continue
            
            existing_arrays = list(all_data[dest_level].values())
            existing_arrays.extend(arrays_list)
            # Temporarily store as a list of arrays. We'll build the final dict from this.
            all_data[dest_level] = existing_arrays

    # Step 3: Re-index and standardize ALL files
    print("\n--- Phase 2: Standardizing all files (Sorting & Re-indexing)... ---")
    for level, data in all_data.items():
        # Ensure data is a list of arrays for sorting
        if isinstance(data, dict):
            word_arrays = list(data.values())
        elif isinstance(data, list): # Handles the case where words were moved
            word_arrays = data
        else:
            word_arrays = []

        # Sort the list of arrays based on the 'word' in the first object of each array (ascending).
        word_arrays.sort(key=lambda arr: arr[0].get('word', '').lower() if (arr and arr[0]) else '')
        
        # Create a new, clean dictionary with sequential integer keys starting from "1"
        reindexed_dict = {str(i + 1): arr for i, arr in enumerate(word_arrays)}
        
        output_path = OUTPUT_FOLDER / f"output_{level}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(reindexed_dict, f, ensure_ascii=False, indent=2)
        print(f"   - ✅ Wrote {output_path} with {len(reindexed_dict)} standardized entries.")

    print("\n--- Validator & Standardizer Finished Successfully ---")

if __name__ == "__main__":
    validate_and_standardize_files()