import React, { useState, useEffect } from 'react';
import QuizContext from '../context/QuizContext';
import * as api from '../services/api';

/**
 * QuizManager is a context provider that encapsulates all the logic and state
 * for an active quiz session.
 */
const QuizManager = ({ children, level, quizItems, allWords, onQuizSubmit, setFeedback, refreshStats, onWordClick, onShowHint, onHideHint }) => {
  const [inputs, setInputs] = useState({});
  const [results, setResults] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const inputRefs = React.useRef({});

  // Initialize or clear inputs when a new set of quiz items is provided
  useEffect(() => {
    if (quizItems.length > 0) {
      const initialInputs = quizItems.reduce((acc, item) => ({ ...acc, [item.key]: '' }), {});
      setInputs(initialInputs);
      setResults({});
      setIsSubmitted(false);
    }
  }, [quizItems]);

  const handleInputChange = (key, value) => {
    setInputs(prev => ({ ...prev, [key]: value }));
  };

  const checkAnswers = async () => {
    const newResults = {};
    const resultsPayload = [];

    quizItems.forEach(item => {
      const correctAnswersSet = new Set(item.correctAnswers);
      const wordDetail = allWords.find(w => w.word === item.key);
      let userAnswer = (inputs[item.key] || "").trim();
      const isNounTest = wordDetail && wordDetail.type === 'Nomen' && item.direction === 'meaningToWord';
      if (!isNounTest) userAnswer = userAnswer.toLowerCase();

      let resultType = 'NO_MATCH';
      if (userAnswer.split(';').map(p => p.trim()).filter(Boolean).some(part => correctAnswersSet.has(part))) {
        resultType = 'PERFECT_MATCH';
      } else if (isNounTest) {
        const userNoun = userAnswer.replace(/^(der|die|das)\s+/i, '');
        if (correctAnswersSet.has(userNoun)) {
          resultType = userAnswer.match(/^(der|die|das)/i) ? 'PARTIAL_MATCH_WRONG_ARTICLE' : 'PARTIAL_MATCH_MISSING_ARTICLE';
        }
      }
      newResults[item.key] = resultType;
      resultsPayload.push({
        word: item.key,
        result_type: resultType,
        user_answer: userAnswer,
        direction: item.direction,
      });
    });

    setResults(newResults);
    setIsSubmitted(true);
    setFeedback('Press Enter to continue to the next quiz.');
    
    try {
      await api.updateWordStats(level, resultsPayload);
      refreshStats(); // Refresh the stats in the header
      onQuizSubmit();   // Notify App component that submission is complete
    } catch (error){
      console.error("Failed to update stats:", error);
    }
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !isSubmitted) {
      const allFilled = quizItems.length > 0 && quizItems.every(item => (inputs[item.key] || "").trim() !== '');
      if (allFilled || quizItems.length === 0) {
        checkAnswers();
      } else {
        setFeedback('Please fill in all the answers before submitting.');
      }
    }
  };

  // The value provided to all consumer components
  const contextValue = {
    quizItems,
    allWords,
    inputs,
    results,
    isSubmitted,
    inputRefs,
    handleInputChange,
    onWordClick,
    onShowHint,
    onHideHint,
  };

  return (
    <QuizContext.Provider value={contextValue}>
      <div onKeyDown={handleKeyDown}>
        {children}
      </div>
    </QuizContext.Provider>
  );
};

export default QuizManager;