const OPENAI_ENDPOINT = 'https://api.openai.com/v1/chat/completions';
const DEFAULT_MODEL = process.env.MIRANDA2_AI_MODEL || 'gpt-4.1-mini';

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  const apiKey = (process.env.OPENAI_API_KEY || '').trim();
  if (!apiKey) {
    return res.status(500).json({ ok: false, error: 'Missing OPENAI_API_KEY on server' });
  }

  const prompt = String(req.body?.prompt || '').trim();
  if (!prompt) {
    return res.status(400).json({ ok: false, error: 'Missing prompt' });
  }

  const model = String(req.body?.model || DEFAULT_MODEL).trim() || DEFAULT_MODEL;

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
      const raw = await upstream.text().catch(() => '');
      return res.status(502).json({
        ok: false,
        error: `OpenAI request failed (${upstream.status}): ${raw.slice(0, 300)}`
      });
    }

    const data = await upstream.json();
    const reply = String(data?.choices?.[0]?.message?.content || '').trim();
    if (!reply) {
      return res.status(502).json({ ok: false, error: 'OpenAI returned empty reply' });
    }

    return res.status(200).json({ ok: true, reply });
  } catch (err) {
    return res.status(502).json({ ok: false, error: `OpenAI request failed: ${String(err?.message || err)}` });
  }
};
