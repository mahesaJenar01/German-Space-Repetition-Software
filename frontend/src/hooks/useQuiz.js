import { useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';
import { createQuizItems, rehydrateQuizAnswers } from '../utils/quizProcessor'; // Import rehydrate function

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
            
            // --- MODIFICATION: Rehydrate the answers ---
            const rehydratedItems = rehydrateQuizAnswers(parsedData.quizItems, parsedData.allWords);
            setQuizItems(rehydratedItems); // Set state with full items (including answers)
            
            setAllWords(parsedData.allWords);
            setFeedback(parsedData.feedback); 
            setIsLoading(false);
            return { restored: true, data: parsedData };
          }
        } catch (e) { console.error("Failed to parse session data", e); }
      }
    }

    sessionStorage.removeItem(sessionKey);

    setIsLoading(true);
    setQuizItems([]);
    setFeedback('Fill all fields and press Enter to submit.');

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