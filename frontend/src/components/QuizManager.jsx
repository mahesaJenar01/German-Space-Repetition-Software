import React, { useState, useEffect } from 'react';
import QuizContext from '../context/QuizContext';
import * as api from '../services/api';

const SESSION_KEY_PREFIX = 'vocabularyQuizSession_';

const QuizManager = ({ children, level, quizItems, allWords, onQuizSubmit, setFeedback, refreshStats, onWordClick, onShowHint, onHideHint }) => {
  const [inputs, setInputs] = useState({});
  const [results, setResults] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const inputRefs = React.useRef({});

  // --- NEW: State for focused item and random examples ---
  const [focusedItemKey, setFocusedItemKey] = useState(null);
  const [randomExamples, setRandomExamples] = useState({});

  useEffect(() => {
    if (quizItems.length > 0) {
      const initialInputs = quizItems.reduce((acc, item) => ({ ...acc, [item.key]: '' }), {});
      setInputs(initialInputs);
      setResults({});
      setIsSubmitted(false);

      // --- NEW: Generate random examples once when the quiz loads ---
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
  }, [quizItems]);

  const handleInputChange = (key, value) => {
    setInputs(prev => ({ ...prev, [key]: value }));
  };

  const checkAnswers = async () => {
    // --- NEW: Clear focus immediately on submit ---
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
      onQuizSubmit();   
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

  // --- NEW: Event handlers for focus and blur ---
  const handleFocus = (key) => setFocusedItemKey(key);
  const handleBlur = () => setFocusedItemKey(null);

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
    // --- NEW: Pass down focus state and handlers ---
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