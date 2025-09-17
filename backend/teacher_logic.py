import random
from datetime import datetime, date
import data_manager
import report_manager

# --- MODIFIED: Configuration for the daily limit ---
DAILY_NEW_WORD_LIMIT = 100
HARD_WORD_THRESHOLD = 3 # Max number of wrongs in a day

def calculate_word_priority(stats, word_details):
    """
    Calculates a word's priority score based on multiple performance metrics.
    """
    right = stats.get('right', 0)
    wrong = stats.get('wrong', 0)
    total = stats.get('total_encountered', 0)
    
    if total == 0: return 100
    
    accuracy = right / total if total > 0 else 0
    accuracy_weight = (1 - accuracy) * 50
    mistake_weight = min(wrong * 5, 40)
    
    time_urgency = 0
    last_seen = stats.get('last_seen')
    if last_seen:
        try:
            days_since = (datetime.now() - datetime.fromisoformat(last_seen)).days
            time_urgency = min(days_since, 10)
        except (ValueError, TypeError): pass

    volatility_weight = 0
    history = stats.get('recent_history', [])
    if len(history) > 3:
        flips = 0
        for i in range(len(history) - 1):
            if history[i] != history[i+1]: flips += 1
        volatility_weight = min(flips * 7, 35)

    article_weakness_weight = 0
    if word_details.get('type') == 'Nomen':
        article_errors = stats.get('article_wrong', 0)
        noun_errors = stats.get('wrong', 0)
        total_errors = article_errors + noun_errors
        if total_errors > 0:
            in_correction_rate = article_errors / total_errors
            if in_correction_rate > 0.6:
                article_weakness_weight = 20
    
    unintuitive_word_boost = 10 if stats.get('failed_first_encounter', False) else 0

    # --- NEW: "Sticky Correction" Score Logic ---
    sticky_correction_weight = 0
    total_mistakes = stats.get('wrong', 0) + stats.get('article_wrong', 0)
    # This metric is only meaningful if the user has made several mistakes.
    if total_mistakes > 2:
        successful_fixes = stats.get('successful_corrections', 0)
        # Calculate the rate of successful correction following a mistake.
        sticky_rate = successful_fixes / total_mistakes
        
        # If the rate is low, the word is "stubborn" and needs more attention.
        # A word with a 0% sticky rate gets a full 30-point boost.
        # A word with a 40% sticky rate gets a (1 - 0.8) * 30 = 6-point boost.
        if sticky_rate < 0.5:
            sticky_correction_weight = (1 - (sticky_rate * 2)) * 30
    # --- END OF NEW LOGIC ---

    total_priority = (accuracy_weight + mistake_weight + time_urgency + 
                      volatility_weight + article_weakness_weight +
                      unintuitive_word_boost + sticky_correction_weight)
    return min(total_priority, 100)


def weighted_random_selection(words_with_priorities, count=5):
    """Selects unique words using weighted random selection without replacement."""
    if len(words_with_priorities) <= count:
        words = [w for w, p in words_with_priorities]
        random.shuffle(words)
        return words

    population = [item[0] for item in words_with_priorities]
    weights = [p for w, p in words_with_priorities]
    selected = []
    
    while len(selected) < count and population:
        if sum(weights) <= 0:
            remaining_needed = count - len(selected)
            if len(population) > 0:
                selected.extend(random.sample(population, k=min(remaining_needed, len(population))))
            break

        chosen = random.choices(population, weights=weights, k=1)[0]
        selected.append(chosen)
        
        idx = population.index(chosen)
        population.pop(idx)
        weights.pop(idx)
        
    return selected

def select_quiz_words(level, word_to_level_map):
    """
    Main logic for selecting words, factoring in all performance metrics.
    """
    all_word_details = {}
    all_repetition_stats = {}
    
    levels_to_load = data_manager.LEVELS if level == "mix" else [level]

    for lvl in levels_to_load:
        all_word_details.update(data_manager.load_output_words(lvl))
        all_repetition_stats.update(data_manager.load_repetition_stats(lvl))

    if not all_word_details: return []

    for word in all_word_details.keys():
        if word not in all_repetition_stats:
            all_repetition_stats[word] = data_manager.REPETITION_SCHEMA.copy()

    due_words = []
    today = date.today()
    for word, stats in all_repetition_stats.items():
        next_show_str = stats.get('next_show_date')
        is_due = not next_show_str or (datetime.fromisoformat(next_show_str).date() <= today if next_show_str else True)
        if is_due: due_words.append(word)

    report_data = report_manager.load_report_data()
    today_str = datetime.now().strftime('%Y-%m-%d')
    seen_today_by_level = report_data.get('daily_seen_words', {}).get(today_str, {})
    daily_wrong_counts = report_data.get('daily_wrong_counts', {}).get(today_str, {})
    
    candidate_pool = []
    for word in due_words:
        if daily_wrong_counts.get(word, 0) >= HARD_WORD_THRESHOLD: continue
        word_level = word_to_level_map.get(word)
        if not word_level: continue
        seen_words_for_this_level = seen_today_by_level.get(word_level, [])
        if word in seen_words_for_this_level: candidate_pool.append(word)
        elif len(seen_words_for_this_level) < DAILY_NEW_WORD_LIMIT: candidate_pool.append(word)

    if not candidate_pool: return []

    words_with_priorities = []
    for word in candidate_pool:
        if word in all_word_details:
            stats = all_repetition_stats[word]
            word_details = all_word_details[word]
            priority = calculate_word_priority(stats, word_details)
            words_with_priorities.append((word, priority))

    selected_word_keys = weighted_random_selection(words_with_priorities, 5)
    return [all_word_details[word] for word in selected_word_keys if word in all_word_details]