import { useState, useEffect, useCallback } from 'react';

const getTodayString = () => new Date().toISOString().split('T')[0];

export const useDailyProgress = (level, dailySessionInfo) => { // <-- RECEIVE SESSION INFO
  const getStorageKey = useCallback(() => `dailyProgress_${level}_${getTodayString()}`, [level]);

  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [wordStats, setWordStats] = useState({});

  useEffect(() => {
    if (!dailySessionInfo) return; // Wait for session info to be loaded

    try {
        const key = getStorageKey();
        const savedData = localStorage.getItem(key);
        if (savedData) {
            const { progress: savedProgress, wordStats: savedWordStats } = JSON.parse(savedData);
            setProgress(savedProgress);
            setWordStats(savedWordStats);
        } else {
            // --- THIS IS THE FIX: Calculate initial total dynamically ---
            const effectiveWordCount = Math.min(dailySessionInfo.daily_word_limit, dailySessionInfo.total_words_in_level);
            const initialTotal = effectiveWordCount * dailySessionInfo.mastery_goal;
            setProgress({ current: 0, total: initialTotal });
            setWordStats({});
        }
    } catch (error) {
        console.error("Failed to load daily progress from localStorage", error);
        setProgress({ current: 0, total: 0 });
        setWordStats({});
    }
  }, [level, getStorageKey, dailySessionInfo]); // Depend on dailySessionInfo

  const updateProgress = useCallback((results) => {
    if (!dailySessionInfo) return; // Safety check

     setWordStats(currentWordStats => {
        let newWordStats = { ...currentWordStats };
        let currentTotal = progress.total;
        let currentProgressValue = progress.current;

        results.forEach(result => {
            if (!newWordStats[result.word]) {
                newWordStats[result.word] = { consecutiveCorrect: 0, totalWrong: 0, isDone: false };
            }
        });

        results.forEach(result => {
            const word = result.word;
            const stats = newWordStats[word];
            if (stats.isDone) return;

            const isCorrect = result.result_type === 'PERFECT_MATCH';
            if (isCorrect) {
                currentProgressValue += 1;
                stats.consecutiveCorrect += 1;
                if (stats.consecutiveCorrect >= dailySessionInfo.mastery_goal) stats.isDone = true;
            } else {
                currentTotal += 1;
                stats.consecutiveCorrect = 0;
                stats.totalWrong += 1;
                if (stats.totalWrong >= dailySessionInfo.failure_threshold) {
                    stats.isDone = true;
                    currentTotal -= dailySessionInfo.mastery_goal;
                }
            }
        });
        
        const newProgress = { current: currentProgressValue, total: currentTotal };
        setProgress(newProgress);
        localStorage.setItem(getStorageKey(), JSON.stringify({ progress: newProgress, wordStats: newWordStats }));

        return newWordStats;
    });


  }, [progress, getStorageKey, dailySessionInfo]);

  return { progress, updateProgress };
};