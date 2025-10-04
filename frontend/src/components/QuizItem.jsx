import React from 'react';
import '../styles/QuizItem.css';
import { useQuizContext } from '../context/QuizContext';

const getRegisterClassName = (registerValue) => {
  // First, convert the value to a number. parseInt is perfect for this.
  const numValue = parseInt(registerValue, 10);

  if (!isNaN(numValue)) {
    // Now, use the numeric value for comparisons
    if (numValue <= 3) return 'register-informal';
    if (numValue <= 5) return 'register-colloquial';
    if (numValue >= 8) return 'register-formal';
  } else if (typeof registerValue === 'string') {
    // Backward compatibility for old string-based values
    const lowerCaseValue = registerValue.toLowerCase();
    if (lowerCaseValue.includes('slang') || lowerCaseValue.includes('informal') || lowerCaseValue.includes('umgangssprachlich')) {
      return 'register-colloquial';
    }
    if (lowerCaseValue.includes('formal') || lowerCaseValue.includes('offiziell') || lowerCaseValue.includes('förmlich')) {
      return 'register-formal';
    }
  }
  return ''; // Neutral (6-7) or unrecognized values get no special style
};


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

  const renderExample = () => {
    if (focusedItemKey !== item.key || isSubmitted) {
      return null;
    }
    const exampleString = randomExamples[item.key];
    if (!exampleString) return null;
    let exampleToShow = '';
    if (item.direction === 'meaningToWord') {
      const match = exampleString.match(/\((.*?)\)/);
      exampleToShow = match ? match[1] : '';
    } else {
      exampleToShow = exampleString.replace(/\s*\(.*?\)\s*/, '').trim();
    }
    return exampleToShow ? <small className="quiz-example">{exampleToShow}</small> : null;
  };

  const getWordClassName = () => {
    const registerClass = !isSubmitted ? getRegisterClassName(item.fullDetails?.register) : '';

    if (isSubmitted) return `word clickable ${registerClass}`;
    if (isHintable) return `word hintable ${registerClass}`;
    return `word ${registerClass}`;
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

  const itemWordDetails = item.fullDetails;
  const containerClassName = `quiz-item`;

  return (
    <div className={containerClassName} key={item.key}>
      <span
         className={getWordClassName().trim()}
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