// Kinor Partners - shared leaderboard for the kids' 2026 football trivia game.
//
// A tiny Cloudflare Worker with one SQLite-backed Durable Object. It stores
// only a nickname, a score, how many answers were right, the level and a
// timestamp. No email, age, IP address or anything else personal is kept
// (IP addresses are hashed with a daily salt and used only for rate limiting,
// then thrown away after a day).
//
// Endpoints (all JSON):
//   GET  /scores?level=easy|medium|hard   -> { level, top: [{ n, s, r, t }] }
//   POST /round   { level }               -> { token }   (call when a round starts)
//   POST /scores  { token, name, score, right } -> { ok, place, top }
//   DELETE /scores?level=..&t=..  (header X-Admin-Key) removes one entry
//
// Anti-cheat is deliberately simple: a round token must be fetched before a
// round, used once, and redeemed no sooner than a real round could finish;
// the score must be possible for that level and number of right answers.

const LEVELS = { easy: 100, medium: 200, hard: 300 };
const ROUND = 10;
const KEEP = 100;          // entries kept per level
const SHOW = 10;           // entries returned
const MIN_ROUND_MS = 15000;
const MAX_ROUND_MS = 60 * 60 * 1000;
const SUBMITS_PER_HOUR = 20;
const ROUNDS_PER_HOUR = 60;

// Strong words blocked anywhere inside a nickname (also with look-alike
// letters such as 1 for i or 0 for o), and milder words blocked only when they
// are a whole word, so names like "Michelle" or "Dieter" still pass.
const BLOCK_ANYWHERE = [
  "fuck", "fuk", "fck", "fvck", "phuck", "shit", "bitch", "btch", "cunt", "cock", "pussy",
  "porn", "nazi", "hitler", "nigg", "fag", "retard", "slut", "whore", "rape", "penis", "vagina",
  "jizz", "bastard", "wank", "twat", "dildo", "boob",
];
const BLOCK_WORDS = [
  "ass", "arse", "sex", "nig", "kill", "die", "tit", "tits", "cum", "damn", "hell", "crap", "piss",
  "kkk", "isis", "weed", "drug", "drugs", "suck", "sucks", "stupid", "idiot", "dumb", "loser", "hate",
  "poop", "butt", "fart", "pee", "nude", "naked", "dick", "sht", "puss",
];

function maxScore(level, right) {
  // Best case: every right answer in a row, full speed bonus (x1.5), streak
  // multiplier x1 for the first two, x1.5 for the 3rd and 4th, x2 after that.
  const base = LEVELS[level] * 1.5;
  let total = 0;
  for (let k = 1; k <= right; k++) total += base * (k >= 5 ? 2 : k >= 3 ? 1.5 : 1);
  return Math.ceil(total);
}

function cleanName(raw) {
  const name = String(raw || "").normalize("NFKC").replace(/\s+/g, " ").trim();
  if (name.length < 2 || name.length > 14) return null;
  if (!/^[A-Za-z0-9 _-]+$/.test(name)) return null;
  if (/\d{4,}/.test(name)) return null; // no phone numbers or birth years
  const flat = name.toLowerCase()
    .replace(/0/g, "o").replace(/1/g, "i").replace(/3/g, "e").replace(/4/g, "a")
    .replace(/5/g, "s").replace(/7/g, "t").replace(/8/g, "b").replace(/\$/g, "s")
    .replace(/[^a-z]/g, "");
  if (BLOCK_ANYWHERE.some((w) => flat.includes(w))) return null;
  const words = name.toLowerCase().split(/[\s_-]+/).map((x) => x
    .replace(/0/g, "o").replace(/1/g, "i").replace(/3/g, "e").replace(/4/g, "a")
    .replace(/5/g, "s").replace(/7/g, "t").replace(/[^a-z]/g, ""));
  if (words.some((x) => BLOCK_WORDS.includes(x))) return null;
  return name;
}

function cors(origin, env) {
  const allowed = (env.ALLOWED_ORIGINS || "https://kinorpartners.com,https://www.kinorpartners.com").split(",");
  return {
    "Access-Control-Allow-Origin": allowed.includes(origin) ? origin : allowed[0],
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Admin-Key",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...headers },
  });
}

async function sha(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const h = cors(origin, env);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: h });
    const url = new URL(request.url);
    if (!["/scores", "/round"].includes(url.pathname)) return json({ error: "not found" }, 404, h);

    // Rate limiting uses a hash of the IP and today's date; the raw IP is never stored.
    const day = new Date().toISOString().slice(0, 10);
    const who = await sha((request.headers.get("CF-Connecting-IP") || "unknown") + "|" + day + "|" + (env.SALT || "kinor"));

    const stub = env.BOARD.get(env.BOARD.idFromName("global"));
    let body = null;
    if (request.method === "POST") {
      try { body = await request.json(); } catch (e) { return json({ error: "bad json" }, 400, h); }
    }
    const res = await stub.handle({
      method: request.method, path: url.pathname, query: Object.fromEntries(url.searchParams),
      body, who, admin: !!env.ADMIN_KEY && request.headers.get("X-Admin-Key") === env.ADMIN_KEY,
    });
    return json(res.body, res.status, h);
  },
};

import { DurableObject } from "cloudflare:workers";

export class Board extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(`CREATE TABLE IF NOT EXISTS scores (t INTEGER PRIMARY KEY, level TEXT, n TEXT, s INTEGER, r INTEGER)`);
    this.sql.exec(`CREATE INDEX IF NOT EXISTS by_level ON scores (level, s DESC, t ASC)`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS rounds (token TEXT PRIMARY KEY, level TEXT, started INTEGER)`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS hits (who TEXT, kind TEXT, at INTEGER)`);
  }

  top(level) {
    return this.sql.exec(`SELECT n, s, r, t FROM scores WHERE level = ? ORDER BY s DESC, t ASC LIMIT ?`, level, SHOW).toArray();
  }

  limited(who, kind, max) {
    const now = Date.now();
    this.sql.exec(`DELETE FROM hits WHERE at < ?`, now - 24 * 3600 * 1000);
    const n = this.sql.exec(`SELECT COUNT(*) AS c FROM hits WHERE who = ? AND kind = ? AND at > ?`, who, kind, now - 3600 * 1000).one().c;
    if (n >= max) return true;
    this.sql.exec(`INSERT INTO hits (who, kind, at) VALUES (?, ?, ?)`, who, kind, now);
    return false;
  }

  async handle({ method, path, query, body, who, admin }) {
    const now = Date.now();

    if (path === "/scores" && method === "GET") {
      const level = query.level;
      if (!LEVELS[level]) return { status: 400, body: { error: "bad level" } };
      return { status: 200, body: { level, top: this.top(level) } };
    }

    if (path === "/round" && method === "POST") {
      const level = body && body.level;
      if (!LEVELS[level]) return { status: 400, body: { error: "bad level" } };
      if (this.limited(who, "round", ROUNDS_PER_HOUR)) return { status: 429, body: { error: "slow down" } };
      this.sql.exec(`DELETE FROM rounds WHERE started < ?`, now - MAX_ROUND_MS);
      const token = crypto.randomUUID();
      this.sql.exec(`INSERT INTO rounds (token, level, started) VALUES (?, ?, ?)`, token, level, now);
      return { status: 200, body: { token } };
    }

    if (path === "/scores" && method === "POST") {
      const { token, name, score, right } = body || {};
      const round = this.sql.exec(`SELECT level, started FROM rounds WHERE token = ?`, String(token || "")).toArray()[0];
      if (!round) return { status: 400, body: { error: "unknown round" } };
      this.sql.exec(`DELETE FROM rounds WHERE token = ?`, String(token));
      const level = round.level;
      const age = now - round.started;
      if (age < MIN_ROUND_MS || age > MAX_ROUND_MS) return { status: 400, body: { error: "round time" } };
      if (!Number.isInteger(right) || right < 0 || right > ROUND) return { status: 400, body: { error: "bad right" } };
      if (!Number.isInteger(score) || score < 0 || score > maxScore(level, right)) return { status: 400, body: { error: "bad score" } };
      const n = cleanName(name);
      if (!n) return { status: 422, body: { error: "name" } };
      if (this.limited(who, "submit", SUBMITS_PER_HOUR)) return { status: 429, body: { error: "slow down" } };

      let t = now;
      while (this.sql.exec(`SELECT 1 FROM scores WHERE t = ?`, t).toArray().length) t++;
      this.sql.exec(`INSERT INTO scores (t, level, n, s, r) VALUES (?, ?, ?, ?, ?)`, t, level, n, score, right);
      this.sql.exec(`DELETE FROM scores WHERE level = ? AND t NOT IN (SELECT t FROM scores WHERE level = ? ORDER BY s DESC, t ASC LIMIT ?)`, level, level, KEEP);
      const place = this.sql.exec(`SELECT COUNT(*) AS c FROM scores WHERE level = ? AND (s > ? OR (s = ? AND t < ?))`, level, score, score, t).one().c + 1;
      return { status: 200, body: { ok: true, level, t, place, top: this.top(level) } };
    }

    if (path === "/scores" && method === "DELETE") {
      if (!admin) return { status: 403, body: { error: "forbidden" } };
      this.sql.exec(`DELETE FROM scores WHERE level = ? AND t = ?`, String(query.level), Number(query.t));
      return { status: 200, body: { ok: true } };
    }

    return { status: 405, body: { error: "method" } };
  }
}

export { maxScore, cleanName };
