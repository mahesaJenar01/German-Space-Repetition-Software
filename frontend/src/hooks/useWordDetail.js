import { useState, useEffect } from 'react';

export const useWordDetail = () => {
  const [selectedWord, setSelectedWord] = useState(null);

  const showWordDetail = (wordDetails) => {
    setSelectedWord(wordDetails);
  };

  const closeWordDetail = () => {
    setSelectedWord(null);
  };
  
  // Add keyboard listener for 'Esc' key to close the modal
  useEffect(() => {
    const handleEsc = (event) => {
       if (event.key === 'Escape') {
         closeWordDetail();
       }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  return { selectedWord, showWordDetail, closeWordDetail };
};