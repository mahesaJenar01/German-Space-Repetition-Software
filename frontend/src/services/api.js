const API_URL = 'http://127.0.0.1:5000';

export const fetchWordDetails = async (level) => {
  const response = await fetch(`${API_URL}/api/words/details/${level}`);
  if (!response.ok) throw new Error('Network response for word details was not ok');
  return response.json();
};

export const fetchWordStats = async (words, level) => {
  const response = await fetch(`${API_URL}/api/stats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ words, level }),
  });
  if (!response.ok) throw new Error('Network response for word stats was not ok');
  return response.json();
};

export const updateWordStats = async (level, results) => {
  const response = await fetch(`${API_URL}/api/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ level, results }),
  });
  if (!response.ok) throw new Error('Failed to update stats');
  return response.json();
};

export const fetchPracticedTodayCount = async () => {
    const response = await fetch(`${API_URL}/api/report/today`);
    if (!response.ok) throw new Error('Failed to fetch daily stats');
    const data = await response.json();
    return data.practiced_today || 0;
};

export const fetchTodayStats = async () => {
    const response = await fetch(`${API_URL}/api/report/today_stats`);
    if (!response.ok) throw new Error('Failed to fetch today\'s accuracy stats');
    return response.json();
};

// --- THIS FUNCTION WAS MISSING ---
export const updateStarStatus = async (item_key, is_starred) => {
  const response = await fetch(`${API_URL}/api/word/star`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_key, is_starred }),
  });
  if (!response.ok) throw new Error('Failed to update star status');
  return response.json();
};