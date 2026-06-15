// Tests for formatting / display helpers in app.js.
import { describe, it, expect, vi } from "vitest";
import { createSandbox } from "./sandbox.js";

const ctx = createSandbox();

// ── esc ──

describe("esc", () => {
  it("escapes &, <, >, double-quote, single-quote", () => {
    expect(ctx.esc('<a href="x">&\'')).toBe(
      '&lt;a href=&quot;x&quot;&gt;&amp;&#39;'
    );
  });
  it("returns plain strings unchanged", () => {
    expect(ctx.esc("hello world")).toBe("hello world");
  });
  it("handles null/undefined", () => {
    expect(ctx.esc(null)).toBe("");
    expect(ctx.esc(undefined)).toBe("");
  });
});

// ── scoreColor ──

describe("scoreColor", () => {
  it("returns green for 85+", () => {
    expect(ctx.scoreColor(85)).toBe("var(--green)");
    expect(ctx.scoreColor(100)).toBe("var(--green)");
  });
  it("returns yellow for 65–84", () => {
    expect(ctx.scoreColor(65)).toBe("var(--yellow)");
    expect(ctx.scoreColor(84)).toBe("var(--yellow)");
  });
  it("returns orange for 40–64", () => {
    expect(ctx.scoreColor(40)).toBe("var(--orange)");
    expect(ctx.scoreColor(64)).toBe("var(--orange)");
  });
  it("returns red for <40", () => {
    expect(ctx.scoreColor(39)).toBe("var(--red)");
    expect(ctx.scoreColor(0)).toBe("var(--red)");
  });
});

// ── fmtSpeed ──

describe("fmtSpeed", () => {
  it("returns <1h for sub-hour", () => {
    expect(ctx.fmtSpeed(0.5)).toBe("<1h");
  });
  it("rounds hours", () => {
    expect(ctx.fmtSpeed(2.7)).toBe("3h");
    expect(ctx.fmtSpeed(24)).toBe("24h");
  });
});

// ── scoreLabel ──

describe("scoreLabel", () => {
  it("returns ghosting for <=15", () => {
    expect(ctx.scoreLabel(15)).toContain("ghosting");
    expect(ctx.scoreLabel(0)).toContain("ghosting");
  });
  it("returns bad texter for 16–35", () => {
    expect(ctx.scoreLabel(35)).toContain("bad texter");
  });
  it("returns hit or miss for 36–55", () => {
    expect(ctx.scoreLabel(55)).toContain("hit or miss");
  });
  it("returns solid for 56–75", () => {
    expect(ctx.scoreLabel(75)).toContain("solid");
  });
  it("returns on it for 76–90", () => {
    expect(ctx.scoreLabel(90)).toContain("on it");
  });
  it("returns ELITE for 91+", () => {
    expect(ctx.scoreLabel(91)).toContain("ELITE");
  });
});

// ── cleanScoreLabel ──

describe("cleanScoreLabel", () => {
  it("strips trailing (N)", () => {
    expect(ctx.cleanScoreLabel("solid 👍 (12)")).toBe("solid 👍");
  });
  it("returns the label untouched when no trailing number", () => {
    expect(ctx.cleanScoreLabel("ELITE responder 🏆")).toBe("ELITE responder 🏆");
  });
  it("handles null/undefined", () => {
    expect(ctx.cleanScoreLabel(null)).toBe("");
  });
});

// ── displayName ──

describe("displayName", () => {
  it("prefers group_name for groups", () => {
    expect(ctx.displayName({ is_group: true, group_name: "Family Chat", contact_name: "Mom" }))
      .toBe("Family Chat");
  });
  it("falls back to contact_name", () => {
    expect(ctx.displayName({ contact_name: "Alice" })).toBe("Alice");
  });
  it("falls back to phone", () => {
    expect(ctx.displayName({ phone: "+1234567890" })).toBe("+1234567890");
  });
  it("falls back to Unknown", () => {
    expect(ctx.displayName({})).toBe("Unknown");
  });
  it("ignores blank group_name", () => {
    expect(ctx.displayName({ is_group: true, group_name: "  ", contact_name: "Bob" }))
      .toBe("Bob");
  });
});

// ── initial ──

describe("initial", () => {
  it("returns first letter uppercased", () => {
    expect(ctx.initial({ contact_name: "alice" })).toBe("A");
  });
  it("works for groups", () => {
    expect(ctx.initial({ is_group: true, group_name: "team" })).toBe("T");
  });
});

// ── fullTime ──

describe("fullTime", () => {
  it("returns empty for falsy", () => {
    expect(ctx.fullTime("")).toBe("");
    expect(ctx.fullTime(null)).toBe("");
  });
  it("formats an ISO date", () => {
    const result = ctx.fullTime("2025-03-15T14:30:00Z");
    expect(result).toBeTruthy();
    expect(result).toContain("Mar");
    expect(result).toContain("15");
  });
});

// ── localDateKey ──

describe("localDateKey", () => {
  it("returns YYYY-MM-DD", () => {
    const d = new Date(2025, 0, 5);
    expect(ctx.localDateKey(d)).toBe("2025-01-05");
  });
  it("pads single-digit month and day", () => {
    const d = new Date(2025, 5, 3);
    expect(ctx.localDateKey(d)).toBe("2025-06-03");
  });
});

// ── normFirstName ──

describe("normFirstName", () => {
  it("extracts first word and strips non-alpha", () => {
    expect(ctx.normFirstName("Sarah Brown")).toBe("Sarah");
  });
  it("handles punctuation", () => {
    expect(ctx.normFirstName("O'Brien-Smith Jr")).toBe("O'Brien-Smith");
  });
  it("returns empty for empty/null", () => {
    expect(ctx.normFirstName("")).toBe("");
    expect(ctx.normFirstName(null)).toBe("");
  });
  it("truncates at 30 chars", () => {
    expect(ctx.normFirstName("A".repeat(50)).length).toBeLessThanOrEqual(30);
  });
});

// ── latestEventAt / latestEventText / literalRecentEvents ──

describe("latestEventAt", () => {
  it("returns last_message_at", () => {
    expect(ctx.latestEventAt({ last_message_at: "2025-01-01T00:00:00Z" }))
      .toBe("2025-01-01T00:00:00Z");
  });
  it("returns null when missing", () => {
    expect(ctx.latestEventAt({})).toBeNull();
  });
});

describe("latestEventText", () => {
  it("returns last_message_text", () => {
    expect(ctx.latestEventText({ last_message_text: "hi" })).toBe("hi");
  });
  it("returns empty string when missing", () => {
    expect(ctx.latestEventText({})).toBe("");
  });
});

describe("literalRecentEvents", () => {
  it("returns last 5 messages", () => {
    const msgs = Array.from({ length: 8 }, (_, i) => ({ text: `m${i}` }));
    expect(ctx.literalRecentEvents({ messages: msgs })).toHaveLength(5);
    expect(ctx.literalRecentEvents({ messages: msgs })[0].text).toBe("m3");
  });
  it("handles missing messages", () => {
    expect(ctx.literalRecentEvents({})).toEqual([]);
  });
});

// ── buildSmsHref ──

describe("buildSmsHref", () => {
  it("returns sms: link with body", () => {
    expect(ctx.buildSmsHref("+1234567890", "hey there")).toBe(
      "sms:+1234567890&body=hey%20there"
    );
  });
  it("returns sms: link without body when empty", () => {
    expect(ctx.buildSmsHref("+1234567890", "")).toBe("sms:+1234567890");
  });
  it("returns # for empty phone", () => {
    expect(ctx.buildSmsHref("", "text")).toBe("#");
  });
});
