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
    volatility
)

def calculate_item_priority(stats, meaning_details):
    """
    Aggregates scores from various metrics to determine a specific item's final priority.
    """
    first_encounter_boost = 10 if stats.get('failed_first_encounter', False) else 0
    total_priority = (
        accuracy.calculate_accuracy_score(stats) +
        recency.calculate_recency_score(stats) +
        volatility.calculate_volatility_score(stats) +
        article_weakness.calculate_article_weakness_score(stats, meaning_details) +
        stickiness.calculate_stickiness_score(stats) +
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
    Main logic for selecting words. This version strictly enforces the daily new word limit per level.
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
    # This dictionary contains { "a1": ["word1#meaningA"], "b1": ["word2#meaningB"] }
    seen_today_by_level_item_keys = report_data.get('daily_seen_words', {}).get(today_str, {})
    
    # --- THIS IS THE FIX ---
    # Create a single set of all item_keys seen today, regardless of level, for efficient lookup.
    all_seen_item_keys_today = set()
    for item_keys in seen_today_by_level_item_keys.values():
        all_seen_item_keys_today.update(item_keys)

    # 1. Separate all due items into two groups: those already seen today (reviews)
    # and those not yet seen today (potential new words). This is now based on ITEM_KEY.
    review_items = []
    new_items_by_level = {lvl: [] for lvl in levels_to_load}

    for item in due_items:
        item_level = word_to_level_map.get(item["base_word"])
        if not item_level or item_level not in levels_to_load:
            continue

        if item["item_key"] in all_seen_item_keys_today:
            review_items.append(item)
        else:
            new_items_by_level[item_level].append(item)

    # 2. Build the final selection, prioritizing reviews and respecting the new word limit.
    final_selection = []
    final_selection.extend(review_items) # All review items are always eligible
    
    # In 'mix' mode, we might take words from multiple levels.
    for lvl in levels_to_load:
        new_items_for_this_level = new_items_by_level[lvl]
        if not new_items_for_this_level:
            continue
            
        # Determine how many new ITEM_KEYS we are allowed to introduce for this level.
        # The count is now based on the specific item_keys seen today.
        seen_count_for_level = len(seen_today_by_level_item_keys.get(lvl, []))
        new_word_slots = data_manager.DAILY_NEW_WORD_LIMIT - seen_count_for_level
        
        if new_word_slots > 0:
            # We have room for new items. Calculate their priorities.
            new_items_with_priorities = [
                (item, calculate_item_priority(all_repetition_stats.get(item["item_key"], {}), item["details"]))
                for item in new_items_for_this_level
            ]

            num_new_to_select = min(new_word_slots, len(new_items_with_priorities))
            selected_new = weighted_random_selection(new_items_with_priorities, num_new_to_select)
            final_selection.extend(selected_new)
    # --- END OF FIX ---


    # 3. Trim the final pool to the quiz size (5) and format for the frontend.
    final_selection_with_priorities = [
        (item, calculate_item_priority(all_repetition_stats.get(item["item_key"], {}), item["details"]))
        for item in final_selection
    ]
    
    final_selection_with_priorities.sort(key=lambda x: x[1], reverse=True)

    quiz_items = weighted_random_selection(final_selection_with_priorities, 5)

    final_quiz_details = []
    for item in quiz_items:
        detail = item["details"].copy()
        detail['item_key'] = item['item_key']
        final_quiz_details.append(detail)
            
    return {"quiz_words": final_quiz_details, "session_info": session_info}