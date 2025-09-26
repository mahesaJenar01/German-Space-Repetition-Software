def update_reports_from_results(report_data, results, word_level_map, word_details_map):
    """
    Updates all performance report metrics based on a batch of quiz results.
    """
    today_str = report_data['today_str']

    # Ensure today's keys exist in the report object
    daily_seen = report_data.setdefault('daily_seen_words', {}).setdefault(today_str, {})
    daily_wrong_per_word = report_data.setdefault('daily_wrong_counts', {}).setdefault(today_str, {})
    daily_article_wrong_per_word = report_data.setdefault('daily_article_wrong_counts', {}).setdefault(today_str, {})
    daily_level_correct = report_data.setdefault('daily_level_correct_counts', {}).setdefault(today_str, {})
    daily_level_wrong = report_data.setdefault('daily_level_wrong_counts', {}).setdefault(today_str, {})
    daily_level_article_wrong = report_data.setdefault('daily_level_article_wrong_counts', {}).setdefault(today_str, {})
    category_performance = report_data.setdefault('category_performance', {})

    for result in results:
        item_key = result.get('word')
        if not item_key or '#' not in item_key:
            continue
            
        base_word, meaning_str = item_key.split('#', 1)
        
        # --- FIX #1: Determine level from the specific meaning object ---
        meanings_array = word_details_map.get(base_word)
        word_lvl = None
        word_details = None

        if meanings_array:
            word_details = next((m for m in meanings_array if m['meaning'] == meaning_str), None)
            if word_details and 'level' in word_details:
                word_lvl = word_details['level'].lower()
        
        if not word_lvl or not word_details:
            print(f"WARNING: Could not determine level/details for '{item_key}'. Skipping report update.")
            continue
        
        result_type = result.get('result_type')
        
        # --- FIX #2: Use ITEM_KEY for tracking unique words seen today ---
        seen_words_for_level = daily_seen.setdefault(word_lvl, [])
        if item_key not in seen_words_for_level:
            seen_words_for_level.append(item_key)

        word_type = word_details.get('type')
        if word_type:
            type_stats = category_performance.setdefault(word_type, {'right': 0, 'wrong': 0})
        
        if result_type == "PERFECT_MATCH":
            daily_level_correct[word_lvl] = daily_level_correct.get(word_lvl, 0) + 1
            if word_type:
                type_stats['right'] += 1
        
        elif result_type == "PARTIAL_MATCH_WRONG_ARTICLE":
            daily_level_article_wrong[word_lvl] = daily_level_article_wrong.get(word_lvl, 0) + 1
            
            # --- FIX #3: Use new flattened structure for article wrong counts ---
            daily_article_wrong_per_word[item_key] = daily_article_wrong_per_word.get(item_key, 0) + 1
            
            if word_type == 'Nomen':
                type_stats.setdefault('article_wrong', 0)
                type_stats['article_wrong'] += 1

        else: # NO_MATCH and any other non-perfect results
            daily_level_wrong[word_lvl] = daily_level_wrong.get(word_lvl, 0) + 1
            if word_type:
                type_stats['wrong'] += 1
            
            if result_type == 'NO_MATCH':
                # --- FIX #4: Use new flattened structure for NO_MATCH wrong counts ---
                daily_wrong_per_word[item_key] = daily_wrong_per_word.get(item_key, 0) + 1
                
    return report_data