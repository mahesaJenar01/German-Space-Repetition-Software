import React, { createContext, useContext } from 'react';

// Create the context with a default null value
const QuizContext = createContext(null);

/**
 * A custom hook to provide easy access to the QuizContext.
 * It ensures the hook is used within a QuizProvider.
 */
export const useQuizContext = () => {
  const context = useContext(QuizContext);
  if (!context) {
    throw new Error('useQuizContext must be used within a QuizManager provider');
  }
  return context;
};

export default QuizContext;