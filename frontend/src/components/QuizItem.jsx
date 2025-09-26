import React from 'react';
import '../styles/QuizItem.css';
import { useQuizContext } from '../context/QuizContext';

const QuizItem = ({ item, autoFocus }) => {
  const {
    inputs,
    results,
    isSubmitted,
    inputRefs,
    handleInputChange,
    onWordClick,
    onShowHint,
    onHideHint,
    // --- NEW: Get focus state and handlers ---
    focusedItemKey,
    randomExamples,
    handleFocus,
    handleBlur,
  } = useQuizContext();

  const inputValue = inputs[item.key] || '';
  const result = results[item.key];
    
  const handleWordClick = () => {
    if(isSubmitted){
      onWordClick(item.fullDetails);
    }
  }

  const isHintable = !isSubmitted && item.direction === 'meaningToWord';

  // --- NEW: Logic to get and parse the example sentence ---
  const renderExample = () => {
    // Only show if this input is focused and quiz is not submitted
    if (focusedItemKey !== item.key || isSubmitted) {
      return null;
    }

    const exampleString = randomExamples[item.key];
    if (!exampleString) {
      return null;
    }

    let exampleToShow = '';
    if (item.direction === 'meaningToWord') {
      // Show the translated (Indonesian) sentence
      const match = exampleString.match(/\((.*?)\)/);
      exampleToShow = match ? match[1] : '';
    } else {
      // Show the German sentence
      exampleToShow = exampleString.replace(/\s*\(.*?\)\s*/, '').trim();
    }
    
    return exampleToShow ? <small className="quiz-example">{exampleToShow}</small> : null;
  };

  const getWordClassName = () => {
    if (isSubmitted) return 'word clickable';
    if (isHintable) return 'word hintable';
    return 'word';
  };

  const getInputClassName = () => {
    if (isSubmitted) {
      if (result === 'PERFECT_MATCH') return 'input-correct';
      if (result === 'NO_MATCH') return 'input-wrong';
      if (result && result.startsWith('PARTIAL_MATCH')) return 'input-partial';
      return '';
    }
    const hasArticleErrorHistory = item.article_wrong > 0;
    if (item.direction === 'meaningToWord' && hasArticleErrorHistory) {
      return 'input-article-warning';
    }
    return '';
  };
  
  const renderFeedback = () => {
    if (!isSubmitted) return null;

    switch (result) {
      case 'NO_MATCH':
        return <div className="correct-answer">Correct answer: {item.displayAnswer}</div>;
      case 'PARTIAL_MATCH_WRONG_ARTICLE': {
        // ... (feedback logic remains the same)
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
        // ... (feedback logic remains the same)
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

  const itemWordDetails = item.fullDetails;
  const containerClassName = `quiz-item`;

  return (
    <div className={containerClassName} key={item.key}>
      <span
         className={getWordClassName()}
         onClick={handleWordClick}
         onMouseEnter={(e) => isHintable && onShowHint(itemWordDetails, e)}
         onMouseLeave={() => isHintable && onHideHint()}
      >
         {item.question}
       </span>
      <div className="input-container">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => handleInputChange(item.key, e.target.value)}
          disabled={isSubmitted}
          ref={el => inputRefs.current[item.key] = el}
          className={getInputClassName()}
          placeholder="Type the answer..."
          autoFocus={autoFocus}
          // --- NEW: Add focus and blur handlers ---
          onFocus={() => handleFocus(item.key)}
          onBlur={handleBlur}
        />
        {renderExample()}
        {renderFeedback()}
      </div>
    </div>
  );
};

export default QuizItem;