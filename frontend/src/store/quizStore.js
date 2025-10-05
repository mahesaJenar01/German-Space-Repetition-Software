import { create } from 'zustand';
import * as api from '../services/api';
import { createQuizItems, rehydrateQuizAnswers } from '../utils/quizProcessor';

const LEVEL_STORAGE_KEY = 'vocabularyAppLevel';
const SESSION_KEY_PREFIX = 'vocabularyQuizSession_';
const getTodayString = () => new Date().toISOString().split('T')[0];

export const useQuizStore = create((set, get) => ({
  // --- STATE ---
  level: localStorage.getItem(LEVEL_STORAGE_KEY) || 'a1',
  quizItems: [],
  currentQuizDetails: [], // Holds full details for rehydration
  isLoading: true,
  feedback: 'Loading your session...',
  isQuizCompleted: false,
  
  practicedToday: 0,
  todayStats: { correct_by_level: {}, wrong_by_level: {} },
  
  selectedWord: null,
  hintData: null,
  hintPosition: { top: 0, left: 0 },

  // --- ACTIONS ---

  // Initialization action to fetch initial data
  init: () => {
    get().fetchWords();
    get().refreshStats();
  },

  // Level and Quiz Management
  setLevel: (newLevel) => {
    if (get().level === newLevel) return; // Prevent re-fetching for the same level
    localStorage.setItem(LEVEL_STORAGE_KEY, newLevel);
    // The isQuizCompleted reset is now handled by fetchWords, simplifying this action
    set({ level: newLevel }); 
    get().fetchWords(true); // Force refetch when level changes
  },
  
  setFeedback: (message) => set({ feedback: message }),
  
  setIsQuizCompleted: (status) => set({ isQuizCompleted: status }),

  fetchWords: async (forceRefetch = false) => {
    // --- THIS IS THE FIX ---
    // Always reset the completion status when starting to fetch a new quiz.
    set({ isQuizCompleted: false });

    const { level } = get();
    const today = getTodayString();
    const sessionKey = `${SESSION_KEY_PREFIX}${level}`;

    if (!forceRefetch) {
      const sessionData = sessionStorage.getItem(sessionKey);
      if (sessionData) {
        try {
          const parsedData = JSON.parse(sessionData);
          if (parsedData.date === today && parsedData.level === level) {
            console.log(`Restoring quiz for level ${level} from session.`);
            const rehydratedItems = rehydrateQuizAnswers(parsedData.quizItems, parsedData.currentQuizDetails);
            set({
              quizItems: rehydratedItems,
              currentQuizDetails: parsedData.currentQuizDetails,
              feedback: parsedData.feedback || 'Fill all fields and press Enter to submit.',
              isLoading: false,
            });
            return;
          }
        } catch (e) { console.error("Failed to parse session data", e); }
      }
    }

    sessionStorage.removeItem(sessionKey);
    set({ isLoading: true, quizItems: [], feedback: 'Fetching new words...' });

    try {
      const { quiz_words: meaningDetailsList, session_info: sessionInfo } = await api.fetchWordDetails(level);

      if (meaningDetailsList.length === 0) {
        set({ feedback: "You're all done for today. Check back tomorrow!", quizItems: [], currentQuizDetails: [] });
        return;
      }
      
      const itemKeys = meaningDetailsList.map(detail => detail.item_key);
      const wordsStats = await api.fetchWordStats(itemKeys, level);
      const newQuizItems = createQuizItems(meaningDetailsList, wordsStats);
      const sanitizedQuizItems = newQuizItems.map(({ correctAnswers, fullDetails, ...item }) => item);
      const initialFeedback = 'Fill all fields and press Enter to submit.';
      
      const sessionPayload = {
        date: today,
        level: level,
        quizItems: sanitizedQuizItems,
        currentQuizDetails: meaningDetailsList,
        dailySessionInfo: sessionInfo,
        feedback: initialFeedback,
      };
      
      sessionStorage.setItem(sessionKey, JSON.stringify(sessionPayload));
      console.log(`Saved new quiz for level ${level} to session.`);
      set({ quizItems: newQuizItems, currentQuizDetails: meaningDetailsList, feedback: initialFeedback });

    } catch (error) {
      console.error("Failed to fetch words:", error);
      set({ feedback: 'Error: Could not load words from the server.' });
    } finally {
      set({ isLoading: false });
    }
  },

  // Daily Stats Management
  refreshStats: async () => {
    try {
      const count = await api.fetchPracticedTodayCount();
      const stats = await api.fetchTodayStats();
      set({ practicedToday: count, todayStats: stats });
    } catch (error) {
      console.error("Failed to fetch daily stats:", error);
    }
  },

  // Word Detail Modal Management
  showWordDetail: (wordDetails) => set({ selectedWord: wordDetails }),
  closeWordDetail: () => set({ selectedWord: null }),
  
  // Hint Management
  showHint: (wordDetails, event) => {
    if (!wordDetails) return;
    const { register, type, context } = wordDetails;
    const isPreposition = type === 'Präposition';
    const isNoun = type === 'Nomen';
    const showContext = (isPreposition || isNoun) && context;
    if (register || type || showContext) {
      set({
        hintData: { register, type, context: showContext ? context : null },
        hintPosition: { top: event.clientY + 15, left: event.clientX + 15 },
      });
    }
  },
  hideHint: () => set({ hintData: null }),
}));

// --- Initialize the store with data on app load ---
useQuizStore.getState().init();