import React from 'react';
import '../styles/QuizItem.css';
import { useQuizContext } from '../context/QuizContext';

const QuizItem = ({ item, autoFocus }) => {
  // Consume all the state and functions needed from the context
  const {
    allWords,
    inputs,
    results,
    isSubmitted,
    inputRefs,
    handleInputChange,
    onWordClick,
    onShowHint,
    onHideHint,
  } = useQuizContext();

  const inputValue = inputs[item.key] || '';
  const result = results[item.key];
    
  const handleWordClick = () => {
    if(isSubmitted){
      onWordClick(item.key)
    }
  }

  const isHintable = !isSubmitted && item.direction === 'meaningToWord';

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

  const itemWordDetails = allWords.find(word => word.word === item.key);

  return (
    <div className="quiz-item" key={item.key}>
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
        />
        {renderFeedback()}
      </div>
    </div>
  );
};

export default QuizItem;