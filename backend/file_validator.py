import json
from pathlib import Path

# --- Configuration ---
OUTPUT_FOLDER = Path("output")
LEVELS = ["a1", "a2", "b1"]

def validate_and_standardize_files():
    """
    Validates and standardizes vocabulary files for the "word-keyed" data structure.

    This script performs two main actions:
    1.  Distributes every individual word meaning into its correct level file.
        If a homonym like "meinen" has meanings for A1, A2, and B1, this
        script will ensure each meaning object is placed in the correct file
        (output_a1.json, output_a2.json, etc.).
    2.  Standardizes ALL files by sorting their entries alphabetically by the
        word key, ensuring a consistent and predictable file structure.
    """
    print("--- Starting Vocabulary File Validator & Standardizer ---")
    
    # Step 1: Load all data from all level files into memory
    all_data_by_file = {}
    for level in LEVELS:
        file_path = OUTPUT_FOLDER / f"output_{level}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_data_by_file[level] = json.load(f)
                print(f"✅ Loaded {file_path} ({len(all_data_by_file[level])} word entries)")
            except json.JSONDecodeError:
                print(f"⚠️  Error: Could not parse {file_path}. Treating as empty.")
                all_data_by_file[level] = {}
        else:
            print(f"ℹ️  Info: File {file_path} not found. Will create if needed.")
            all_data_by_file[level] = {}

    # --- REFINED LOGIC ---
    # Step 2: Create a new, corrected data structure from scratch.
    # This will hold the final, correctly distributed data.
    corrected_data = {level: {} for level in LEVELS}
    total_meanings_relocated = 0
    total_meanings_processed = 0

    print("\n--- Phase 1: Validating and redistributing every word meaning... ---")
    
    # Iterate through all the data we loaded, file by file.
    for source_level, word_dict in all_data_by_file.items():
        # Iterate through each word (e.g., "meinen") in the current file.
        for word_key, meanings_array in word_dict.items():
            if not isinstance(meanings_array, list):
                print(f"   - ⚠️  Warning: Invalid entry for word '{word_key}' in {source_level}.json (not a list). Skipping.")
                continue
                
            # Iterate through each meaning object within the word's list.
            for meaning_obj in meanings_array:
                total_meanings_processed += 1
                actual_level = meaning_obj.get("level", "").strip().lower()

                if not actual_level or actual_level not in LEVELS:
                    print(f"   - ⚠️  Warning: Meaning for '{word_key}' has invalid/missing level: '{actual_level}'. Skipping.")
                    print(f"     -> Meaning: '{meaning_obj.get('meaning', 'N/A')}'")
                    continue

                # This is the core logic: place the meaning object into the correct level's dictionary.
                # setdefault ensures that if the word_key doesn't exist yet in the target level,
                # it creates an empty list for it before appending the meaning.
                corrected_data[actual_level].setdefault(word_key, []).append(meaning_obj)

                # Track if a meaning was in the wrong file.
                if actual_level != source_level:
                    total_meanings_relocated += 1
                    print(f"   - ➡️  Relocating meaning for '{word_key}' from {source_level}.json to {actual_level}.json.")
                    print(f"     -> Meaning: '{meaning_obj.get('meaning', 'N/A')}'")

    if total_meanings_relocated == 0:
        print("✅ No misplaced word meanings found.")
    else:
        print(f"✅ Relocated {total_meanings_relocated} word meanings successfully.")
    
    print(f"Processed a total of {total_meanings_processed} meanings across all files.")

    # Step 3: Standardize and write the corrected data to the files.
    print("\n--- Phase 2: Standardizing all files by sorting alphabetically... ---")
    for level, data_dict in corrected_data.items():
        # Sort the dictionary items by key (the word) case-insensitively.
        sorted_items = sorted(data_dict.items(), key=lambda item: item[0].lower())
        
        # Create a new dictionary from the sorted items.
        standardized_dict = dict(sorted_items)
        
        output_path = OUTPUT_FOLDER / f"output_{level}.json"
        # Only write the file if it contains data, to avoid empty files.
        if standardized_dict:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(standardized_dict, f, ensure_ascii=False, indent=2)
            print(f"   - ✅ Wrote {output_path} with {len(standardized_dict)} sorted word entries.")
        elif output_path.exists():
            # If the file should now be empty, we remove it.
            output_path.unlink()
            print(f"   - 🗑️  Removed {output_path} as it is now empty.")


    print("\n--- Validator & Standardizer Finished Successfully ---")

if __name__ == "__main__":
    validate_and_standardize_files()