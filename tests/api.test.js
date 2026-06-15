// Tests for api/ai-suggest-reply.js — the Vercel serverless function.
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Helper to build mock req/res objects.
function mockReq(overrides = {}) {
  return {
    method: "POST",
    headers: { "content-length": "100", origin: "", host: "localhost" },
    body: { prompt: "test prompt", model: "" },
    socket: { remoteAddress: "127.0.0.1" },
    ...overrides,
  };
}

function mockRes() {
  const res = {
    _status: null,
    _body: null,
    _headers: {},
    _ended: false,
    status(code) { res._status = code; return res; },
    json(body) { res._body = body; return res; },
    end() { res._ended = true; return res; },
    setHeader(k, v) { res._headers[k] = v; },
  };
  return res;
}

// We need to mock process.env and fetch before importing the module.
let handler;

beforeEach(async () => {
  vi.stubGlobal("fetch", vi.fn());
  // Set required env vars
  process.env.ANTHROPIC_API_KEY = "test-key-123";
  process.env.MIRANDA2_ALLOWED_ORIGINS = "";
  process.env.UPSTASH_REDIS_REST_URL = "";
  process.env.UPSTASH_REDIS_REST_TOKEN = "";

  // Fresh import each time to pick up env changes.
  // Vitest caches modules, so we use dynamic import with cache busting.
  vi.resetModules();
  const mod = await import("../api/ai-suggest-reply.js");
  handler = mod.default;
});

afterEach(() => {
  vi.unstubAllGlobals();
  delete process.env.ANTHROPIC_API_KEY;
  delete process.env.MIRANDA2_ALLOWED_ORIGINS;
});

describe("api/ai-suggest-reply", () => {
  it("rejects non-POST methods", async () => {
    const res = mockRes();
    await handler(mockReq({ method: "GET" }), res);
    expect(res._status).toBe(405);
    expect(res._body.error).toContain("Method not allowed");
  });

  it("handles OPTIONS (CORS preflight)", async () => {
    const res = mockRes();
    await handler(mockReq({ method: "OPTIONS" }), res);
    expect(res._status).toBe(204);
  });

  it("rejects missing prompt", async () => {
    const res = mockRes();
    await handler(mockReq({ body: { prompt: "" } }), res);
    expect(res._status).toBe(400);
    expect(res._body.error).toContain("Missing prompt");
  });

  it("rejects oversized content-length", async () => {
    const res = mockRes();
    await handler(mockReq({ headers: { "content-length": "99999", origin: "", host: "localhost" } }), res);
    expect(res._status).toBe(413);
  });

  it("returns 500 when ANTHROPIC_API_KEY is missing", async () => {
    delete process.env.ANTHROPIC_API_KEY;
    vi.resetModules();
    const mod = await import("../api/ai-suggest-reply.js");
    const res = mockRes();
    await mod.default(mockReq(), res);
    expect(res._status).toBe(500);
    expect(res._body.error).toContain("not configured");
  });

  it("proxies to Anthropic and returns reply on success", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        content: [{ type: "text", text: "sounds good, let's do it" }],
      }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const res = mockRes();
    await handler(mockReq(), res);
    expect(res._status).toBe(200);
    expect(res._body.ok).toBe(true);
    expect(res._body.reply).toBe("sounds good, let's do it");
    // Verify upstream call
    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.anthropic.com/v1/messages",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("returns 502 when Anthropic returns an error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));

    const res = mockRes();
    await handler(mockReq(), res);
    expect(res._status).toBe(502);
    expect(res._body.ok).toBe(false);
  });

  it("returns 502 when Anthropic returns empty content", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ content: [] }),
    }));

    const res = mockRes();
    await handler(mockReq(), res);
    expect(res._status).toBe(502);
    expect(res._body.error).toContain("empty reply");
  });

  it("returns 502 on network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network fail")));

    const res = mockRes();
    await handler(mockReq(), res);
    expect(res._status).toBe(502);
  });

  it("sanitizes upstream 401 to user-friendly message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 401 }));

    const res = mockRes();
    await handler(mockReq(), res);
    expect(res._body.error).toContain("authentication failed");
  });

  it("sanitizes upstream 429 to rate limit message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 429 }));

    const res = mockRes();
    await handler(mockReq(), res);
    expect(res._body.error).toContain("rate limit");
  });
});
