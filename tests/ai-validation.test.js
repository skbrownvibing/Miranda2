// Tests for AI reply validation, prompt building, and content filters.
import { describe, it, expect } from "vitest";
import { createSandbox } from "./sandbox.js";

const ctx = createSandbox();

// ── containsBannedPreamble ──

describe("containsBannedPreamble", () => {
  it("detects 'here's a reply'", () => {
    expect(ctx.containsBannedPreamble("Here's a reply for you")).toBe(true);
  });
  it("detects 'you could say'", () => {
    expect(ctx.containsBannedPreamble("you could say something like")).toBe(true);
  });
  it("detects 'I apologize for the delay'", () => {
    expect(ctx.containsBannedPreamble("I apologize for the delay in responding")).toBe(true);
  });
  it("passes clean text", () => {
    expect(ctx.containsBannedPreamble("sounds good, let's do it")).toBe(false);
  });
});

// ── hasGreetingOrSignoff ──

describe("hasGreetingOrSignoff", () => {
  it("detects 'Hey' at start", () => {
    expect(ctx.hasGreetingOrSignoff("Hey there")).toBe(true);
  });
  it("detects 'Best' at end", () => {
    expect(ctx.hasGreetingOrSignoff("talk soon best")).toBe(true);
  });
  it("detects 'thanks for'", () => {
    expect(ctx.hasGreetingOrSignoff("thanks for reaching out")).toBe(true);
  });
  it("passes casual text", () => {
    expect(ctx.hasGreetingOrSignoff("sounds good")).toBe(false);
  });
});

// ── looksAssistantLike ──

describe("looksAssistantLike", () => {
  it("detects 'absolutely'", () => {
    expect(ctx.looksAssistantLike("Absolutely, I can help with that")).toBe(true);
  });
  it("detects 'happy to help'", () => {
    expect(ctx.looksAssistantLike("I'm happy to help")).toBe(true);
  });
  it("detects 'let me know'", () => {
    expect(ctx.looksAssistantLike("let me know if you need more")).toBe(true);
  });
  it("passes casual text", () => {
    expect(ctx.looksAssistantLike("yeah that works")).toBe(false);
  });
});

// ── stripWrappingQuotes ──

describe("stripWrappingQuotes", () => {
  it("strips double quotes", () => {
    expect(ctx.stripWrappingQuotes('"hello"')).toBe("hello");
  });
  it("strips smart double quotes", () => {
    expect(ctx.stripWrappingQuotes("\u201Chello\u201D")).toBe("hello");
  });
  it("strips smart single quotes", () => {
    expect(ctx.stripWrappingQuotes("\u2018hello\u2019")).toBe("hello");
  });
  it("strips nested wrapping (up to 2 layers)", () => {
    expect(ctx.stripWrappingQuotes("\"'hello'\"")).toBe("hello");
  });
  it("leaves non-wrapped text alone", () => {
    expect(ctx.stripWrappingQuotes("hello")).toBe("hello");
  });
  it("handles null/empty", () => {
    expect(ctx.stripWrappingQuotes("")).toBe("");
    expect(ctx.stripWrappingQuotes(null)).toBe("");
  });
});

// ── buildReplyContext ──

describe("buildReplyContext", () => {
  it("filters out attachment messages and limits to 6", () => {
    const thread = {
      messages: [
        { from_me: false, text: "hello" },
        { from_me: true, text: "📎 Attachment" },
        { from_me: true, text: "hey" },
        { from_me: false, text: "what's up" },
        { from_me: true, text: "not much" },
        { from_me: false, text: "cool" },
        { from_me: true, text: "yeah" },
        { from_me: false, text: "ok" },
      ],
    };
    const result = ctx.buildReplyContext(thread);
    expect(result.length).toBeLessThanOrEqual(6);
    // Attachment should be excluded
    expect(result.every((m) => m.text !== "📎 Attachment")).toBe(true);
  });
  it("labels speakers correctly", () => {
    const thread = {
      messages: [
        { from_me: false, text: "hey" },
        { from_me: true, text: "yo" },
      ],
    };
    const result = ctx.buildReplyContext(thread);
    expect(result[0]).toEqual({ speaker: "Them", text: "hey" });
    expect(result[1]).toEqual({ speaker: "Me", text: "yo" });
  });
  it("returns empty for no messages", () => {
    expect(ctx.buildReplyContext({})).toEqual([]);
  });
});

// ── buildAiPrompt ──

describe("buildAiPrompt", () => {
  it("includes conversation context and latest inbound", () => {
    const context = [
      { speaker: "Them", text: "hey what's up" },
      { speaker: "Me", text: "not much" },
    ];
    const prompt = ctx.buildAiPrompt(context, "hey what's up");
    expect(prompt).toContain("Them: hey what's up");
    expect(prompt).toContain("Me: not much");
    expect(prompt).toContain("Latest inbound message:");
    expect(prompt).toContain("hey what's up");
    expect(prompt).toContain("Reply:");
  });
});

// ── validateAiReply ──

describe("validateAiReply", () => {
  const thread = {
    messages: [
      { from_me: false, text: "what do you think about dinner tonight?" },
    ],
  };

  it("accepts a good short reply", () => {
    expect(ctx.validateAiReply("sounds good, where?", thread))
      .toEqual({ valid: true, reason: "ok" });
  });
  it("rejects empty", () => {
    expect(ctx.validateAiReply("", thread).valid).toBe(false);
    expect(ctx.validateAiReply("", thread).reason).toBe("empty");
  });
  it("rejects single word (near-empty)", () => {
    expect(ctx.validateAiReply("ok", thread).reason).toBe("near-empty");
  });
  it("rejects em-dash", () => {
    expect(ctx.validateAiReply("sure — sounds great", thread).reason).toBe("em-dash");
  });
  it("rejects smart quotes", () => {
    expect(ctx.validateAiReply("that\u2019s a \u201Cbig\u201D mood", thread).reason).toBe("quotes");
  });
  it("rejects banned preamble", () => {
    expect(ctx.validateAiReply("Here's a reply you could use for dinner tonight", thread).reason).toBe("preamble");
  });
  it("rejects greeting/signoff", () => {
    expect(ctx.validateAiReply("Hey there, sounds good for dinner tonight!", thread).reason).toBe("greeting-signoff");
  });
  it("rejects assistant tone", () => {
    expect(ctx.validateAiReply("Absolutely, I'd love to do dinner tonight", thread).reason).toBe("assistant-tone");
  });
  it("rejects multi-line", () => {
    expect(ctx.validateAiReply("option 1\noption 2", thread).reason).toBe("multiple-options");
  });
  it("rejects 'option 1' phrasing", () => {
    expect(ctx.validateAiReply("you could go with option 1 for dinner", thread).reason).toBe("multiple-options");
  });
});

// ── aiReplyBlockReason ──

describe("aiReplyBlockReason", () => {
  it("blocks threads not on allowlist", () => {
    expect(ctx.aiReplyBlockReason({ id: "unknown-thread" }))
      .toBe("Not on demo allowlist");
  });
  it("blocks when latest visible is from_me", () => {
    const thread = {
      id: "iMessage;-;+12125550101",
      messages: [
        { from_me: false, text: "hey" },
        { from_me: true, text: "sup" },
      ],
    };
    expect(ctx.aiReplyBlockReason(thread)).toBe("Need an incoming text to reply to");
  });
  it("allows when latest visible is inbound", () => {
    const thread = {
      id: "iMessage;-;+12125550101",
      messages: [
        { from_me: true, text: "hey" },
        { from_me: false, text: "what's up?" },
      ],
    };
    expect(ctx.aiReplyBlockReason(thread)).toBe("");
  });
});

// ── isAiReplyAllowed ──

describe("isAiReplyAllowed", () => {
  it("returns true when block reason is empty", () => {
    const thread = {
      id: "iMessage;-;+12125550101",
      messages: [{ from_me: false, text: "hey" }],
    };
    expect(ctx.isAiReplyAllowed(thread)).toBe(true);
  });
  it("returns false for non-allowlisted thread", () => {
    expect(ctx.isAiReplyAllowed({ id: "nope" })).toBe(false);
  });
});
