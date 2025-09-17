import { useState } from 'react';

export const useHint = () => {
  const [hintData, setHintData] = useState(null);
  const [hintPosition, setHintPosition] = useState({ top: 0, left: 0 });

  const showHint = (wordDetails, event) => {
    if (!wordDetails) return;
    
    const { register, type, context } = wordDetails;
    const isPreposition = type === 'Präposition';
    const isNoun = type === 'Nomen';
    const showContext = (isPreposition || isNoun) && context;

    if (register || type || showContext) {
      setHintData({ register, type, context: showContext ? context : null });
      setHintPosition({ top: event.clientY + 15, left: event.clientX + 15 });
    }
  };

  const hideHint = () => {
    setHintData(null);
  };

  return { hintData, hintPosition, showHint, hideHint };
};