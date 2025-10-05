import React from 'react';
import { useQuizContext } from '../context/QuizContext';

const QuizInput = ({ item, autoFocus }) => {
    const {
        inputs,
        results,
        isSubmitted,
        inputRefs,
        handleInputChange,
        focusedItemKey,
        randomExamples,
        handleFocus,
        handleBlur,
    } = useQuizContext();

    const inputValue = inputs[item.key] || '';
    const result = results[item.key];

    const getInputClassName = () => {
        if (isSubmitted) {
            if (result === 'PERFECT_MATCH') return 'input-correct';
            if (result === 'NO_MATCH') return 'input-wrong';
            if (result && result.startsWith('PARTIAL_MATCH')) return 'input-partial';
        }
        const hasArticleErrorHistory = item.article_wrong > 0;
        if (item.direction === 'meaningToWord' && hasArticleErrorHistory) {
            return 'input-article-warning';
        }
        return '';
    };

    const renderExample = () => {
        // Always render the element to prevent layout shift
        let exampleToShow = '\u00A0'; // Non-breaking space
        
        if (focusedItemKey === item.key && !isSubmitted) {
            const exampleString = randomExamples[item.key];
            if (exampleString) {
                if (item.direction === 'meaningToWord') {
                    const match = exampleString.match(/\((.*?)\)/);
                    exampleToShow = match ? match[1] : '\u00A0';
                } else {
                    exampleToShow = exampleString.replace(/\s*\(.*?\)\s*/, '').trim() || '\u00A0';
                }
            }
        }
        return <small className="quiz-example">{exampleToShow}</small>;
    };

    return (
        // Use a Fragment as the container is handled by QuizItem
        <>
            <input
                type="text"
                value={inputValue}
                onChange={(e) => handleInputChange(item.key, e.target.value)}
                disabled={isSubmitted}
                ref={el => inputRefs.current[item.key] = el}
                className={getInputClassName()}
                placeholder="Type the answer..."
                // --- THIS IS THE FIX ---
                // Only apply autoFocus if the quiz is not submitted.
                autoFocus={autoFocus && !isSubmitted}
                onFocus={() => handleFocus(item.key)}
                onBlur={handleBlur}
            />
            {renderExample()}
        </>
    );
};

export default QuizInput;