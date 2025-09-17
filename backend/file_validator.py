import json
from pathlib import Path

# --- Configuration ---
# Point this to the folder containing your output_*.json files
OUTPUT_FOLDER = Path("output")
# Define the levels you want to process
LEVELS = ["a1", "a2", "b1"]

def validate_and_fix_levels():
    """
    Validates that each word in an output_{level}.json file has the correct level property.
    Moves misplaced words to their correct file and re-indexes all affected files.
    """
    print("--- Starting Vocabulary File Validator ---")
    
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
                print(f"⚠️  Error: Could not parse {file_path}. Skipping.")
                all_data[level] = {}
        else:
            print(f"ℹ️  Info: File {file_path} not found. Will create if needed.")
            all_data[level] = {}

    # Step 2: Identify misplaced words and schedule them for moving
    words_to_move = {level: [] for level in LEVELS}
    files_to_clean = set()
    total_misplaced = 0

    print("\n--- Checking for misplaced words... ---")
    for source_level, word_dict in all_data.items():
        # We iterate over a copy of the items because we will be deleting from the original dict
        for original_id, word_obj in list(word_dict.items()):
            actual_level = word_obj.get("level", "").strip().lower()

            if not actual_level or actual_level not in LEVELS:
                print(f"   - ⚠️  Warning: Word '{word_obj.get('word')}' in {source_level}.json has an invalid or missing level: '{actual_level}'. Skipping.")
                continue

            if actual_level != source_level:
                print(f"   - ➡️  Found misplaced word '{word_obj.get('word')}' in {source_level}.json. Moving to {actual_level}.json.")
                # Add the word object to the correct destination list
                words_to_move[actual_level].append(word_obj)
                # Remove the word from its incorrect source
                del all_data[source_level][original_id]
                
                # Mark both files as needing updates
                files_to_clean.add(source_level)
                files_to_clean.add(actual_level)
                total_misplaced += 1

    if total_misplaced == 0:
        print("✅ No misplaced words found. All files are clean!")
        print("\n--- Validator Finished ---")
        return

    print(f"\n--- Relocating {total_misplaced} words... ---")
    # Step 3: Add the moved words to their new destination dictionaries
    for dest_level, words_list in words_to_move.items():
        if not words_list:
            continue
        
        # We don't care about IDs yet, just add the words. We will re-index later.
        for i, word_obj in enumerate(words_list):
            # Use a temporary, unique key to avoid collisions before re-indexing
            temp_key = f"new_{i}" 
            all_data[dest_level][temp_key] = word_obj

    print("\n--- Re-indexing and saving files... ---")
    # Step 4: Re-index all affected files and save them
    for level in files_to_clean:
        # Get all the word objects from the dictionary's values
        word_objects = list(all_data[level].values())
        
        # Sort the words alphabetically to ensure a consistent order every time
        word_objects.sort(key=lambda x: x.get('word', ''))
        
        # Create a new, clean dictionary with sequential integer keys
        reindexed_dict = {str(i + 1): word_obj for i, word_obj in enumerate(word_objects)}
        
        # Save the cleaned and re-indexed data
        output_path = OUTPUT_FOLDER / f"output_{level}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(reindexed_dict, f, ensure_ascii=False, indent=2)
        print(f"   - ✅ Saved {output_path} with {len(reindexed_dict)} correctly placed entries.")

    print("\n--- Validator Finished Successfully ---")

# This allows the script to be run from the command line
if __name__ == "__main__":
    validate_and_fix_levels()