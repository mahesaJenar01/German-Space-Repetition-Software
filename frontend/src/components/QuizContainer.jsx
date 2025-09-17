import React from 'react';
import QuizItem from './QuizItem';
import '../styles/QuizContainer.css';
import { useQuizContext } from '../context/QuizContext';

const QuizContainer = () => {
  // Get the quiz items directly from our context
  const { quizItems } = useQuizContext();

  return (
    <div className="quiz-container">
      {quizItems.map((item, index) => (
        <QuizItem
          key={item.key}
          item={item}
          autoFocus={index === 0}
        />
      ))}
    </div>
  );
};

export default QuizContainer;