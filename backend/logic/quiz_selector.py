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
RIVAL_CONFUSION_THRESHOLD = 3

def calculate_item_priority(stats, meaning_details):
    """
    Aggregates scores from various metrics to determine a specific item's final priority.
    The role of this function is to orchestrate, not to calculate.
    """
    first_encounter_boost = 10 if stats.get('failed_first_encounter', False) else 0
    total_priority = (
        accuracy.calculate_accuracy_score(stats) +
        recency.calculate_recency_score(stats) +
        volatility.calculate_volatility_score(stats) +
        article_weakness.calculate_article_weakness_score(stats, meaning_details) +
        stickiness.calculate_stickiness_score(stats) +
        confusion.calculate_confusion_score(stats) +
        first_encounter_boost
    )
    return min(total_priority, 100)


def weighted_random_selection(items_with_priorities, count=5):
    """Selects unique items using weighted random selection without replacement."""
    if len(items_with_priorities) <= count:
        items = [item for item, p in items_with_priorities]
        random.shuffle(items)
        return items

    population = [item[0] for item in items_with_priorities]
    weights = [p for w, p in items_with_priorities]
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
    Main logic for selecting words, now aware of individual meanings.
    It returns both the specific meaning objects for the quiz and session metadata.
    """
    all_word_details_map = {}
    all_repetition_stats = {}
    
    levels_to_load = data_manager.LEVELS if level == "mix" else [level]

    for lvl in levels_to_load:
        all_word_details_map.update(data_manager.load_output_words(lvl))
        all_repetition_stats.update(data_manager.load_repetition_stats(lvl))

    session_info = {
        "daily_word_limit": data_manager.DAILY_NEW_WORD_LIMIT,
        "total_words_in_level": len(all_word_details_map),
        "mastery_goal": data_manager.MASTERY_GOAL,
        "failure_threshold": data_manager.FAILURE_THRESHOLD,
    }

    if not all_word_details_map:
        return {"quiz_words": [], "session_info": session_info}

    all_learnable_items = []
    for base_word, meanings_array in all_word_details_map.items():
        for meaning_obj in meanings_array:
            item_key = f"{meaning_obj['word']}#{meaning_obj['meaning']}"
            all_learnable_items.append({
                "item_key": item_key,
                "base_word": base_word,
                "details": meaning_obj
            })

    due_items = []
    today = date.today()
    for item in all_learnable_items:
        stats = all_repetition_stats.get(item["item_key"], {})
        next_show_str = stats.get('next_show_date')
        is_due = not next_show_str or (datetime.fromisoformat(next_show_str).date() <= today if next_show_str else True)
        if is_due:
            due_items.append(item)

    report_data = report_manager.load_report_data()
    today_str = datetime.now().strftime('%Y-%m-%d')
    seen_today_by_level = report_data.get('daily_seen_words', {}).get(today_str, {})
    
    candidate_pool = []
    for item in due_items:
        word_level = word_to_level_map.get(item["base_word"])
        if not word_level: continue
        
        seen_words_for_this_level = seen_today_by_level.get(word_level, [])
        if item["base_word"] in seen_words_for_this_level:
            candidate_pool.append(item)
        elif len(seen_words_for_this_level) < data_manager.DAILY_NEW_WORD_LIMIT:
            candidate_pool.append(item)

    if not candidate_pool:
        return {"quiz_words": [], "session_info": session_info}
    
    items_with_priorities = []
    for item in candidate_pool:
        stats = all_repetition_stats.get(item["item_key"], data_manager.get_new_repetition_schema())
        priority = calculate_item_priority(stats, item["details"])
        items_with_priorities.append((item, priority))

    initial_selection = weighted_random_selection(items_with_priorities, 5)
    final_selection_items = list(initial_selection)
    rival_pair_bases = None

    initial_selection_with_priority = sorted(
        [item for item in items_with_priorities if item[0] in initial_selection],
        key=lambda x: x[1]
    )

    # --- Rival Injection Logic (CORRECTED) ---
    for selected_item, priority in reversed(initial_selection_with_priority):
        base_word_A = selected_item["base_word"]
        stats_A = all_repetition_stats.get(selected_item["item_key"], {})
        confusions = stats_A.get('confused_with', {})
        
        for rival_base_B, count in confusions.items():
            if rival_base_B not in word_to_level_map: continue
            
            # --- THIS IS THE FIX: Reintroduce the nuanced trigger logic ---
            word_A_level = word_to_level_map.get(base_word_A)
            rival_B_level = word_to_level_map.get(rival_base_B)
            if not word_A_level or not rival_B_level: continue

            is_same_level = word_A_level == rival_B_level
            
            # Trigger if count > 0 AND (they are same level OR the count is high)
            should_trigger = count > 0 and (is_same_level or count >= RIVAL_CONFUSION_THRESHOLD)
            # --- END OF FIX ---

            is_rival_already_present = any(item['base_word'] == rival_base_B for item in final_selection_items)

            if should_trigger and rival_base_B in all_word_details_map and not is_rival_already_present:
                item_to_replace = initial_selection_with_priority[0][0]
                
                if item_to_replace['base_word'] == base_word_A: 
                    if len(initial_selection_with_priority) > 1:
                        item_to_replace = initial_selection_with_priority[1][0]
                    else:
                        continue

                rival_meanings_array = all_word_details_map[rival_base_B]
                if rival_meanings_array:
                    rival_meaning_obj = rival_meanings_array[0]
                    rival_item_key = f"{rival_meaning_obj['word']}#{rival_meaning_obj['meaning']}"
                    rival_item_to_inject = {
                        "item_key": rival_item_key,
                        "base_word": rival_base_B,
                        "details": rival_meaning_obj
                    }
                    
                    replacement_index = final_selection_items.index(item_to_replace)
                    final_selection_items[replacement_index] = rival_item_to_inject
                    
                    rival_pair_bases = (base_word_A, rival_base_B)
                    print(f"Injecting rival '{rival_base_B}' for '{base_word_A}'. Same-level: {is_same_level}")
                    break
        if rival_pair_bases:
            break

    final_quiz_details = []
    for item in final_selection_items:
        detail = item["details"].copy()
        detail['item_key'] = item['item_key']
        if rival_pair_bases and item["base_word"] in rival_pair_bases:
            detail['rival_group'] = 1 
        final_quiz_details.append(detail)
            
    return {"quiz_words": final_quiz_details, "session_info": session_info}