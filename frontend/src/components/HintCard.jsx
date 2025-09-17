import React, { useState, useEffect, useRef } from 'react';
import '../styles/HintCard.css';

const HintCard = ({ register, type, context, position }) => {
  const cardRef = useRef(null);
  const [adjustedPosition, setAdjustedPosition] = useState(position);

  useEffect(() => {
    if (cardRef.current) {
      const cardRect = cardRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;

      let newTop = position.top;
      let newLeft = position.left;

      // Check for vertical overflow (bottom edge)
      if (position.top + cardRect.height > viewportHeight - 10) { // 10px buffer
        // Flip to be above the cursor
        newTop = position.top - cardRect.height - 15;
      }

      // Check for horizontal overflow (right edge)
      if (position.left + cardRect.width > viewportWidth - 10) { // 10px buffer
        // Flip to be to the left of the cursor
        newLeft = position.left - cardRect.width - 15;
      }

      setAdjustedPosition({ top: newTop, left: newLeft });
    }
    // Re-run this effect if the initial position or content changes
  }, [position, register, type, context]);

  // Don't render the card if there's no data to show
  if (!register && !type && !context) {
    return null;
  }

  const cardStyle = {
    // Use the adjusted position for rendering
    top: `${adjustedPosition.top}px`,
    left: `${adjustedPosition.left}px`,
    // Initially hide the card until its position is calculated to prevent flicker
    visibility: cardRef.current ? 'visible' : 'hidden',
  };

  return (
    <div ref={cardRef} className="hint-card" style={cardStyle}>
      <dl className="hint-attributes">
        {register && (
          <div className="hint-item">
            <dt>Register</dt>
            <dd>{register}</dd>
          </div>
        )}
        {type && (
          <div className="hint-item">
            <dt>Type</dt>
            <dd>{type}</dd>
          </div>
        )}
        {context && (
          <div className="hint-item hint-context">
            <dt>Context</dt>
            <dd>{context}</dd>
          </div>
        )}
      </dl>
    </div>
  );
};

export default HintCard;