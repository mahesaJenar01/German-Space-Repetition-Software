import { useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';
import { createQuizItems, rehydrateQuizAnswers } from '../utils/quizProcessor';

const getTodayString = () => new Date().toISOString().split('T')[0];
const SESSION_KEY_PREFIX = 'vocabularyQuizSession_';

export const useQuiz = (level) => {
  const [quizItems, setQuizItems] = useState([]);
  const [allWords, setAllWords] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [feedback, setFeedback] = useState('Fill all fields and press Enter to submit.');
  const [dailySessionInfo, setDailySessionInfo] = useState(null); // <-- NEW STATE

  const fetchWords = useCallback(async (forceRefetch = false) => {
    const today = getTodayString();
    const sessionKey = `${SESSION_KEY_PREFIX}${level}`;

    if (!forceRefetch) {
      const sessionData = sessionStorage.getItem(sessionKey);
      if (sessionData) {
        try {
          const parsedData = JSON.parse(sessionData);
          if (parsedData.date === today && parsedData.level === level) {
            console.log(`Restoring quiz for level ${level} from session.`);
            const rehydratedItems = rehydrateQuizAnswers(parsedData.quizItems, parsedData.allWords);
            setQuizItems(rehydratedItems);
            setAllWords(parsedData.allWords);
            setDailySessionInfo(parsedData.dailySessionInfo); // <-- RESTORE SESSION INFO
            setFeedback(parsedData.feedback || 'Fill all fields and press Enter to submit.');
            setIsLoading(false);
            return { restored: true, data: parsedData };
          }
        } catch (e) { console.error("Failed to parse session data", e); }
      }
    }

    sessionStorage.removeItem(sessionKey);

    setIsLoading(true);
    setQuizItems([]);
    const initialFeedback = 'Fill all fields and press Enter to submit.';
    setFeedback(initialFeedback);

    try {
      const responseData = await api.fetchWordDetails(level);
      const { quiz_words: wordsDetails, session_info: sessionInfo } = responseData;

      if (wordsDetails.length === 0) {
        setFeedback('No more words to be displayed, congratulations!');
        setAllWords([]);
        setQuizItems([]);
        setDailySessionInfo(sessionInfo); // Set session info even if quiz is empty
        return { restored: false, data: null };
      }

      setAllWords(wordsDetails);
      setDailySessionInfo(sessionInfo); // <-- SET SESSION INFO FROM API
      const wordKeys = wordsDetails.map(word => word.word);
      const wordsStats = await api.fetchWordStats(wordKeys, level);
      
      const newQuizItems = createQuizItems(wordsDetails, wordsStats);
      setQuizItems(newQuizItems);
      
      const sanitizedQuizItems = newQuizItems.map(({ correctAnswers, ...item }) => item);
      
      const sessionPayload = {
        date: today,
        level: level,
        quizItems: sanitizedQuizItems,
        allWords: wordsDetails,
        dailySessionInfo: sessionInfo, // <-- SAVE SESSION INFO
        feedback: initialFeedback,
      };
      
      sessionStorage.setItem(sessionKey, JSON.stringify(sessionPayload));
      console.log(`Saved new quiz for level ${level} to session.`);

      return { restored: false, data: { quizItems: newQuizItems, allWords: wordsDetails } };
    } catch (error) {
      console.error("Failed to fetch words:", error);
      setFeedback('Error: Could not load words from the server.');
      return { restored: false, data: null };
    } finally {
      setIsLoading(false);
    }
  }, [level]);

  useEffect(() => {
    fetchWords();
  }, [level, fetchWords]);

  return { quizItems, allWords, isLoading, feedback, setFeedback, fetchWords, dailySessionInfo }; // <-- RETURN SESSION INFO
};