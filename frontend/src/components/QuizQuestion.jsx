import React from 'react';
import { useQuizContext } from '../context/QuizContext';

// This logic is now co-located with the component that uses it.
const getRegisterClassName = (registerValue) => {
  const numValue = parseInt(registerValue, 10);
  if (!isNaN(numValue)) {
    if (numValue <= 3) return 'register-informal';
    if (numValue <= 5) return 'register-colloquial';
    if (numValue >= 8) return 'register-formal';
  } else if (typeof registerValue === 'string') {
    const lowerCaseValue = registerValue.toLowerCase();
    if (lowerCaseValue.includes('slang') || lowerCaseValue.includes('informal') || lowerCaseValue.includes('umgangssprachlich')) {
      return 'register-colloquial';
    }
    if (lowerCaseValue.includes('formal') || lowerCaseValue.includes('offiziell') || lowerCaseValue.includes('förmlich')) {
      return 'register-formal';
    }
  }
  return '';
};


const QuizQuestion = ({ item, isSubmitted, isHintable }) => {
    const { onWordClick, onShowHint, onHideHint } = useQuizContext();

    const handleWordClick = () => {
        if (isSubmitted) {
            onWordClick(item.fullDetails);
        }
    };

    const getWordClassName = () => {
        const registerClass = !isSubmitted ? getRegisterClassName(item.fullDetails?.register) : '';
        if (isSubmitted) return `word clickable ${registerClass}`;
        if (isHintable) return `word hintable ${registerClass}`;
        return `word ${registerClass}`;
    };

    return (
        <span
            className={getWordClassName().trim()}
            onClick={handleWordClick}
            onMouseEnter={(e) => isHintable && onShowHint(item.fullDetails, e)}
            onMouseLeave={() => isHintable && onHideHint()}
        >
            {item.question}
        </span>
    );
};

export default QuizQuestion;