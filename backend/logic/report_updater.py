def update_reports_from_results(report_data, results, word_level_map, word_details_map):
    """
    Updates all performance report metrics based on a batch of quiz results.
    """
    today_str = report_data['today_str']

    # Ensure today's keys exist in the report object
    daily_seen = report_data.setdefault('daily_seen_words', {}).setdefault(today_str, {})
    daily_wrong_per_word = report_data.setdefault('daily_wrong_counts', {}).setdefault(today_str, {})
    daily_level_correct = report_data.setdefault('daily_level_correct_counts', {}).setdefault(today_str, {})
    daily_level_wrong = report_data.setdefault('daily_level_wrong_counts', {}).setdefault(today_str, {})
    category_performance = report_data.setdefault('category_performance', {})

    for result in results:
        word = result.get('word')
        word_lvl = word_level_map.get(word)
        word_details = word_details_map.get(word)
        if not word_lvl or not word_details:
            continue

        result_type = result.get('result_type')
        is_correct = result_type == "PERFECT_MATCH"

        # --- THIS IS THE FIX ---
        # Add the word to the list of unique words seen today for its level.
        seen_words_for_level = daily_seen.setdefault(word_lvl, [])
        if word not in seen_words_for_level:
            seen_words_for_level.append(word)
        # --- END OF FIX ---

        # Update category performance (Nomen, Verb, etc.)
        word_type = word_details.get('type')
        if word_type:
            type_stats = category_performance.setdefault(word_type, {'right': 0, 'wrong': 0})
            if is_correct:
                type_stats['right'] += 1
            else:
                type_stats['wrong'] += 1
        
        # Update daily counts
        if is_correct:
            daily_level_correct[word_lvl] = daily_level_correct.get(word_lvl, 0) + 1
        else: # Both partial and no_match are considered "wrong" for reporting
            daily_level_wrong[word_lvl] = daily_level_wrong.get(word_lvl, 0) + 1
            if result_type == 'NO_MATCH':
                daily_wrong_per_word[word] = daily_wrong_per_word.get(word, 0) + 1

    return report_data