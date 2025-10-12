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
  currentQuizDetails: [],
  isLoading: true,
  feedback: 'Loading your session...',
  isQuizCompleted: false,
  
  // --- NEW STATE FOR DEBRIEF ---
  debriefData: null,
  isDebriefVisible: false,
  
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
    if (get().level === newLevel) return;
    localStorage.setItem(LEVEL_STORAGE_KEY, newLevel);
    set({ level: newLevel, isDebriefVisible: false, debriefData: null }); // <-- Reset debrief on level change
    get().fetchWords(true);
  },
  
  setFeedback: (message) => set({ feedback: message }),
  
  setIsQuizCompleted: (status) => set({ isQuizCompleted: status }),
  
  // --- NEW ACTION ---
  fetchDebriefData: async () => {
    const { level } = get();
    try {
      const data = await api.fetchDailyDebrief(level);
      set({ debriefData: data, isDebriefVisible: true, isLoading: false });
    } catch (error) {
      console.error("Failed to fetch debrief data:", error);
      set({ feedback: "Could not load your daily summary.", isLoading: false });
    }
  },

  fetchWords: async (forceRefetch = false) => {
    set({ isQuizCompleted: false, isDebriefVisible: false }); // <-- Hide debrief when fetching new words

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
        // --- THIS IS THE TRIGGER FOR THE DEBRIEF ---
        set({ feedback: "You're all caught up for today! Here's your summary.", quizItems: [], currentQuizDetails: [] });
        get().fetchDebriefData(); // Fetch and show the debrief
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

  // --- NEW ACTION ---
  toggleStarStatus: async (itemKey) => {
    const { quizItems, selectedWord, debriefData } = get();

    // Find the item to determine its original status. Search in all possible places.
    let originalStatus = false;
    const itemInQuiz = quizItems.find(item => item.key === itemKey);
    const itemInDebrief = debriefData ? 
      [...debriefData.mastered, ...debriefData.progress, ...debriefData.tricky].find(item => item.item_key === itemKey) : null;
    const itemInModal = selectedWord?.item_key === itemKey ? selectedWord : null;

    if (itemInQuiz) {
      originalStatus = itemInQuiz.fullDetails?.is_starred ?? false;
    } else if (itemInDebrief) {
      originalStatus = itemInDebrief.is_starred ?? false;
    } else if (itemInModal) {
      originalStatus = itemInModal.is_starred ?? false;
    }
    
    const newStatus = !originalStatus;

    // --- Create a reusable state update function for optimistic UI and rollbacks ---
    const updateState = (status) => {
      set(state => {
        // 1. Update quizItems list
        const updatedQuizItems = state.quizItems.map(item =>
          item.key === itemKey
            ? { ...item, fullDetails: { ...item.fullDetails, is_starred: status } }
            : item
        );
        
        // 2. Update selectedWord in the modal
        const updatedSelectedWord = state.selectedWord && state.selectedWord.item_key === itemKey
          ? { ...state.selectedWord, is_starred: status }
          : state.selectedWord;

        // 3. (THE FIX) Update debriefData if it exists
        let updatedDebriefData = state.debriefData;
        if (state.debriefData) {
          const updateArray = (arr) => arr.map(item =>
            item.item_key === itemKey ? { ...item, is_starred: status } : item
          );
          updatedDebriefData = {
            mastered: updateArray(state.debriefData.mastered),
            progress: updateArray(state.debriefData.progress),
            tricky: updateArray(state.debriefData.tricky),
          };
        }

        return {
          quizItems: updatedQuizItems,
          selectedWord: updatedSelectedWord,
          debriefData: updatedDebriefData,
        };
      });
    };

    // --- Perform Optimistic UI Update ---
    updateState(newStatus);

    // --- API Call ---
    try {
      await api.updateStarStatus(itemKey, newStatus);
      // On success, the optimistic state is correct.
    } catch (error) {
      console.error("Failed to update star status:", error);
      // --- Rollback on failure ---
      updateState(originalStatus); 
    }
  },
}));

// --- Initialize the store with data on app load ---
useQuizStore.getState().init();