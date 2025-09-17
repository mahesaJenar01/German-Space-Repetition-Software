import { useState, useEffect, useRef } from 'react';
import LevelSelector from './components/LevelSelector';
import QuizContainer from './components/QuizContainer';
import WordDetail from './components/WordDetail';
import HintCard from './components/HintCard';
import './App.css';
import { useQuiz } from './hooks/useQuiz';
import * as api from './services/api';

const getTodayString = () => new Date().toISOString().split('T')[0];
const SESSION_KEY_PREFIX = 'vocabularyQuizSession_';

function App() {
  const [level, setLevel] = useState('a1');
  const { quizItems, allWords, isLoading, feedback, setFeedback, fetchWords } = useQuiz(level);

  const [inputs, setInputs] = useState({});
  const [results, setResults] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [selectedWord, setSelectedWord] = useState(null);
  const [practicedToday, setPracticedToday] = useState(0);
  const [todayStats, setTodayStats] = useState({ correct_by_level: {}, wrong_by_level: {} });
  const [hintData, setHintData] = useState(null);
  const [hintPosition, setHintPosition] = useState({ top: 0, left: 0 });

  const inputRefs = useRef({});
  const appContainerRef = useRef(null);

  // ... useEffect for session storage is unchanged ...
  useEffect(() => {
    const sessionKey = `${SESSION_KEY_PREFIX}${level}`;
    const sessionData = sessionStorage.getItem(sessionKey);
    if (sessionData) {
      const parsed = JSON.parse(sessionData);
      if (parsed.date === getTodayString() && parsed.level === level) {
          setInputs(parsed.inputs || {});
          setResults(parsed.results || {});
          setIsSubmitted(parsed.isSubmitted || false);
      }
    } else {
      setIsSubmitted(false);
      setResults({});
    }
  }, [level]);
  
  useEffect(() => {
    if (isLoading || quizItems.length === 0) return;
    const sanitizedQuizItems = quizItems.map(({ correctAnswers, ...rest }) => rest);
    const sessionKey = `${SESSION_KEY_PREFIX}${level}`;
    const sessionData = {
      date: getTodayString(),
      level,
      quizItems: sanitizedQuizItems,
      allWords,
      inputs,
      results,
      isSubmitted,
      feedback,
    };
    sessionStorage.setItem(sessionKey, JSON.stringify(sessionData));
  }, [level, quizItems, allWords, inputs, results, isSubmitted, feedback, isLoading]);

  const updateAllTodayStats = async () => {
    const count = await api.fetchPracticedTodayCount();
    setPracticedToday(count);
    const stats = await api.fetchTodayStats();
    setTodayStats(stats);
  };
  
  useEffect(() => {
    updateAllTodayStats();
  }, []);

  useEffect(() => {
    const handleEsc = (event) => {
       if (event.keyCode === 27) setSelectedWord(null);
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  useEffect(() => {
    if (quizItems.length > 0) {
      const sessionKey = `${SESSION_KEY_PREFIX}${level}`;
      const sessionData = sessionStorage.getItem(sessionKey);
      let isSessionSubmitted = false;
      if (sessionData) {
        try { isSessionSubmitted = JSON.parse(sessionData).isSubmitted; } catch (e) {}
      }
      if (!isSessionSubmitted) {
        const initialInputs = quizItems.reduce((acc, item) => ({...acc, [item.key]: acc[item.key] || ''}), {...inputs});
        setInputs(initialInputs);
      }
    }
  }, [quizItems, level]);

  const handleWordClick = (wordKey) => {
    const wordDetails = allWords.find(word => word.word === wordKey);
    setSelectedWord(wordDetails);
  };
  
  const handleInputChange = (key, value) => {
    setInputs(prev => ({ ...prev, [key]: value }));
  };
  
  const handleShowHint = (wordKey, event) => {
    const wordDetails = allWords.find(word => word.word === wordKey);
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

  const handleHideHint = () => setHintData(null);

  const checkAnswers = async () => {
    const newResults = {};
    const resultsPayload = [];

    quizItems.forEach(item => {
      const correctAnswersSet = new Set(item.correctAnswers);
      const wordDetail = allWords.find(w => w.word === item.key);
      let userAnswer = (inputs[item.key] || "").trim();
      const isNounTest = wordDetail && wordDetail.type === 'Nomen' && item.direction === 'meaningToWord';
      if (!isNounTest) userAnswer = userAnswer.toLowerCase();

      let resultType = 'NO_MATCH';
      if (userAnswer.split(';').map(p => p.trim()).filter(Boolean).some(part => correctAnswersSet.has(part))) {
        resultType = 'PERFECT_MATCH';
      } else if (isNounTest) {
        const userNoun = userAnswer.replace(/^(der|die|das)\s+/i, '');
        if (correctAnswersSet.has(userNoun)) {
          resultType = userAnswer.match(/^(der|die|das)/i) ? 'PARTIAL_MATCH_WRONG_ARTICLE' : 'PARTIAL_MATCH_MISSING_ARTICLE';
        }
      }
      newResults[item.key] = resultType;
      resultsPayload.push({ word: item.key, result_type: resultType });
    });

    setResults(newResults);
    setIsSubmitted(true);
    setFeedback('Press Enter to continue to the next quiz.');
    if (appContainerRef.current) appContainerRef.current.focus();

    try {
      await api.updateWordStats(level, resultsPayload);
      updateAllTodayStats();
    } catch (error){
      console.error("Failed to update stats:", error);
    }
  };

  const handleKeyDown = async (e) => {
    if (e.key === 'Enter') {
      if (isSubmitted) {
        setIsSubmitted(false);
        setResults({});
        const result = await fetchWords(true);
        if (result && !result.restored && result.data) {
            const initialInputs = result.data.quizItems.reduce((acc, item) => ({...acc, [item.key]: ''}), {});
            setInputs(initialInputs);
        }
      } else {
        const allFilled = quizItems.length > 0 && quizItems.every(item => (inputs[item.key] || "").trim() !== '');
        if (allFilled || quizItems.length === 0) checkAnswers();
        else setFeedback('Please fill in all the answers before submitting.');
      }
    }
  };
  
  const { correct_by_level, wrong_by_level } = todayStats;
  
  const totalCorrect = Object.values(correct_by_level).reduce((sum, count) => sum + count, 0);
  const totalWrong = Object.values(wrong_by_level).reduce((sum, count) => sum + count, 0);
  const overallTotal = totalCorrect + totalWrong;
  const overallAccuracy = overallTotal > 0 ? Math.round((totalCorrect / overallTotal) * 100) : 'N/A';
  
  const levelCorrect = correct_by_level[level] || 0;
  const levelWrong = wrong_by_level[level] || 0;
  const levelTotal = levelCorrect + levelWrong;
  const levelAccuracy = levelTotal > 0 ? Math.round((levelCorrect / levelTotal) * 100) : 'N/A';

  const formatAccuracy = (value) => value !== 'N/A' ? `${value}%` : 'N/A';

  return (
    <div className="app-container" onKeyDown={handleKeyDown} tabIndex="0" ref={appContainerRef}>
      <h1>Vocabulary Repetition</h1>
      <div className="stats-bar">
        <span>Words Practiced: <strong>{practicedToday}</strong></span>
        {level !== 'mix' && <span>{level.toUpperCase()} Accuracy: <strong>{formatAccuracy(levelAccuracy)}</strong></span>}
        <span>Overall Accuracy: <strong>{formatAccuracy(overallAccuracy)}</strong></span>
      </div>
      <LevelSelector level={level} setLevel={setLevel} />
      {isLoading ? (<p>Loading words...</p>) : (
        <QuizContainer
          quizItems={quizItems}
          inputs={inputs}
          handleInputChange={handleInputChange}
          isSubmitted={isSubmitted}
          results={results}
          inputRefs={inputRefs}
          onWordClick={handleWordClick}
          onShowHint={handleShowHint} /* --- THIS IS THE FIX --- */
          onHideHint={handleHideHint} /* --- THIS IS THE FIX --- */
        />
      )}
      <p className="feedback-message">{feedback}</p>
      {selectedWord && <WordDetail wordDetails={selectedWord} onClose={() => setSelectedWord(null)} />}
      {hintData && <HintCard {...hintData} position={hintPosition} />}
    </div>
  );
}

export default App;
