import React, { useEffect } from 'react';
import '../styles/WordDetail.css';

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

  const formatKey = (key) => {
    return key.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
  };

  const keysToExclude = ['word', 'right', 'wrong', 'total_encountered', 'item_key'];
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
        
        <h2>{wordDetails.word}</h2>
        
        <dl className="word-attributes">
          {detailKeys.map(key => (
            wordDetails[key] != null && wordDetails[key] !== '' && (
              <div key={key} className="attribute-item">
                <dt>{formatKey(key)}</dt>
                {/* Pass the key to the render function */}
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