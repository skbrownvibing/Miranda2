// Tests for normalization, dismiss-key logic, and content classification.
import { describe, it, expect } from "vitest";
import { createSandbox } from "./sandbox.js";

const ctx = createSandbox();

// ── normalizeIdentityToken ──

describe("normalizeIdentityToken", () => {
  it("lowercases and trims", () => {
    expect(ctx.normalizeIdentityToken("  Alice  ")).toBe("alice");
  });
  it("returns empty for null", () => {
    expect(ctx.normalizeIdentityToken(null)).toBe("");
  });
});

// ── normalizeHandleValue ──

describe("normalizeHandleValue", () => {
  it("strips non-digits from phone numbers", () => {
    expect(ctx.normalizeHandleValue("+1 (234) 567-8901")).toBe("12345678901");
  });
  it("preserves email addresses", () => {
    expect(ctx.normalizeHandleValue("Alice@Example.com")).toBe("alice@example.com");
  });
  it("returns empty for blank", () => {
    expect(ctx.normalizeHandleValue("")).toBe("");
    expect(ctx.normalizeHandleValue(null)).toBe("");
  });
});

// ── participantDismissKey ──

describe("participantDismissKey", () => {
  it("returns phone-based key for 1:1 with phone", () => {
    expect(ctx.participantDismissKey({ phone: "+1234567890" }))
      .toBe("p:1234567890");
  });
  it("returns name-based key for 1:1 without phone", () => {
    expect(ctx.participantDismissKey({ contact_name: "Alice" }))
      .toBe("p:name:alice");
  });
  it("returns id-based key as last resort", () => {
    expect(ctx.participantDismissKey({ id: "thread-99" }))
      .toBe("p:id:thread-99");
  });
  it("returns group key with name and phone", () => {
    expect(ctx.participantDismissKey({ is_group: true, group_name: "Family", phone: "+111" }))
      .toBe("g:family|111");
  });
  it("returns group id-based key when no name/phone", () => {
    expect(ctx.participantDismissKey({ is_group: true, id: "g1" }))
      .toBe("g:id:g1");
  });
  it("returns empty for null", () => {
    expect(ctx.participantDismissKey(null)).toBe("");
  });
});

// ── isRealTextMessageContent ──

describe("isRealTextMessageContent", () => {
  it("returns true for normal text", () => {
    expect(ctx.isRealTextMessageContent("Hey!")).toBe(true);
  });
  it("returns false for attachment placeholder", () => {
    expect(ctx.isRealTextMessageContent("📎 Attachment")).toBe(false);
  });
  it("returns false for empty/null", () => {
    expect(ctx.isRealTextMessageContent("")).toBe(false);
    expect(ctx.isRealTextMessageContent(null)).toBe(false);
  });
});

// ── isPlainTextMessage ──

describe("isPlainTextMessage", () => {
  it("returns true for normal text message", () => {
    expect(ctx.isPlainTextMessage({ text: "hello" })).toBe(true);
  });
  it("returns false for attachment", () => {
    expect(ctx.isPlainTextMessage({ text: "📎 Attachment" })).toBe(false);
  });
  it("returns false for empty", () => {
    expect(ctx.isPlainTextMessage({ text: "" })).toBe(false);
    expect(ctx.isPlainTextMessage({})).toBe(false);
  });
});

// ── latestInboundTextAt ──

describe("latestInboundTextAt", () => {
  it("prefers latest_inbound_at field", () => {
    const c = { latest_inbound_at: "2025-06-01T12:00:00Z", messages: [] };
    expect(ctx.latestInboundTextAt(c)).toBe("2025-06-01T12:00:00.000Z");
  });
  it("falls back to scanning messages", () => {
    const c = {
      messages: [
        { from_me: true, text: "hi", date: "2025-06-01T10:00:00Z" },
        { from_me: false, text: "hey", date: "2025-06-01T11:00:00Z" },
        { from_me: false, text: "sup", date: "2025-06-01T12:00:00Z" },
      ],
    };
    expect(ctx.latestInboundTextAt(c)).toBe("2025-06-01T12:00:00.000Z");
  });
  it("ignores attachment-only inbound messages", () => {
    const c = {
      messages: [
        { from_me: false, text: "📎 Attachment", date: "2025-06-01T12:00:00Z" },
      ],
    };
    expect(ctx.latestInboundTextAt(c)).toBeNull();
  });
  it("returns null for empty conversations", () => {
    expect(ctx.latestInboundTextAt({})).toBeNull();
    expect(ctx.latestInboundTextAt({ messages: [] })).toBeNull();
  });
});

// ── hasNewInboundSinceCheckpoint ──

describe("hasNewInboundSinceCheckpoint", () => {
  it("returns false when no inbound", () => {
    expect(ctx.hasNewInboundSinceCheckpoint({}, { inboundCheckpointAt: "2025-01-01T00:00:00Z" }))
      .toBe(false);
  });
  it("returns true when inbound is newer than checkpoint", () => {
    const c = { latest_inbound_at: "2025-06-15T10:00:00Z" };
    const rec = { inboundCheckpointAt: "2025-06-10T10:00:00Z" };
    expect(ctx.hasNewInboundSinceCheckpoint(c, rec)).toBe(true);
  });
  it("returns false when inbound is older than checkpoint", () => {
    const c = { latest_inbound_at: "2025-06-05T10:00:00Z" };
    const rec = { inboundCheckpointAt: "2025-06-10T10:00:00Z" };
    expect(ctx.hasNewInboundSinceCheckpoint(c, rec)).toBe(false);
  });
  it("falls back to dismissedAt for legacy records without checkpoint", () => {
    const c = { latest_inbound_at: "2025-06-15T10:00:00Z" };
    const rec = { dismissedAt: "2025-06-10T10:00:00Z" };
    expect(ctx.hasNewInboundSinceCheckpoint(c, rec)).toBe(true);
  });
});

// ── isHighConfidenceRideshare ──

describe("isHighConfidenceRideshare", () => {
  it("detects Lyft trip notification", () => {
    expect(ctx.isHighConfidenceRideshare("lyft: your driver is arriving in 3 min")).toBe(true);
  });
  it("detects Uber trip notification", () => {
    expect(ctx.isHighConfidenceRideshare("uber trip with john, look for the silver car")).toBe(true);
  });
  it("rejects non-rideshare text", () => {
    expect(ctx.isHighConfidenceRideshare("hey want to grab uber eats?")).toBe(false);
  });
  it("rejects text with only brand but no txn keywords", () => {
    expect(ctx.isHighConfidenceRideshare("lyft is a great app")).toBe(false);
  });
});

// ── previewTextIncluded ──

describe("previewTextIncluded", () => {
  it("includes normal text", () => {
    expect(ctx.previewTextIncluded("hello")).toBe(true);
  });
  it("excludes empty/null", () => {
    expect(ctx.previewTextIncluded("")).toBe(false);
    expect(ctx.previewTextIncluded(null)).toBe(false);
  });
});

// ── previewRows ──

describe("previewRows", () => {
  it("returns last 2 non-attachment messages", () => {
    const c = {
      messages: [
        { from_me: false, text: "hey" },
        { from_me: true, text: "📎 Attachment" },
        { from_me: true, text: "ok" },
        { from_me: false, text: "cool" },
      ],
    };
    const rows = ctx.previewRows(c);
    expect(rows).toHaveLength(2);
    expect(rows[0]).toEqual({ from_me: true, text: "ok" });
    expect(rows[1]).toEqual({ from_me: false, text: "cool" });
  });
  it("handles empty messages", () => {
    expect(ctx.previewRows({})).toEqual([]);
  });
});

// ── recentInboundText ──

describe("recentInboundText", () => {
  it("joins last 3 inbound messages", () => {
    const c = {
      messages: [
        { from_me: true, text: "outbound" },
        { from_me: false, text: "Hi there" },
        { from_me: false, text: "How are you?" },
      ],
    };
    expect(ctx.recentInboundText(c)).toBe("hi there how are you?");
  });
  it("returns empty for no messages", () => {
    expect(ctx.recentInboundText({})).toBe("");
  });
});

// ── looksConversational ──

describe("looksConversational", () => {
  it("scores higher with two-way messages and pronouns", () => {
    const c = {
      messages: [
        { from_me: true, text: "I think so" },
        { from_me: false, text: "Do you want to?" },
      ],
    };
    expect(ctx.looksConversational(c)).toBeGreaterThanOrEqual(3);
  });
  it("scores low for one-way traffic", () => {
    const c = {
      messages: [
        { from_me: false, text: "verification code 123456" },
      ],
    };
    expect(ctx.looksConversational(c)).toBeLessThanOrEqual(1);
  });
});

// ── latestVisibleTextMessage ──

describe("latestVisibleTextMessage", () => {
  it("returns the last plain text message", () => {
    const thread = {
      messages: [
        { text: "hello", from_me: false },
        { text: "📎 Attachment", from_me: false },
      ],
    };
    expect(ctx.latestVisibleTextMessage(thread)).toEqual({ text: "hello", from_me: false });
  });
  it("returns null when all are attachments", () => {
    const thread = { messages: [{ text: "📎 Attachment" }] };
    expect(ctx.latestVisibleTextMessage(thread)).toBeNull();
  });
  it("returns null for empty thread", () => {
    expect(ctx.latestVisibleTextMessage({})).toBeNull();
  });
});
