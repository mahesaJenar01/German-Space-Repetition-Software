def update_reports_from_results(report_data, results, word_level_map, word_details_map):
    """
    Updates all performance report metrics based on a batch of quiz results.
    """
    today_str = report_data['today_str']

    # Ensure today's keys exist in the report object
    daily_seen = report_data.setdefault('daily_seen_words', {}).setdefault(today_str, {})
    daily_wrong_per_word = report_data.setdefault('daily_wrong_counts', {}).setdefault(today_str, {})
    # --- NEW: Initialize our new specific word counter ---
    daily_article_wrong_per_word = report_data.setdefault('daily_article_wrong_counts', {}).setdefault(today_str, {})
    daily_level_correct = report_data.setdefault('daily_level_correct_counts', {}).setdefault(today_str, {})
    daily_level_wrong = report_data.setdefault('daily_level_wrong_counts', {}).setdefault(today_str, {})
    daily_level_article_wrong = report_data.setdefault('daily_level_article_wrong_counts', {}).setdefault(today_str, {})
    category_performance = report_data.setdefault('category_performance', {})

    for result in results:
        word = result.get('word')
        word_lvl = word_level_map.get(word)
        word_details = word_details_map.get(word)
        if not word_lvl or not word_details:
            continue

        result_type = result.get('result_type')
        
        # Add the word to the list of unique words seen today for its level.
        seen_words_for_level = daily_seen.setdefault(word_lvl, [])
        if word not in seen_words_for_level:
            seen_words_for_level.append(word)

        # Update category performance (Nomen, Verb, etc.)
        word_type = word_details.get('type')
        if word_type:
            type_stats = category_performance.setdefault(word_type, {'right': 0, 'wrong': 0})
        
        # --- REFINED LOGIC TO DIFFERENTIATE ERROR TYPES ---
        if result_type == "PERFECT_MATCH":
            daily_level_correct[word_lvl] = daily_level_correct.get(word_lvl, 0) + 1
            if word_type:
                type_stats['right'] += 1
        
        elif result_type == "PARTIAL_MATCH_WRONG_ARTICLE":
            # This is a partial error, so we use the new dedicated counters.
            daily_level_article_wrong[word_lvl] = daily_level_article_wrong.get(word_lvl, 0) + 1
            # --- NEW: Track the specific word with the article error ---
            daily_article_wrong_per_word[word] = daily_article_wrong_per_word.get(word, 0) + 1
            
            if word_type == 'Nomen':
                # Dynamically add the article_wrong counter for nouns
                type_stats.setdefault('article_wrong', 0)
                type_stats['article_wrong'] += 1

        else: # This now correctly covers NO_MATCH and any other future non-perfect results
            daily_level_wrong[word_lvl] = daily_level_wrong.get(word_lvl, 0) + 1
            if word_type:
                type_stats['wrong'] += 1
            
            # Only a complete NO_MATCH should count towards the "hard word" threshold
            if result_type == 'NO_MATCH':
                daily_wrong_per_word[word] = daily_wrong_per_word.get(word, 0) + 1
                
    return report_data