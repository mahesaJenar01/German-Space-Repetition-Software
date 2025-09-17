import React from 'react';
import QuizItem from './QuizItem';
import '../styles/QuizContainer.css';

const QuizContainer = ({ quizItems, inputs, handleInputChange, isSubmitted, results, inputRefs, onWordClick, onShowHint, onHideHint }) => {
  return (
    <div className="quiz-container">
      {quizItems.map((item, index) => (
        <QuizItem
          key={item.key}
          item={item}
          inputValue={inputs[item.key] || ''}
          onInputChange={handleInputChange}
          isSubmitted={isSubmitted}
          result={results[item.key]}
          inputRef={el => inputRefs.current[index] = el}
          autoFocus={index === 0}
          onWordClick={onWordClick}
          onShowHint={onShowHint} /* --- NEW: Pass handler down --- */
          onHideHint={onHideHint} /* --- NEW: Pass handler down --- */
        />
      ))}
    </div>
  );
};

export default QuizContainer;