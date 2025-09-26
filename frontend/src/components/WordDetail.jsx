import React, { useEffect } from 'react';
import '../styles/WordDetail.css';

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

  // Function to format the JSON keys into readable labels
  const formatKey = (key) => {
    return key.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
  };

  const keysToExclude = ['word', 'right', 'wrong', 'total_encountered', 'item_key'];
  const detailKeys = Object.keys(wordDetails).filter(key => !keysToExclude.includes(key));
  
  const renderDetailValue = (value) => {
    // Check if the value is a string and contains a semicolon
    if (typeof value === 'string' && value.includes(';')) {
      const listItems = value
        .split(';')
        .map(item => item.trim()) // Clean up whitespace
        .filter(item => item.length > 0); // Remove empty items

      // Only render as a list if there are multiple items
      if (listItems.length > 1) {
        return (
          <ul className="attribute-list">
            {listItems.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        );
      }
    }
    // Fallback: render as a simple string
    return String(value);
  };

  return (
    <div className="word-detail-overlay" onClick={onClose}>
      <div className="word-detail-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose} aria-label="Close details">&times;</button>
        
        <h2>{wordDetails.word}</h2>
        
        <dl className="word-attributes">
          {detailKeys.map(key => (
            wordDetails[key] && (
              <div key={key} className="attribute-item">
                <dt>{formatKey(key)}</dt>
                <dd>{renderDetailValue(wordDetails[key])}</dd>
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