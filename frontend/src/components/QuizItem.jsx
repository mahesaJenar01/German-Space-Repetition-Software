import React from 'react';
import '../styles/QuizItem.css';

const QuizItem = ({ item, inputValue, onInputChange, isSubmitted, result, inputRef, autoFocus, onWordClick, onShowHint, onHideHint }) => {
    
  const handleWordClick = () => {
    if(isSubmitted){
      onWordClick(item.key)
    }
  }

  const isHintable = !isSubmitted && item.direction === 'meaningToWord';

  const getWordClassName = () => {
    if (isSubmitted) {
      return 'word clickable';
    }
    if (isHintable) {
      return 'word hintable';
    }
    return 'word';
  };

  // --- MODIFIED: Function to determine input class dynamically ---
  const getInputClassName = () => {
    // After submission, use the result type
    if (isSubmitted) {
      if (result === 'PERFECT_MATCH') return 'input-correct';
      if (result === 'NO_MATCH') return 'input-wrong';
      if (result && result.startsWith('PARTIAL_MATCH')) return 'input-partial';
      return '';
    }
    
    // Before submission, check for article error history
    const hasArticleErrorHistory = item.article_wrong > 0;
    if (item.direction === 'meaningToWord' && hasArticleErrorHistory) {
      return 'input-article-warning';
    }

    return ''; // Default empty class
  };
  
  const renderFeedback = () => {
    if (!isSubmitted) return null;

    switch (result) {
      case 'NO_MATCH':
        return <div className="correct-answer">Correct answer: {item.displayAnswer}</div>;

      case 'PARTIAL_MATCH_WRONG_ARTICLE': {
        const userInput = inputValue.trim(); // Keep case for display
        // Robustly find parts, defaulting to empty strings if not found
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


  return (
    <div className="quiz-item" key={item.key}>
      <span
         className={getWordClassName()}
         onClick={handleWordClick}
         onMouseEnter={(e) => isHintable && onShowHint(item.key, e)}
         onMouseLeave={() => isHintable && onHideHint()}
      >
         {item.question}
       </span>
      <div className="input-container">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => onInputChange(item.key, e.target.value)}
          disabled={isSubmitted}
          ref={inputRef}
          className={getInputClassName()}
          placeholder="Type the answer..."
          autoFocus={autoFocus}
        />
        {renderFeedback()}
      </div>
    </div>
  );
};

export default QuizItem;