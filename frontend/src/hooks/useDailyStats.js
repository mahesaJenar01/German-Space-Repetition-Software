import { useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';

export const useDailyStats = () => {
  const [practicedToday, setPracticedToday] = useState(0);
  const [todayStats, setTodayStats] = useState({ correct_by_level: {}, wrong_by_level: {} });

  const refreshStats = useCallback(async () => {
    try {
      const count = await api.fetchPracticedTodayCount();
      setPracticedToday(count);
      const stats = await api.fetchTodayStats();
      setTodayStats(stats);
    } catch (error) {
      console.error("Failed to fetch daily stats:", error);
    }
  }, []);

  useEffect(() => {
    refreshStats();
  }, [refreshStats]);

  return { practicedToday, todayStats, refreshStats };
};