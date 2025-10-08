import React, { useState, useEffect } from 'react';
import QuizContext from '../context/QuizContext';
import * as api from '../services/api';
import { useQuizStore } from '../store/quizStore';

const SESSION_KEY_PREFIX = 'vocabularyQuizSession_';

const QuizManager = ({ children, quizItems }) => {
  // State for this specific quiz instance (inputs, results) remains local
  const [inputs, setInputs] = useState({});
  const [results, setResults] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const inputRefs = React.useRef({});
  const [focusedItemKey, setFocusedItemKey] = useState(null);
  const [randomExamples, setRandomExamples] = useState({});
  
  // Get actions and global state from the store
  const {
    level,
    setFeedback,
    refreshStats,
    setIsQuizCompleted,
    showWordDetail,
    showHint,
    hideHint
  } = useQuizStore();

  // --- THIS IS THE FIX ---
  // This effect resets the quiz state. It should ONLY run when a genuinely
  // new set of words is loaded, not when a minor property (like 'is_starred') changes.
  // We determine this by watching the key of the *first* item in the quiz.
  useEffect(() => {
    if (quizItems.length > 0) {
      const initialInputs = quizItems.reduce((acc, item) => ({ ...acc, [item.key]: '' }), {});
      setInputs(initialInputs);
      setResults({});
      setIsSubmitted(false);

      const examples = {};
      quizItems.forEach(item => {
        const exampleString = item.fullDetails?.example || '';
        if (exampleString) {
          const allExamples = exampleString.split(';').map(e => e.trim()).filter(Boolean);
          if (allExamples.length > 0) {
            const randomIndex = Math.floor(Math.random() * allExamples.length);
            examples[item.key] = allExamples[randomIndex];
          }
        }
      });
      setRandomExamples(examples);
    }
  }, [quizItems[0]?.key]); // The dependency is now the key of the first item

  const handleInputChange = (key, value) => {
    setInputs(prev => ({ ...prev, [key]: value }));
  };

  const checkAnswers = async () => {
    setFocusedItemKey(null);

    const newResults = {};
    const resultsPayload = [];

    quizItems.forEach(item => {
      const wordDetail = item.fullDetails; 
      const correctAnswersSet = new Set(item.correctAnswers);
      
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
      
      const sessionKey = `${SESSION_KEY_PREFIX}${level}`;
      sessionStorage.removeItem(sessionKey);
      
      refreshStats(); 
      setIsQuizCompleted(true);
    } catch (error){
      console.error("Failed to update stats:", error);
    }
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !isSubmitted) {
      e.stopPropagation();

      const allFilled = quizItems.length > 0 && quizItems.every(item => (inputs[item.key] || "").trim() !== '');
      if (allFilled || quizItems.length === 0) {
        checkAnswers();
      } else {
        setFeedback('Please fill in all the answers before submitting.');
      }
    }
  };

  const handleFocus = (key) => setFocusedItemKey(key);
  const handleBlur = () => setFocusedItemKey(null);

  const contextValue = {
    quizItems,
    inputs,
    results,
    isSubmitted,
    inputRefs,
    handleInputChange,
    onWordClick: showWordDetail,
    onShowHint: showHint,
    onHideHint: hideHint,
    focusedItemKey,
    randomExamples,
    handleFocus,
    handleBlur,
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