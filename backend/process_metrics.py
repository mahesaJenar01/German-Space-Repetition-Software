import os
import json
import re
import asyncio
import aiohttp
from pathlib import Path
from time import time
import logging
from dotenv import load_dotenv

# Load .env (OPENAI_API_KEY)
load_dotenv()

# --- NEW: Simplified Configuration ---
INPUT_FILE = Path("input.txt") # The single source of new words
OUTPUT_FOLDER = Path("output")
LEVELS = ["a1", "a2", "b1"] # We still need this to know which output files to check

# --- Unchanged Configuration ---
MODEL = "gpt-5-mini"
OPENAI_URL = "https://api.openai.com/v1/responses"
SYSTEM_RULES_PATH = Path("system_prompt.txt")
API_KEY = os.getenv("OPENAI_API_KEY")
RPM = 500
TPM = 200_000
MAX_CONCURRENT = 20
RETRY_LIMIT = 3

# Logger setup
LOG_FILE = Path("log_info.txt")
logging.basicConfig(
    filename=LOG_FILE, filemode="a", level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- Helper functions (load_system_prompt, load_output_json, etc. are mostly unchanged) ---
def load_system_prompt():
    if SYSTEM_RULES_PATH.exists():
        return SYSTEM_RULES_PATH.read_text(encoding="utf-8")
    return ""

def load_output_json(path: Path):
    if not path.exists(): return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text: return {}
    return json.loads(text)

def write_output_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"(\{(?:.|\s)*\})", text)
        if m:
            try: return json.loads(m.group(1))
            except Exception: pass
    return None

# ... RateLimiter, call_openai, etc. remain the same as before ...
class RateLimiter:
    def __init__(self, rpm):
        self.rpm = rpm
        self.tokens = rpm
        self.lock = asyncio.Lock()
        self._last_refill = time()
        self._refill_interval = 60.0

    async def acquire(self):
        while True:
            async with self.lock:
                now = time()
                elapsed = now - self._last_refill
                if elapsed >= self._refill_interval:
                    self.tokens = self.rpm
                    self._last_refill = now
                if self.tokens > 0:
                    self.tokens -= 1
                    return
            await asyncio.sleep(0.05)

async def call_openai(session, system_prompt, word, rl: RateLimiter, req_id: int):
    start_time = time()
    retries = 0
    await rl.acquire()
    prompt_user = (f"Produce a single valid JSON object for the German word: \"{word}\".\n" "Follow the vocabulary metrics schema. Return only valid JSON.")
    payload = {"model": MODEL, "input": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt_user}]}
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    for attempt in range(1, RETRY_LIMIT + 1):
        retries = attempt - 1
        try:
            async with session.post(OPENAI_URL, json=payload, headers=headers, timeout=60) as resp:
                text = await resp.text()
                runtime = time() - start_time
                if resp.status >= 400:
                    if resp.status in (429, 500, 502, 503, 504) and attempt < RETRY_LIMIT:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    logging.error(f"Word={word} ID={req_id} FAILED status={resp.status} runtime={runtime:.2f}s retries={retries}")
                    return None
                data = await resp.json()
                output_text = ""
                if isinstance(data.get("output"), list):
                    for item in data["output"]:
                        for c in item.get("content", []):
                            if "text" in c: output_text += c["text"]
                            elif c.get("payload", {}).get("text"): output_text += c["payload"]["text"]
                elif data.get("output_text"): output_text = data["output_text"]
                obj = extract_json(output_text)
                if obj is None:
                    logging.error(f"Word={word} ID={req_id} JSON_PARSE_FAILED runtime={runtime:.2f}s retries={retries}")
                    return None
                logging.info(f"Word={word} ID={req_id} SUCCESS runtime={runtime:.2f}s retries={retries}")
                return obj
        except Exception as e:
            if attempt < RETRY_LIMIT:
                await asyncio.sleep(1)
                continue
            logging.error(f"Word={word} ID={req_id} EXCEPTION {str(e)} runtime={runtime:.2f}s retries={retries}")
            return None
    return None

# --- NEW: Main processing logic ---
async def main():
    if not API_KEY:
        print("ERROR: Set OPENAI_API_KEY in .env or env variables.")
        return

    system_prompt = load_system_prompt()
    if not system_prompt or '"level":' not in system_prompt:
        print("⚠️  WARNING: Your system_prompt.txt might be missing instructions for the 'level' property!")

    # Step 1: Load all words that ALREADY exist in ANY output file
    print("--- Loading existing vocabulary ---")
    existing_words = set()
    all_output_data = {}
    for level in LEVELS:
        path = OUTPUT_FOLDER / f"output_{level}.json"
        data = load_output_json(path)
        all_output_data[level] = data
        for item in data.values():
            if item and 'word' in item:
                existing_words.add(item['word'].strip().lower())
    print(f"Found {len(existing_words)} unique words in total across all output files.")

    # Step 2: Read the single input file and find words that need processing
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found at '{INPUT_FILE}'. Please create it.")
        return
        
    # Handles words separated by commas or newlines
    input_text = INPUT_FILE.read_text(encoding="utf-8").replace('\n', ',')
    words_to_process = [w.strip() for w in input_text.split(',') if w.strip()]
    
    missing_words = [
        word for word in words_to_process if word.strip().lower() not in existing_words
    ]

    if not missing_words:
        print("\n--- No new words to process. All words from input.txt already exist. ---")
        return

    print(f"\n--- Found {len(missing_words)} new words to process -> calling API... ---")

    # Step 3: Call API for the missing words
    rl = RateLimiter(RPM) # Rate limiter setup
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = []
    
    async def worker(word):
        async with semaphore:
            return await call_openai(session, system_prompt, word, rl, 0)

    async with aiohttp.ClientSession() as session:
        tasks = [worker(word) for word in missing_words]
        results = await asyncio.gather(*tasks)

    # Step 4: Process and sort the results into the correct files
    print("\n--- Processing and sorting AI results ---")
    changed_files = set()
    for word_obj in results:
        if word_obj is None or 'level' not in word_obj or 'word' not in word_obj:
            print(f"   - ⚠️  Skipping invalid result from AI: {word_obj}")
            continue

        level = word_obj['level'].strip().lower()
        word_str = word_obj['word'].strip()

        if level not in LEVELS:
            print(f"   - ⚠️  Skipping word '{word_str}' due to invalid level from AI: '{level}'")
            continue
            
        # Add the word to the correct in-memory dictionary
        target_dict = all_output_data[level]
        next_id = max([int(k) for k in target_dict.keys()] or [0]) + 1
        target_dict[str(next_id)] = word_obj
        changed_files.add(level)
        print(f"   - ✅ Added '{word_str}' to {level.upper()} vocabulary.")

    # Step 5: Save all modified files
    if not changed_files:
        print("\n--- No valid new words were generated by the AI. ---")
    else:
        print("\n--- Saving updated output files... ---")
        for level in sorted(list(changed_files)):
            path = OUTPUT_FOLDER / f"output_{level}.json"
            write_output_json(path, all_output_data[level])
            print(f"   - Saved {path}")
            
    print("\n--- Processing finished. ---")


if __name__ == "__main__":
    asyncio.run(main())