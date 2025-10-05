import React from 'react';
import '../styles/QuizItem.css';
import { useQuizContext } from '../context/QuizContext';
import QuizQuestion from './QuizQuestion';
import QuizInput from './QuizInput';
import QuizFeedback from './QuizFeedback';

const QuizItem = ({ item, autoFocus }) => {
  const { isSubmitted } = useQuizContext();

  const isHintable = !isSubmitted && item.direction === 'meaningToWord';

  return (
    <div className="quiz-item" key={item.key}>
      <QuizQuestion 
        item={item} 
        isSubmitted={isSubmitted} 
        isHintable={isHintable} 
      />
      {/* The input column now holds the input and its feedback */}
      <div className="input-container">
        <QuizInput item={item} autoFocus={autoFocus} />
        <QuizFeedback item={item} />
      </div>
    </div>
  );
};

export default QuizItem;