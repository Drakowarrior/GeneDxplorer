const HISTORY_KEY = 'genedxplorer_search_history';
const MAX_HISTORY = 10;

export function getSearchHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.warn('[SearchHistory] Error parsing search history:', err);
    return [];
  }
}

export function addSearchHistory(query, type = 'disease') {
  if (!query || !query.trim()) return [];
  const cleanQuery = query.trim();

  try {
    const history = getSearchHistory();
    // Deduplicate
    const filtered = history.filter(
      (item) => !(item.query.toLowerCase() === cleanQuery.toLowerCase() && item.type === type)
    );

    const newItem = {
      query: cleanQuery,
      type: type, // 'disease' or 'gene'
      timestamp: new Date().toISOString(),
    };

    const updated = [newItem, ...filtered].slice(0, MAX_HISTORY);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
    return updated;
  } catch (err) {
    console.warn('[SearchHistory] Error adding to search history:', err);
    return [];
  }
}

export function clearSearchHistory() {
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch (err) {
    console.warn('[SearchHistory] Error clearing search history:', err);
  }
  return [];
}
