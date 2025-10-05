import React from 'react';
import { useQuizContext } from '../context/QuizContext';

const QuizFeedback = ({ item }) => {
    const { inputs, results, isSubmitted } = useQuizContext();

    if (!isSubmitted) {
        return null;
    }

    const result = results[item.key];
    const inputValue = inputs[item.key] || '';

    switch (result) {
        case 'NO_MATCH':
            return <div className="correct-answer">Correct answer: {item.displayAnswer}</div>;
        case 'PARTIAL_MATCH_WRONG_ARTICLE': {
            const userInput = inputValue.trim();
            const userArticle = (userInput.match(/^(der|die|das)/i) || [''])[0];
            const userNoun = userInput.replace(/^(der|die|das)\s+/i, '');
            const correctArticle = (item.displayAnswer.match(/^(Der|Die|Das)/i) || [''])[0];
            return (
                <div className="feedback-partial">
                    <span className="feedback-text">Noun correct! The article is <strong>{correctArticle}</strong>.</span>
                    <div className="feedback-highlight">
                        Your answer: <span className="wrong-part">{userArticle}</span> <span className="correct-part">{userNoun}</span>
                    </div>
                </div>
            );
        }
        case 'PARTIAL_MATCH_MISSING_ARTICLE': {
            const correctArticle = (item.displayAnswer.match(/^(Der|Die|Das)/i) || [''])[0];
            return (
                <div className="feedback-partial">
                    <span className="feedback-text">Noun correct, but you missed the article: <strong>{correctArticle}</strong></span>
                </div>
            );
        }
        default:
            return null;
    }
};

export default QuizFeedback;