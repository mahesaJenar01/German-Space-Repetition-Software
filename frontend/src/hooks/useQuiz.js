import { useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';
import { createQuizItems, rehydrateQuizAnswers } from '../utils/quizProcessor';

const getTodayString = () => new Date().toISOString().split('T')[0];
const SESSION_KEY_PREFIX = 'vocabularyQuizSession_';

export const useQuiz = (level) => {
  const [quizItems, setQuizItems] = useState([]);
  // --- RENAMED: This now holds the array of specific meaning objects for the current quiz ---
  const [currentQuizDetails, setCurrentQuizDetails] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [feedback, setFeedback] = useState('Fill all fields and press Enter to submit.');
  const [dailySessionInfo, setDailySessionInfo] = useState(null);

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
            // --- UPDATED: Pass the stored details to the rehydration function ---
            const rehydratedItems = rehydrateQuizAnswers(parsedData.quizItems, parsedData.currentQuizDetails);
            setQuizItems(rehydratedItems);
            setCurrentQuizDetails(parsedData.currentQuizDetails);
            setDailySessionInfo(parsedData.dailySessionInfo);
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
      // --- UPDATED: API response is now an object { quiz_words, session_info } ---
      const responseData = await api.fetchWordDetails(level);
      const { quiz_words: meaningDetailsList, session_info: sessionInfo } = responseData;

      setDailySessionInfo(sessionInfo);

      if (meaningDetailsList.length === 0) {
        setFeedback('No more words to be displayed, congratulations!');
        setCurrentQuizDetails([]);
        setQuizItems([]);
        return { restored: false, data: null };
      }

      setCurrentQuizDetails(meaningDetailsList);
      
      // --- UPDATED: Fetch stats using the unique item_key from each object ---
      const itemKeys = meaningDetailsList.map(detail => detail.item_key);
      const wordsStats = await api.fetchWordStats(itemKeys, level);
      
      const newQuizItems = createQuizItems(meaningDetailsList, wordsStats);
      setQuizItems(newQuizItems);
      
      // --- UPDATED: Sanitize for session storage ---
      const sanitizedQuizItems = newQuizItems.map(({ correctAnswers, fullDetails, ...item }) => item);
      
      const sessionPayload = {
        date: today,
        level: level,
        quizItems: sanitizedQuizItems,
        currentQuizDetails: meaningDetailsList, // Save the full details
        dailySessionInfo: sessionInfo,
        feedback: initialFeedback,
      };
      
      sessionStorage.setItem(sessionKey, JSON.stringify(sessionPayload));
      console.log(`Saved new quiz for level ${level} to session.`);

      return { restored: false, data: { quizItems: newQuizItems, currentQuizDetails: meaningDetailsList } };
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

  return { quizItems, allWords: currentQuizDetails, isLoading, feedback, setFeedback, fetchWords, dailySessionInfo };
};