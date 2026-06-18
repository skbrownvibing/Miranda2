// Tests for scoring logic in app.js.
// computeScoreFromPersonal calls isDismissed internally, which depends on
// global state S.dismissed. In our sandbox, S.dismissed is empty, so
// isDismissed always returns false — conversations are only "replied" if
// c.i_replied_last is true.
import { describe, it, expect, vi } from "vitest";
import { createSandbox } from "./sandbox.js";

const ctx = createSandbox();

describe("computeScoreFromPersonal", () => {
  it("returns perfect score for empty list", () => {
    const r = ctx.computeScoreFromPersonal([]);
    expect(r.score).toBe(100);
    expect(r.rate).toBe(100);
    expect(r.speed).toBe(0);
    expect(r.hanging).toBe(0);
    expect(r.replied).toBe(0);
    expect(r.total).toBe(0);
  });

  it("returns perfect score when all conversations are replied", () => {
    const personal = [
      { i_replied_last: true, last_message_at: new Date().toISOString() },
      { i_replied_last: true, last_message_at: new Date().toISOString() },
    ];
    const r = ctx.computeScoreFromPersonal(personal);
    expect(r.rate).toBe(100);
    expect(r.replied).toBe(2);
    expect(r.total).toBe(2);
    expect(r.hanging).toBe(0);
    expect(r.score).toBeGreaterThanOrEqual(90);
  });

  it("penalizes unreplied conversations", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString();
    const personal = [
      { i_replied_last: true, last_message_at: new Date().toISOString() },
      { i_replied_last: false, last_message_at: twoHoursAgo },
    ];
    const r = ctx.computeScoreFromPersonal(personal);
    expect(r.rate).toBe(50);
    expect(r.replied).toBe(1);
    expect(r.hanging).toBe(1);
    expect(r.score).toBeLessThan(100);
  });

  it("has lower score for older unreplied messages", () => {
    const recent = new Date(Date.now() - 1 * 3600000).toISOString();
    const old = new Date(Date.now() - 80 * 3600000).toISOString();

    const recentUnreplied = [{ i_replied_last: false, last_message_at: recent }];
    const oldUnreplied = [{ i_replied_last: false, last_message_at: old }];

    const rRecent = ctx.computeScoreFromPersonal(recentUnreplied);
    const rOld = ctx.computeScoreFromPersonal(oldUnreplied);

    // Older unreplied → worse speed + worse hanging → lower score
    expect(rOld.score).toBeLessThan(rRecent.score);
  });

  it("score is always between 0 and 100", () => {
    const manyOld = Array.from({ length: 20 }, () => ({
      i_replied_last: false,
      last_message_at: new Date(Date.now() - 200 * 3600000).toISOString(),
    }));
    const r = ctx.computeScoreFromPersonal(manyOld);
    expect(r.score).toBeGreaterThanOrEqual(0);
    expect(r.score).toBeLessThanOrEqual(100);
  });

  it("rate is the percentage of replied conversations", () => {
    const personal = [
      { i_replied_last: true, last_message_at: new Date().toISOString() },
      { i_replied_last: true, last_message_at: new Date().toISOString() },
      { i_replied_last: false, last_message_at: new Date().toISOString() },
      { i_replied_last: false, last_message_at: new Date().toISOString() },
    ];
    const r = ctx.computeScoreFromPersonal(personal);
    expect(r.rate).toBe(50);
    expect(r.total).toBe(4);
    expect(r.replied).toBe(2);
  });

  it("hanging penalty escalates with wait time", () => {
    // <1h → 1pt, <24h → 3pt, <72h → 6pt, >=72h → 10pt
    const veryRecent = [{ i_replied_last: false, last_message_at: new Date(Date.now() - 30 * 60000).toISOString() }];
    const dayOld = [{ i_replied_last: false, last_message_at: new Date(Date.now() - 25 * 3600000).toISOString() }];
    const weekOld = [{ i_replied_last: false, last_message_at: new Date(Date.now() - 100 * 3600000).toISOString() }];

    const rRecent = ctx.computeScoreFromPersonal(veryRecent);
    const rDay = ctx.computeScoreFromPersonal(dayOld);
    const rWeek = ctx.computeScoreFromPersonal(weekOld);

    expect(rRecent.hangingScore).toBeGreaterThan(rDay.hangingScore);
    expect(rDay.hangingScore).toBeGreaterThan(rWeek.hangingScore);
  });

  it("returns correct structure shape", () => {
    const r = ctx.computeScoreFromPersonal([
      { i_replied_last: true, last_message_at: new Date().toISOString() },
    ]);
    expect(r).toHaveProperty("score");
    expect(r).toHaveProperty("rate");
    expect(r).toHaveProperty("speed");
    expect(r).toHaveProperty("speedScore");
    expect(r).toHaveProperty("hanging");
    expect(r).toHaveProperty("hangingScore");
    expect(r).toHaveProperty("replied");
    expect(r).toHaveProperty("total");
  });
});
