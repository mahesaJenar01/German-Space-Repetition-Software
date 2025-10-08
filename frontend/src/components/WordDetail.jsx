import React, { useEffect } from 'react';
import '../styles/WordDetail.css';
import { useQuizStore } from '../store/quizStore';

const formatRegisterValue = (value) => {
  const numValue = parseInt(value, 10);

  if (isNaN(numValue)) {
    return value; // Return the original string as-is.
  }

  switch (numValue) {
    case 0:
    case 1:
      return "Vulgär";
    case 2:
    case 3:
      return "Slang";
    case 4:
    case 5:
      return "Umgangssprachlich";
    case 6:
    case 7:
      return "Neutral";
    case 8:
      return "Formell-neutral";
    case 9:
      return "Offiziell";
    case 10:
      return "Gehoben";
    default:
      return String(numValue);
  }
};

const WordDetail = ({ wordDetails, onClose }) => {
  const { toggleStarStatus } = useQuizStore();

  useEffect(() => {
    const handleEscKey = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscKey);
    return () => {
      window.removeEventListener('keydown', handleEscKey);
    };
  }, [onClose]);

  if (!wordDetails) {
    return null;
  }

  const handleStarClick = (e) => {
    e.stopPropagation(); // Prevent the modal from closing when star is clicked
    toggleStarStatus(wordDetails.item_key);
  };

  const formatKey = (key) => {
    return key.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
  };

  // --- THIS IS THE FIX ---
  // We expand this list to include all internal repetition stats that
  // should not be displayed to the user on the detail card.
  const keysToExclude = [
    'word', 'right', 'wrong', 'total_encountered', 'item_key', 'is_starred',
    'article_wrong', 'last_seen', 'last_correct', 'consecutive_correct',
    'streak_level', 'current_delay_days', 'next_show_date', 'recent_history',
    'failed_first_encounter', 'last_result_was_wrong', 'successful_corrections'
  ];
  const detailKeys = Object.keys(wordDetails).filter(key => !keysToExclude.includes(key));
  
  const renderDetailValue = (key, value) => {
    if (key === 'register') {
      return formatRegisterValue(value);
    }

    if (typeof value === 'string' && value.includes(';')) {
      const listItems = value.split(';').map(item => item.trim()).filter(item => item.length > 0);
      if (listItems.length > 1) {
        return (
          <ul className="attribute-list">
            {listItems.map((item, index) => <li key={index}>{item}</li>)}
          </ul>
        );
      }
    }
    return String(value);
  };

  return (
    <div className="word-detail-overlay" onClick={onClose}>
      <div className="word-detail-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose} aria-label="Close details">&times;</button>
        
        <div className="word-detail-header">
          <h2>{wordDetails.word}</h2>
          <button
            className={`star-button ${wordDetails.is_starred ? 'starred' : ''}`}
            onClick={handleStarClick}
            aria-label={wordDetails.is_starred ? 'Unstar this word' : 'Star this word'}
            title={wordDetails.is_starred ? 'Unstar this word' : 'Star this word'}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
            </svg>
          </button>
        </div>
        
        <dl className="word-attributes">
          {detailKeys.map(key => (
            wordDetails[key] != null && wordDetails[key] !== '' && (
              <div key={key} className="attribute-item">
                <dt>{formatKey(key)}</dt>
                <dd>{renderDetailValue(key, wordDetails[key])}</dd>
              </div>
            )
          ))}
        </dl>
        
        <small className="close-hint">Click outside or press 'Esc' to close</small>
      </div>
    </div>
  );
};

export default WordDetail;