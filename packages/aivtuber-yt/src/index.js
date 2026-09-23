/**
 * aivtuber-yt — YouTube Live 聊天室（免 API 金鑰）
 *
 *   const yt = require("aivtuber-yt");
 *   const live = await yt.resolveLive("@LofiGirl");   // {videoId, isLive, title}
 *   await yt.watch(live.videoId, (m) => console.log(m.user, m.message));
 *
 * 原理（已在 ai_vtuber 實測驗證）：
 *   頻道 → {channel}/live 頁: canonical 取 videoId +
 *          ytInitialPlayerResponse.videoDetails.isLiveContent 判在播
 *   聊天 → live_chat 頁拿 continuation → InnerTube get_live_chat 輪詢
 *          （載荷欄位是 continuation；下一代 token 在
 *           continuations[0].invalidationContinuationData.continuation）
 */
const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";
const CLIENT = { clientName: "WEB", clientVersion: "2.20260101.01.00", hl: "zh-TW", gl: "TW" };
const API = "https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?prettyPrint=false";

function normalizeChannel(raw) {
  raw = String(raw || "").trim().replace(/^['"]|['"]$/g, "");
  if (!raw) return "";
  if (raw.startsWith("@")) return raw.split("/")[0].replace(/\/$/, "");
  let m = raw.match(/youtube\.com\/(@[^/?#]+|channel\/UC[A-Za-z0-9_-]+|(?:c|user)\/[^/?#]+)/);
  if (m) return m[1];
  if (/^UC[A-Za-z0-9_-]{20,}$/.test(raw)) return `channel/${raw}`;
  return "";
}

function normalizeVideoId(raw) {
  raw = String(raw || "").trim().replace(/^['"]|['"]$/g, "");
  if (!raw) return "";
  if (raw.startsWith("@") || /^UC[A-Za-z0-9_-]{20,}$/.test(raw) ||
      /youtube\.com\/@|youtube\.com\/channel\/|youtube\.com\/(c|user)\//.test(raw)) return "";
  const m = raw.match(/(?:v=|youtu\.be\/|live\/)([A-Za-z0-9_-]{6,})/);
  return m ? m[1] : raw;
}

function cutBalancedJson(html, marker) {
  const i = html.indexOf(marker);
  if (i < 0) return null;
  const j = html.indexOf("{", i);
  if (j < 0) return null;
  let depth = 0, instr = false, esc = false;
  for (let k = j; k < html.length; k++) {
    const c = html[k];
    if (instr) {
      if (esc) esc = false;
      else if (c === "\\") esc = true;
      else if (c === '"') instr = false;
    } else {
      if (c === '"') instr = true;
      else if (c === "{") depth++;
      else if (c === "}") {
        depth--;
        if (depth === 0) return html.slice(j, k + 1);
      }
    }
  }
  return null;
}

function extractLiveFromHtml(html) {
  if (!html) return { videoId: null, isLive: false, title: "", ok: false };
  const canon = html.match(/rel="canonical" href="[^"]*[?&]v=([A-Za-z0-9_-]{6,})/);
  const videoId = canon ? canon[1] : null;
  const raw = cutBalancedJson(html, "ytInitialPlayerResponse");
  if (!raw || !videoId) return { videoId, isLive: false, title: "", ok: false };
  try {
    const pr = JSON.parse(raw);
    const vd = pr.videoDetails || {};
    const ok = ((pr.playabilityStatus || {}).status || "") === "OK";
    return { videoId, isLive: Boolean(vd.isLiveContent) && ok,
      title: String(vd.title || "").slice(0, 80), ok: true };
  } catch {
    return { videoId, isLive: false, title: "", ok: true };
  }
}

const CONT_PATTERNS = [
  /"liveChatRenderer":\{"continuation":"([^"]+)"/,
  /"continuation"\s*:\s*"([A-Za-z0-9_%\-.]{12,})"/,
];

function extractContinuation(html) {
  for (const p of CONT_PATTERNS) {
    const m = (html || "").match(p);
    if (m) return m[1];
  }
  return null;
}

function findSimple(obj, key) {
  if (obj && typeof obj === "object") {
    if (Array.isArray(obj)) {
      for (const v of obj) {
        const r = findSimple(v, key);
        if (r) return r;
      }
    } else {
      if (key in obj) {
        const v = obj[key];
        if (v && typeof v === "object" && "simpleText" in v) return v.simpleText;
        if (typeof v === "string") return v;
      }
      for (const v of Object.values(obj)) {
        const r = findSimple(v, key);
        if (r) return r;
      }
    }
  }
  return null;
}

function parseLiveChatResponse(data) {
  data = data || {};
  const lc = ((data.continuationContents || {}).liveChatContinuation) || data.liveChatContinuation || data;
  const messages = [];
  for (const act of lc.actions || []) {
    const ta = act.addLiveChatTextAction;
    if (!ta || typeof ta !== "object") continue;
    const item = ta.item || ta;
    const renderer = item.liveChatTextActionRenderer;
    if (!renderer) continue;
    const runs = ((renderer.message || {}).runs) || [];
    const text = runs.map((r) => r.text || "").join("").trim();
    if (!text) continue;
    messages.push({ user: findSimple(renderer, "authorName") || "觀眾", message: text });
  }
  let cont = lc.continuation;
  if (!cont) {
    for (const c of lc.continuations || []) {
      const icd = (c || {}).invalidationContinuationData || (c || {}).timedContinuationData ||
        (c || {}).liveChatReplayContinuationData || {};
      if (icd.continuation) { cont = icd.continuation; break; }
    }
  }
  if (!cont) {
    const m = JSON.stringify(lc).match(/"continuation":"([A-Za-z0-9_%\-.]{40,})/);
    if (m) cont = m[1];
  }
  const wait = Math.max(5, Math.min(15, (Number(lc.timeoutMs) || 8000) / 1000));
  return { messages, cont: cont || null, wait };
}

async function get(url, opts = {}) {
  const r = await fetch(url, { headers: { "User-Agent": UA }, signal: AbortSignal.timeout(opts.timeout || 25000) });
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${url.slice(0, 60)}`);
  return r.text();
}

async function postJson(url, payload, opts = {}) {
  const r = await fetch(url, { method: "POST",
    headers: { "User-Agent": UA, "Content-Type": "application/json" },
    body: JSON.stringify(payload), signal: AbortSignal.timeout(opts.timeout || 25000) });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(`HTTP ${r.status}: ${t.slice(0, 120)}`);
  }
  return r.json();
}

/** 頻道 → 目前直播（不在播時 isLive=false，照樣回 videoId/title） */
async function resolveLive(channel, opts = {}) {
  const ch = normalizeChannel(channel);
  if (!ch) throw new Error("頻道格式不對（支援 @handle / 完整網址 / UC id）");
  const html = await get(`https://www.youtube.com/${ch}/live`, opts);
  return extractLiveFromHtml(html);
}

/** 單次輪詢：回 {messages, cont, wait} */
async function pollOnce(videoId, cont, opts = {}) {
  const data = await postJson(API, { context: { client: CLIENT }, continuation: cont }, opts);
  return parseLiveChatResponse(data);
}

/** 首次 continuation（打 live_chat 頁） */
async function firstContinuation(videoId, opts = {}) {
  const html = await get(`https://www.youtube.com/live_chat?v=${videoId}&is_popout=1`, opts);
  return extractContinuation(html);
}

/**
 * 持續監聽：onMessage({user, message})、onError(err)。
 * 回傳 {stop()}。cont 過期/直播結束時自動重抓（最多重試到 stop）。
 */
async function watch(videoId, onMessage, opts = {}) {
  const onError = opts.onError || (() => {});
  let stopped = false;
  let cont = opts.continuation || null;
  (async () => {
    while (!stopped) {
      try {
        if (!cont) {
          cont = await firstContinuation(videoId, opts);
          if (!cont) {
            onError(new Error("取不到 continuation（沒在播？）"));
            await new Promise((r) => setTimeout(r, 15000));
            continue;
          }
        }
        const { messages, cont: next, wait } = await pollOnce(videoId, cont, opts);
        cont = next;
        for (const m of messages) {
          if (stopped) break;
          try { await onMessage(m); } catch (e) { onError(e); }
        }
        if (!cont) {
          await new Promise((r) => setTimeout(r, 20000));
          continue;
        }
        await new Promise((r) => setTimeout(r, wait * 1000));
      } catch (e) {
        if (stopped) break;
        onError(e);
        cont = null;
        await new Promise((r) => setTimeout(r, 10000));
      }
    }
  })();
  return { stop() { stopped = true; } };
}

module.exports = {
  normalizeChannel, normalizeVideoId, cutBalancedJson, extractLiveFromHtml,
  extractContinuation, parseLiveChatResponse,
  resolveLive, pollOnce, firstContinuation, watch,
};
