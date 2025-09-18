import random
from datetime import datetime, date
import data_manager
import report_manager

# Import individual metric calculators
from .priority_metrics import (
    accuracy,
    article_weakness,
    recency,
    stickiness,
    volatility,
    confusion,
)

# Configuration
DAILY_NEW_WORD_LIMIT = 100
HARD_WORD_THRESHOLD = 3
RIVAL_CONFUSION_THRESHOLD = 3 # <-- NEW: Min confusion count to trigger injection

def calculate_word_priority(stats, word_details):
    """
    Aggregates scores from various metrics to determine a word's final priority.
    The role of this function is to orchestrate, not to calculate.
    """
    first_encounter_boost = 10 if stats.get('failed_first_encounter', False) else 0
    total_priority = (
        accuracy.calculate_accuracy_score(stats) +
        recency.calculate_recency_score(stats) +
        volatility.calculate_volatility_score(stats) +
        article_weakness.calculate_article_weakness_score(stats, word_details) +
        stickiness.calculate_stickiness_score(stats) +
        confusion.calculate_confusion_score(stats) +
        first_encounter_boost
    )
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
    Main logic for selecting words, now with "Rival Word" injection.
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
            all_repetition_stats[word] = data_manager.get_new_repetition_schema()

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
            stats = all_repetition_stats.get(word, {})
            word_details = all_word_details[word]
            priority = calculate_word_priority(stats, word_details)
            words_with_priorities.append((word, priority))

    # --- RIVAL WORD INJECTION LOGIC ---
    initial_selection_keys = weighted_random_selection(words_with_priorities, 5)
    final_selection_keys = list(initial_selection_keys) # Make a mutable copy
    rival_pair = None

    # Sort the initial selection by priority to find the weakest link
    initial_selection_with_priority = sorted(
        [item for item in words_with_priorities if item[0] in initial_selection_keys],
        key=lambda x: x[1]
    )

    for word_key, priority in reversed(initial_selection_with_priority): # Check high-priority words first
        stats = all_repetition_stats.get(word_key, {})
        confusions = stats.get('confused_with', {})
        
        # Find the most confused rival word that meets the threshold
        for rival_key, count in confusions.items():
            if count >= RIVAL_CONFUSION_THRESHOLD and rival_key in due_words and rival_key not in final_selection_keys:
                # Found a rival to inject!
                word_to_replace = initial_selection_with_priority[0][0] # The one with lowest priority
                
                # Make sure we don't replace the word we are checking against
                if word_to_replace == word_key: 
                    if len(initial_selection_with_priority) > 1:
                        word_to_replace = initial_selection_with_priority[1][0]
                    else:
                        continue # Cannot replace if only one word

                # Perform the replacement
                final_selection_keys[final_selection_keys.index(word_to_replace)] = rival_key
                rival_pair = (word_key, rival_key)
                break # Inject only one pair per quiz
        if rival_pair:
            break

    # Prepare final word details, adding rival group info if applicable
    final_word_details = []
    for word_key in final_selection_keys:
        if word_key in all_word_details:
            detail = all_word_details[word_key].copy()
            if rival_pair and word_key in rival_pair:
                detail['rival_group'] = 1 # Mark this word as part of a rival pair
            final_word_details.append(detail)
            
    return final_word_details