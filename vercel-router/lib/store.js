/**
 * lib/store.js — 持久層抽象（Vercel KV 可選；沒有 KV 時退回 env 唯讀模式）
 *
 * 資料模型（KV hash/key）：
 *   gr:keys              JSON array [{id, prefix, key, label, addedAt, disabled}]
 *   gr:users             JSON object {token: {name, role, credits, createdAt}}
 *   gr:meta              JSON {seeded: true}
 *
 * 有 KV：完整 CRUD + 點數扣減。
 * 無 KV：keys 只讀 env（管理 API 回 503 + 提示開通 KV），users 不可用。
 */
let _kv = null;
let _kvTried = false;

function kv() {
  if (_kvTried) return _kv;
  _kvTried = true;
  try {
    // Upstash Redis（Vercel Marketplace → Storage → Redis，自動注入環境變數）。
    // 沒配時拋錯 → 走 env 唯讀模式。
    const { Redis } = require("@upstash/redis");
    const url = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
    const token = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;
    if (!url || !token) return null;
    _kv = new Redis({ url, token });
  } catch {
    _kv = null;
  }
  return _kv;
}

function hasKV() {
  return Boolean(kv());
}

/** env 來的 Groq keys（唯讀基底；KV 有額外 keys 時合併） */
function envKeys() {
  const set = new Set();
  const raw = process.env.GROQ_KEYS || process.env.GROQ_KEY || process.env.GROQ_API_KEYS || "";
  for (const k of raw.split(/[\s,;]+/)) if (k.trim()) set.add(k.trim());
  for (let i = 1; i <= 64; i++) {
    const v = process.env[`GROQ_KEY_${i}`];
    if (v && v.trim()) set.add(v.trim());
  }
  return [...set];
}

function mask(key) {
  if (!key || key.length < 10) return "***";
  return key.slice(0, 7) + "…" + key.slice(-4);
}

async function getManagedKeys() {
  const k = kv();
  if (!k) return null;
  try {
    const raw = await k.get("gr:keys");
    if (!raw) return [];
    return typeof raw === "string" ? JSON.parse(raw) : raw;
  } catch {
    return [];
  }
}

async function setManagedKeys(list) {
  const k = kv();
  if (!k) throw new Error("NO_KV");
  await k.set("gr:keys", JSON.stringify(list));
}

/** 全部可用 keys = env 基底 + KV 管理的（disabled 跳過，去重） */
async function allKeys() {
  const base = envKeys().map((key) => ({ id: "env:" + key.slice(-6), prefix: mask(key), key, label: "env", managed: false }));
  const managed = (await getManagedKeys()) || [];
  const seen = new Set(base.map((k) => k.key));
  const extra = managed.filter((k) => !k.disabled && k.key && !seen.has(k.key)).map((k) => ({ ...k, managed: true }));
  return [...base, ...extra];
}

async function getUsers() {
  const k = kv();
  if (!k) return null;
  try {
    const raw = await k.get("gr:users");
    if (!raw) return {};
    return typeof raw === "string" ? JSON.parse(raw) : raw;
  } catch {
    return {};
  }
}

async function setUsers(users) {
  const k = kv();
  if (!k) throw new Error("NO_KV");
  await k.set("gr:users", JSON.stringify(users));
}

async function isSeeded() {
  const k = kv();
  if (!k) return false;
  try {
    const raw = await k.get("gr:meta");
    const meta = typeof raw === "string" ? JSON.parse(raw) : raw;
    return Boolean(meta && meta.seeded);
  } catch {
    return false;
  }
}

async function markSeeded() {
  const k = kv();
  if (!k) throw new Error("NO_KV");
  await k.set("gr:meta", JSON.stringify({ seeded: true, at: new Date().toISOString() }));
}

/** 渠道：gr:channels JSON {id: {name, keys:[完整key], weight, models, disabled, createdAt}}
 *  聊天路由：按 weight 選渠道 → 渠道內輪 key。預設渠道 default（env 來的 keys）。 */
async function getChannels() {
  const k = kv();
  if (!k) return null;
  try {
    const raw = await k.get("gr:channels");
    return raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : {};
  } catch {
    return {};
  }
}

async function setChannels(ch) {
  const k = kv();
  if (!k) throw new Error("NO_KV");
  await k.set("gr:channels", JSON.stringify(ch));
}

function newChannelId() {
  return "ch_" + require("crypto").randomBytes(6).toString("hex");
}

/** 選渠道：啟用的、支援該模型的，按 weight 加權隨機 */
function pickChannel(channels, model) {
  const list = Object.entries(channels || {})
    .filter(([, c]) => !c.disabled && (c.keys || []).length > 0)
    .filter(([, c]) => !(c.models || []).length || (c.models || []).includes(model));
  if (!list.length) return null;
  const total = list.reduce((s, [, c]) => s + Math.max(1, Number(c.weight) || 1), 0);
  let r = Math.random() * total;
  for (const [id, c] of list) {
    r -= Math.max(1, Number(c.weight) || 1);
    if (r <= 0) return { id, ...c };
  }
  const [id, c] = list[list.length - 1];
  return { id, ...c };
}
async function getInvites() {
  const k = kv();
  if (!k) throw new Error("NO_KV");
  try {
    const raw = await k.get("gr:invites");
    return raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : {};
  } catch {
    return {};
  }
}

async function setInvites(inv) {
  const k = kv();
  if (!k) throw new Error("NO_KV");
  await k.set("gr:invites", JSON.stringify(inv));
}

function newInviteCode() {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const b = require("crypto").randomBytes(6);
  let s = "";
  for (const x of b) s += chars[x % chars.length];
  return s.slice(0, 4) + "-" + s.slice(4);
}

/** 點數匯率：1,000,000 點 = $1（env POINTS_PER_USD 可覆寫）
 *  舊制「tokens × 單一倍率」已廢棄 → 改為直接按官方價：(in×input價 + out×output價) 計美元再轉點 */
const POINTS_PER_USD = Math.max(1, Number(process.env.POINTS_PER_USD) || 10000000);

/** 計費表 = 促銷係數（1 = 官方價直轉；<1 折扣、>1 加價）
 *  v2 版（__v 標記）：舊的 10/2/1/0.5 倍率表偵測到 __v 不符 → 自動回到預設 ×1 */
const DEFAULT_PRICING = {
  "qwen/qwen3.8-27b": 1,
  "qwen/qwen3-32b": 1,
  "openai/gpt-oss-120b": 1,
  "openai/gpt-oss-20b": 1,
  "allam-2-7b": 1,
};
const PRICING_VERSION = 2;

async function getPricing() {
  const k = kv();
  if (!k) return { ...DEFAULT_PRICING };
  try {
    const raw = await k.get("gr:pricing");
    const p = raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : null;
    if (!p || p.__v !== PRICING_VERSION) return { ...DEFAULT_PRICING };   // 舊版倍率表作廢
    const out = { ...p };
    delete out.__v;
    return { ...DEFAULT_PRICING, ...out };
  } catch {
    return { ...DEFAULT_PRICING };
  }
}

async function setPricing(p) {
  const k = kv();
  if (!k) throw new Error("NO_KV");
  await k.set("gr:pricing", JSON.stringify({ ...p, __v: PRICING_VERSION }));
}

function priceFor(pricing, model) {
  const m = Number(pricing[model]);
  return Number.isFinite(m) && m > 0 ? m : 1;
}

/** 直接按官方價算扣點：
 *  usd = (pt × input + ct × output) / 1e6 × 促銷係數；轉點後至少 1 點（$0 模型 = 免費0點） */
function costFor(model, pt, ct, pricing) {
  const mp = MODEL_PRICES[model];
  const mult = priceFor(pricing || {}, model);
  let usd;
  if (mp) usd = (Math.max(0, pt) * mp.input + Math.max(0, ct) * mp.output) / 1e6;
  else usd = ((Math.max(0, pt) + Math.max(0, ct)) * 0.075) / 1e6;   // 未列模型 → 按基準價
  usd *= mult;
  if (usd <= 0) return 0;
  return Math.max(1, Math.ceil(usd * POINTS_PER_USD));
}

/** 請求日誌：gr:logs JSON array（最新在前，只留 100 筆）
 *  entry = {t, user, model, tokens, cost} */
async function logRequest(entry) {
  const k = kv();
  if (!k) return;
  try {
    let logs = [];
    try {
      const raw = await k.get("gr:logs");
      logs = raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : [];
      if (!Array.isArray(logs)) logs = [];
    } catch { logs = []; }
    logs.unshift({ t: Date.now(), ...entry });
    await k.set("gr:logs", JSON.stringify(logs.slice(0, 100)));
  } catch { /* 日誌失敗不影響 */ }
}

async function getLogs() {
  const k = kv();
  if (!k) return [];
  try {
    const raw = await k.get("gr:logs");
    const logs = raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : [];
    return Array.isArray(logs) ? logs : [];
  } catch {
    return [];
  }
}

/** 訂閱制：當月首次使用自動補點
 *  user.plan: 'free'（無）| 方案名；user.monthlyQuota: 每月額度；user.quotaReset: 'YYYY-MM'
 *  回傳 true 表示本月已重置（補過點） */
async function ensureMonthlyQuota(users, token) {
  const u = users[token];
  if (!u || !u.monthlyQuota || Number(u.monthlyQuota) <= 0) return false;
  const t = new Date();
  const ym = `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}`;
  if (u.quotaReset === ym) return false;
  u.quotaReset = ym;
  if (u.credits !== -1) u.credits = Number(u.monthlyQuota);
  return true;
}

/** 用量記錄：gr:usage:{yyyymmdd} JSON {token: {tokens(真實), points(扣點), reqs, models}} + user.usedTokens 累加 */
function dayKey(d) {
  const t = d || new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${t.getFullYear()}${p(t.getMonth() + 1)}${p(t.getDate())}`;
}

async function recordUsage(userToken, model, tokens, points) {
  const k = kv();
  if (!k) return;
  const dk = `gr:usage:${dayKey()}`;
  try {
    let day = {};
    try {
      const raw = await k.get(dk);
      day = raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : {};
    } catch { day = {}; }
    const e = day[userToken] || { tokens: 0, points: 0, reqs: 0, models: {} };
    e.tokens += Math.max(0, Number(tokens) || 0);
    e.points = (Number(e.points) || 0) + Math.max(0, Number(points) || 0);
    e.reqs += 1;
    e.models[model] = (e.models[model] || 0) + 1;
    day[userToken] = e;
    await k.set(dk, JSON.stringify(day), { ex: 90 * 86400 });  // 留 90 天
  } catch { /* 用量記錄失敗不影響回應 */ }
}

/** 讀用量：days 天內每日彙總（只回該 token 自己的，除非 admin 看全部） */
async function getUsage(days) {
  const k = kv();
  if (!k) return null;
  const n = Math.max(1, Math.min(90, Number(days) || 7));
  const out = [];
  const now = new Date();
  for (let i = 0; i < n; i++) {
    const d = new Date(now.getTime() - i * 86400000);
    const dk = `gr:usage:${dayKey(d)}`;
    try {
      const raw = await k.get(dk);
      out.push({ day: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`,
        data: raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : {} });
    } catch { out.push({ day: "", data: {} }); }
  }
  return out;
}

/* ── 方案（plus/pro/max/ultra 預留）：gr:plans {id:{label,monthlyQuota,rewardMult}} ── */
const DEFAULT_PLANS = {
  free:  { label: "Free",  monthlyQuota: 0,       rewardMult: 1 },
  plus:  { label: "Plus",  monthlyQuota: 30000,   rewardMult: 1 },
  pro:   { label: "Pro",   monthlyQuota: 100000,  rewardMult: 1 },
  max:   { label: "Max",   monthlyQuota: 300000,  rewardMult: 1 },
  ultra: { label: "Ultra", monthlyQuota: 1000000, rewardMult: 1 },
};

async function getPlans() {
  const k = kv();
  if (!k) return JSON.parse(JSON.stringify(DEFAULT_PLANS));
  try {
    const raw = await k.get("gr:plans");
    const p = raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : {};
    return { ...JSON.parse(JSON.stringify(DEFAULT_PLANS)), ...p };
  } catch { return JSON.parse(JSON.stringify(DEFAULT_PLANS)); }
}

async function setPlans(p) {
  const k = kv();
  if (!k) throw new Error("NO_KV");
  await k.set("gr:plans", JSON.stringify(p));
}

/* ── 活動：gr:event {enabled,label,mult,until}；activeEvent() 回目前有效的，否則 null ── */
async function getEvent() {
  const k = kv();
  if (!k) return { enabled: false, label: "", mult: 1, until: "" };
  try {
    const raw = await k.get("gr:event");
    const e = raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : {};
    return { enabled: false, label: "", mult: 1, until: "", ...e };
  } catch { return { enabled: false, label: "", mult: 1, until: "" }; }
}

async function setEvent(e) {
  const k = kv();
  if (!k) throw new Error("NO_KV");
  await k.set("gr:event", JSON.stringify(e));
}

function activeEvent(ev) {
  if (!ev || !ev.enabled) return null;
  const t = new Date();
  const p = (n) => String(n).padStart(2, "0");
  const today = `${t.getFullYear()}-${p(t.getMonth() + 1)}-${p(t.getDate())}`;
  if (ev.until && today > String(ev.until)) return null;
  return ev;
}

/* ── KEY 壓力統計（只記流量數字，零內容）：gr:keystat {day, keys:{hash:{prefix,reqs,tokens,errs,ts[]}}} ── */
function keyStatHash(key) {
  return "h_" + require("crypto").createHash("sha256").update(key).digest("hex").slice(0, 12);
}

async function recordKeyStat(key, opts) {
  const k = kv();
  if (!k) return;
  const o = opts || {};
  try {
    let s = null;
    try {
      const raw = await k.get("gr:keystat");
      s = raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : null;
    } catch { s = null; }
    const t = new Date();
    const p = (n) => String(n).padStart(2, "0");
    const day = `${t.getFullYear()}-${p(t.getMonth() + 1)}-${p(t.getDate())}`;
    if (!s || s.day !== day || !s.keys) s = { day, keys: {} };
    const h = keyStatHash(key);
    const e = s.keys[h] || { prefix: mask(key), reqs: 0, tokens: 0, errs: 0, ts: [] };
    e.reqs += 1;
    e.tokens += Math.max(0, Number(o.tokens) || 0);
    if (o.err) e.errs += 1;
    const now = Date.now();
    e.ts = [...(e.ts || []), now].filter((x) => now - x < 60000).slice(-120);
    s.keys[h] = e;
    await k.set("gr:keystat", JSON.stringify(s), { ex: 2 * 86400 });
  } catch { /* 統計失敗不影響回應 */ }
}

async function getKeyStat() {
  const k = kv();
  if (!k) return { day: "", keys: {} };
  try {
    const raw = await k.get("gr:keystat");
    const s = raw ? (typeof raw === "string" ? JSON.parse(raw) : raw) : null;
    return s && s.keys ? s : { day: "", keys: {} };
  } catch { return { day: "", keys: {} }; }
}

/** 模型官方參考價（$/1M tokens，input/output；以 Groq 公告為準）
 *  扣點規則：站內實付 = total_tokens × 倍率（倍率見 DEFAULT_PRICING） */
const MODEL_PRICES = {
  "qwen/qwen3.8-27b":    { input: 0.80,  output: 3.2,  note: "主力對話" },
  "qwen/qwen3-32b":      { input: 0.60,  output: 2.4,  note: "備援梯隊" },
  "openai/gpt-oss-120b": { input: 0.15,  output: 0.6,  note: "推理較強" },
  "openai/gpt-oss-20b":  { input: 0.075, output: 0.3,  note: "計費基準（1x）" },
  "allam-2-7b":          { input: 0,     output: 0,    note: "未定價（0 計）" },
};

module.exports = { kv, hasKV, envKeys, mask, getManagedKeys, setManagedKeys, allKeys, getUsers, setUsers, isSeeded, markSeeded, recordUsage, getUsage, getInvites, setInvites, newInviteCode, getPricing, setPricing, priceFor, DEFAULT_PRICING, MODEL_PRICES, POINTS_PER_USD, costFor, logRequest, getLogs, ensureMonthlyQuota, getChannels, setChannels, newChannelId, pickChannel, getPlans, setPlans, DEFAULT_PLANS, getEvent, setEvent, activeEvent, keyStatHash, recordKeyStat, getKeyStat };
