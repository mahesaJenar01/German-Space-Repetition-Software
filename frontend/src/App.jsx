import { useState, useEffect, useRef } from 'react';
import LevelSelector from './components/LevelSelector';
import QuizContainer from './components/QuizContainer';
import WordDetail from './components/WordDetail';
import HintCard from './components/HintCard';
import QuizManager from './components/QuizManager';
// import ProgressBar from './components/ProgressBar'; // --- REMOVED ---
import './App.css';
import { useQuiz } from './hooks/useQuiz';
import { useDailyStats } from './hooks/useDailyStats';
import { useWordDetail } from './hooks/useWordDetail';
import { useHint } from './hooks/useHint';
// import { useDailyProgress } from './hooks/useDailyProgress'; // --- REMOVED ---

const LEVEL_STORAGE_KEY = 'vocabularyAppLevel';

function App() {
  const [level, setLevel] = useState(() => {
    const savedLevel = localStorage.getItem(LEVEL_STORAGE_KEY);
    return savedLevel || 'a1';
  });
  
  const [isQuizCompleted, setIsQuizCompleted] = useState(false);
  
  const { quizItems, allWords, isLoading, feedback, setFeedback, fetchWords, dailySessionInfo } = useQuiz(level);
  const { practicedToday, todayStats, refreshStats } = useDailyStats();
  const { selectedWord, showWordDetail, closeWordDetail } = useWordDetail();
  const { hintData, hintPosition, showHint, hideHint } = useHint();
  // const { progress, updateProgress } = useDailyProgress(level, dailySessionInfo); // --- REMOVED ---

  const appContainerRef = useRef(null);
  
  const handleKeyDown = async (e) => {
    if (e.key === 'Enter' && isQuizCompleted) {
      setIsQuizCompleted(false);
      await fetchWords(true);
    }
  };
  
  useEffect(() => {
    localStorage.setItem(LEVEL_STORAGE_KEY, level);
    setIsQuizCompleted(false);
  }, [level]);

  useEffect(() => {
    if (isQuizCompleted && appContainerRef.current) {
      appContainerRef.current.focus({ preventScroll: true });
    }
  }, [isQuizCompleted]);

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
        {level !== 'mix' && <span>{level.toUpperCase()} Accuracy: <strong>{`${levelAccuracy}%`}</strong></span>}
        <span>Overall Accuracy: <strong>{`${overallAccuracy}%`}</strong></span>
      </div>
      
      {/* --- REMOVED the ProgressBar component from here --- */}
      
      <LevelSelector level={level} setLevel={setLevel} />
      
      {isLoading ? (<p>Loading words...</p>) : (
        <QuizManager
          level={level}
          quizItems={quizItems}
          allWords={allWords}
          setFeedback={setFeedback}
          refreshStats={refreshStats}
          // updateProgress={updateProgress} // --- REMOVED ---
          onQuizSubmit={() => setIsQuizCompleted(true)}
          onWordClick={(wordDetailsObject) => {
            showWordDetail(wordDetailsObject);
          }}
          onShowHint={showHint}
          onHideHint={hideHint}
        >
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