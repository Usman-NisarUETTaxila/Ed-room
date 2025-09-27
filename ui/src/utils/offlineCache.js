// Simple offline cache and canned responses for the chat app
// Uses localStorage to persist recent Q&A so the UI can continue working temporarily offline

const STORAGE_KEY = 'edroom_offline_cache_v1';
const MAX_ENTRIES = 100; // prevent unbounded growth

function loadCache() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: 1, entries: [] };
    const parsed = JSON.parse(raw);
    if (!parsed.entries || !Array.isArray(parsed.entries)) return { version: 1, entries: [] };
    return parsed;
  } catch (e) {
    return { version: 1, entries: [] };
  }
}

function saveCache(cache) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cache));
  } catch (e) {
    // ignore quota errors silently
  }
}

function normalizeKey(text) {
  if (!text) return '';
  return String(text)
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/[^\p{L}\p{N}\s]/gu, '')
    .trim();
}

export function putToCache(userMessage, botPayload) {
  const cache = loadCache();
  const key = normalizeKey(userMessage);
  const now = Date.now();

  // remove existing with same key
  cache.entries = cache.entries.filter(e => e.key !== key);
  cache.entries.unshift({
    key,
    value: {
      // store only what we need to render quickly
      bot_response: botPayload?.bot_response || '',
      explanation_result: botPayload?.explanation_result || null,
    },
    timestamp: now,
  });

  // cap size
  if (cache.entries.length > MAX_ENTRIES) {
    cache.entries = cache.entries.slice(0, MAX_ENTRIES);
  }
  saveCache(cache);
}

function jaccardSimilarity(a, b) {
  const setA = new Set(a.split(' '));
  const setB = new Set(b.split(' '));
  const intersection = new Set([...setA].filter(x => setB.has(x)));
  const union = new Set([...setA, ...setB]);
  return union.size === 0 ? 0 : intersection.size / union.size;
}

export function getFromCache(userMessage) {
  const cache = loadCache();
  const key = normalizeKey(userMessage);

  // exact
  const exact = cache.entries.find(e => e.key === key);
  if (exact) return exact.value;

  // fuzzy fallback: simple token overlap
  let best = null;
  let bestScore = 0;
  for (const e of cache.entries) {
    const score = jaccardSimilarity(key, e.key);
    if (score > bestScore) {
      best = e;
      bestScore = score;
    }
  }
  if (best && bestScore >= 0.5) return best.value; // moderate threshold
  return null;
}

export function getCannedResponse(userMessage) {
  const templates = [
    {
      title: 'Summary:',
      body: 'You appear to be offline. Here is a helpful, temporary response so you can keep working.'
    },
    {
      title: 'Key Points:',
      list: [
        'This is an offline fallback message generated locally.',
        'Your original input is preserved below.',
        'Reconnect to get fresh, AI-generated results.'
      ]
    },
    {
      title: 'Your Input:',
      body: userMessage || 'N/A'
    },
    {
      title: 'Details (JSON):',
      json: {
        source: 'offline-cache',
        freshness: 'temporary',
        confidence: 0.0,
        recommendation: 'Retry when connection is restored'
      }
    }
  ];

  // Build a single markdown-ish string compatible with MessageFormatter
  const parts = [];
  templates.forEach(t => {
    if (t.title) parts.push(`${t.title}`);
    if (t.body) parts.push(t.body);
    if (t.list && t.list.length) {
      t.list.forEach(item => parts.push(`- ${item}`));
    }
    if (t.json) {
      parts.push('```json');
      parts.push(JSON.stringify(t.json, null, 2));
      parts.push('```');
    }
    parts.push(''); // blank line between sections
  });

  return {
    bot_response: parts.join('\n'),
    explanation_result: null,
  };
}

export function annotateOffline(text) {
  const banner = '**[Offline Mode]** Using cached/canned response.\n\n';
  return banner + (text || '');
}
