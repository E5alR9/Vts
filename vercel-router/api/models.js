/**
 * GET /v1/models — 轉發 Groq 的模型清單（讓 OpenAI 相容客戶端的「列出模型」功能可用）
 */
const MODELS_URL = "https://api.groq.com/openai/v1/models";

function loadKeys() {
  const set = new Set();
  const raw = process.env.GROQ_KEYS || process.env.GROQ_KEY || process.env.GROQ_API_KEYS || "";
  for (const k of raw.split(/[\s,;]+/)) if (k.trim()) set.add(k.trim());
  for (let i = 1; i <= 64; i++) {
    const v = process.env[`GROQ_KEY_${i}`];
    if (v && v.trim()) set.add(v.trim());
  }
  return [...set];
}

module.exports = async (req, res) => {
  if (req.method !== "GET") {
    res.statusCode = 405;
    return res.end(JSON.stringify({ error: "GET only" }));
  }

  const want = process.env.ROUTER_TOKEN;
  const got = req.headers.authorization || "";
  if (!want || got !== `Bearer ${want}`) {
    res.statusCode = 401;
    res.setHeader("Content-Type", "application/json");
    return res.end(JSON.stringify({ error: { message: "unauthorized" } }));
  }

  const keys = loadKeys();
  if (!keys.length) {
    res.statusCode = 500;
    res.setHeader("Content-Type", "application/json");
    return res.end(JSON.stringify({ error: { message: "未設定 GROQ_KEYS" } }));
  }

  const upstream = await fetch(MODELS_URL, { headers: { Authorization: `Bearer ${keys[0]}` } });
  const text = await upstream.text();
  res.statusCode = upstream.status;
  res.setHeader("Content-Type", upstream.headers.get("content-type") || "application/json");
  res.end(text);
};
