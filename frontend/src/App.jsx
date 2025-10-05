import { useEffect, useRef } from 'react';
import LevelSelector from './components/LevelSelector';
import QuizContainer from './components/QuizContainer';
import WordDetail from './components/WordDetail';
import HintCard from './components/HintCard';
import QuizManager from './components/QuizManager';
import './App.css';
import { useQuizStore } from './store/quizStore'; // <-- IMPORT THE STORE

function App() {
  // --- Select state and actions from the Zustand store ---
  const { 
    level, 
    isQuizCompleted, 
    quizItems, 
    isLoading, 
    feedback,
    practicedToday, 
    todayStats,
    selectedWord,
    hintData,
    hintPosition,
    fetchWords,
    closeWordDetail,
  } = useQuizStore();
  
  const appContainerRef = useRef(null);
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && isQuizCompleted) {
      // Directly call the action from the store
      fetchWords(true);
    }
  };

  useEffect(() => {
    // This effect now only handles focus management
    if (isQuizCompleted && appContainerRef.current) {
      appContainerRef.current.focus({ preventScroll: true });
    }
  }, [isQuizCompleted]);
  
  // This effect handles closing the word detail modal with the 'Esc' key
  useEffect(() => {
    const handleEsc = (event) => {
       if (event.key === 'Escape') {
         closeWordDetail();
       }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [closeWordDetail]);


  // --- All calculations remain the same, using state from the store ---
  const totalCorrect = Object.values(todayStats.correct_by_level).reduce((sum, count) => sum + count, 0);
  const totalWrong = Object.values(todayStats.wrong_by_level).reduce((sum, count) => sum + count, 0);
  const overallTotal = totalCorrect + totalWrong;
  const overallAccuracy = overallTotal > 0 ? Math.round((totalCorrect / overallTotal) * 100) : 0;
  
  const levelCorrect = todayStats.correct_by_level[level] || 0;
  const levelWrong = todayStats.wrong_by_level[level] || 0;
  const levelTotal = levelCorrect + levelWrong;
  const levelAccuracy = levelTotal > 0 ? Math.round((levelCorrect / levelTotal) * 100) : 0;

  return (
    <div className="app-container" onKeyDown={handleKeyDown} tabIndex="0" ref={appContainerRef}>
      <div className="stats-bar">
        <span>Words Practiced: <strong>{practicedToday}</strong></span>
        <span>{level.toUpperCase()} Accuracy: <strong>{`${levelAccuracy}%`}</strong></span>
        <span>Overall Accuracy: <strong>{`${overallAccuracy}%`}</strong></span>
      </div>
      
      <LevelSelector />
      
      {isLoading ? (<p>Loading words...</p>) : (
        <QuizManager quizItems={quizItems}>
          <QuizContainer />
        </QuizManager>
      )}
      
      <p className="feedback-message">{feedback}</p>
      
      {selectedWord && <WordDetail wordDetails={selectedWord} onClose={closeWordDetail} />}
      {hintData && <HintCard {...hintData} position={hintPosition} />}
    </div>
  );
}

export default App;