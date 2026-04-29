const OPENAI_ENDPOINT = 'https://api.openai.com/v1/chat/completions';

const MAX_PROMPT_CHARS = Number(process.env.MIRANDA2_MAX_PROMPT_CHARS || 2500);
const MAX_BODY_BYTES = Number(process.env.MIRANDA2_MAX_BODY_BYTES || 12_000);
const RATE_LIMIT_WINDOW_SECONDS = Number(process.env.MIRANDA2_RATE_LIMIT_WINDOW_SECONDS || 60);
const RATE_LIMIT_MAX_REQUESTS = Number(process.env.MIRANDA2_RATE_LIMIT_MAX_REQUESTS || 20);
const DEFAULT_MODEL = String(process.env.MIRANDA2_AI_MODEL || '').trim();
const ALLOWED_MODELS = String(process.env.MIRANDA2_ALLOWED_MODELS || DEFAULT_MODEL)
  .split(',')
  .map((m) => m.trim())
  .filter(Boolean);
const ALLOWED_ORIGINS = String(process.env.MIRANDA2_ALLOWED_ORIGINS || '')
  .split(',')
  .map((origin) => origin.trim())
  .filter(Boolean);

const memoryRateLimit = new Map();

function getClientIp(req) {
  const xff = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim();
  const xri = String(req.headers['x-real-ip'] || '').trim();
  return xff || xri || req.socket?.remoteAddress || 'unknown';
}

function getCorsOrigin(req) {
  const origin = String(req.headers.origin || '').trim();
  if (!origin) return '';
  if (!ALLOWED_ORIGINS.length) return '';
  return ALLOWED_ORIGINS.includes(origin) ? origin : null;
}

function applyCors(req, res) {
  const corsOrigin = getCorsOrigin(req);
  if (corsOrigin === null) return false;
  if (corsOrigin) {
    res.setHeader('Access-Control-Allow-Origin', corsOrigin);
    res.setHeader('Vary', 'Origin');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  }
  return true;
}

async function rateLimitViaUpstash(ip) {
  const url = String(process.env.UPSTASH_REDIS_REST_URL || '').trim();
  const token = String(process.env.UPSTASH_REDIS_REST_TOKEN || '').trim();
  if (!url || !token) return { limited: false, source: 'memory-fallback' };

  const key = `miranda2:ai:rl:${ip}:${Math.floor(Date.now() / (RATE_LIMIT_WINDOW_SECONDS * 1000))}`;
  const headers = { Authorization: `Bearer ${token}` };

  const incrRes = await fetch(`${url}/incr/${encodeURIComponent(key)}`, { headers });
  if (!incrRes.ok) throw new Error(`Upstash INCR failed (${incrRes.status})`);
  const incrJson = await incrRes.json();
  const count = Number(incrJson?.result || 0);

  if (count === 1) {
    await fetch(`${url}/expire/${encodeURIComponent(key)}/${RATE_LIMIT_WINDOW_SECONDS}`, { headers }).catch(() => {});
  }

  return { limited: count > RATE_LIMIT_MAX_REQUESTS, source: 'upstash' };
}

async function isRateLimited(ip) {
  try {
    return await rateLimitViaUpstash(ip);
  } catch (_err) {
    const now = Date.now();
    const bucketStart = Math.floor(now / (RATE_LIMIT_WINDOW_SECONDS * 1000)) * RATE_LIMIT_WINDOW_SECONDS * 1000;
    const key = `${ip}:${bucketStart}`;
    const current = memoryRateLimit.get(key) || 0;
    memoryRateLimit.set(key, current + 1);
    return { limited: current + 1 > RATE_LIMIT_MAX_REQUESTS, source: 'memory-fallback' };
  }
}

function sanitizedUpstreamError(status) {
  if (status === 401 || status === 403) return 'AI provider authentication failed';
  if (status === 429) return 'AI provider rate limit reached';
  if (status >= 500) return 'AI provider is temporarily unavailable';
  return 'AI request failed';
}

module.exports = async (req, res) => {
  if (!applyCors(req, res)) {
    return res.status(403).json({ ok: false, error: 'Origin not allowed' });
  }

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST, OPTIONS');
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  const contentLength = Number(req.headers['content-length'] || 0);
  if (contentLength > MAX_BODY_BYTES) {
    return res.status(413).json({ ok: false, error: 'Request body too large' });
  }

  const ip = getClientIp(req);
  const limited = await isRateLimited(ip);
  if (limited.limited) {
    return res.status(429).json({ ok: false, error: 'Too many requests. Try again shortly.' });
  }

  const apiKey = (process.env.OPENAI_API_KEY || '').trim();
  if (!apiKey) {
    return res.status(500).json({ ok: false, error: 'AI service is not configured on server' });
  }

  const prompt = String(req.body?.prompt || '').trim();
  if (!prompt) {
    return res.status(400).json({ ok: false, error: 'Missing prompt' });
  }
  if (prompt.length > MAX_PROMPT_CHARS) {
    return res.status(400).json({ ok: false, error: `Prompt is too long (max ${MAX_PROMPT_CHARS} chars)` });
  }

  const requestedModel = String(req.body?.model || '').trim();
  const model = requestedModel || DEFAULT_MODEL;
  if (!model) {
    return res.status(500).json({ ok: false, error: 'No AI model configured on server' });
  }
  if (ALLOWED_MODELS.length && !ALLOWED_MODELS.includes(model)) {
    return res.status(400).json({ ok: false, error: 'Model is not allowed' });
  }

  try {
    const upstream = await fetch(OPENAI_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model,
        temperature: 0.9,
        messages: [
          {
            role: 'system',
            content: 'You draft short, sendable text replies. Return only the reply text.'
          },
          { role: 'user', content: prompt }
        ]
      })
    });

    if (!upstream.ok) {
      return res.status(502).json({
        ok: false,
        error: sanitizedUpstreamError(upstream.status),
        provider_status: upstream.status
      });
    }

    const data = await upstream.json();
    const reply = String(data?.choices?.[0]?.message?.content || '').trim();
    if (!reply) {
      return res.status(502).json({ ok: false, error: 'AI provider returned empty reply' });
    }

    return res.status(200).json({ ok: true, reply, model });
  } catch (_err) {
    return res.status(502).json({ ok: false, error: 'AI provider request failed' });
  }
};
