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
            setFeedback(parsedData.feedback || 'Fill all fields and press Enter to submit.'); // Use saved feedback or default
            setIsLoading(false);
            return { restored: true, data: parsedData };
          }
        } catch (e) { console.error("Failed to parse session data", e); }
      }
    }

    sessionStorage.removeItem(sessionKey); // Clear old session data before fetching new

    setIsLoading(true);
    setQuizItems([]);
    const initialFeedback = 'Fill all fields and press Enter to submit.';
    setFeedback(initialFeedback);

    try {
      const wordsDetails = await api.fetchWordDetails(level);

      if (wordsDetails.length === 0) {
        setFeedback('No more words to be displayed, congratulations!');
        setAllWords([]);
        setQuizItems([]);
        return { restored: false, data: null };
      }

      setAllWords(wordsDetails);
      const wordKeys = wordsDetails.map(word => word.word);
      const wordsStats = await api.fetchWordStats(wordKeys, level);
      
      const newQuizItems = createQuizItems(wordsDetails, wordsStats);
      setQuizItems(newQuizItems);
      
      // --- THIS IS THE FIX ---
      // After fetching a new quiz, save it to sessionStorage for the current day.
      // We sanitize the quiz items by removing the correctAnswers to save space
      // and avoid storing answers in the browser's storage.
      const sanitizedQuizItems = newQuizItems.map(({ correctAnswers, ...item }) => item);
      
      const sessionPayload = {
        date: today,
        level: level,
        quizItems: sanitizedQuizItems, // Save the version without answers
        allWords: wordsDetails,
        feedback: initialFeedback,
      };
      
      sessionStorage.setItem(sessionKey, JSON.stringify(sessionPayload));
      console.log(`Saved new quiz for level ${level} to session.`);
      // --- END OF FIX ---

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

  return { quizItems, allWords, isLoading, feedback, setFeedback, fetchWords };
};