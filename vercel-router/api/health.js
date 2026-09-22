/**
 * GET /api/health — 冒煙測試用。只回統計數字，不回任何金鑰內容。
 */
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

module.exports = (req, res) => {
  const keys = loadKeys();
  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(
    JSON.stringify({
      ok: true,
      hasRouterToken: Boolean(process.env.ROUTER_TOKEN),
      keyCount: keys.length,
      keyPrefixes: [...new Set(keys.map((k) => k.slice(0, 4)))],
      ladder: (process.env.MODEL_LADDER || "qwen/qwen3.8-27b,openai/gpt-oss-120b,openai/gpt-oss-20b,allam-2-7b")
        .split(/[\s,;]+/)
        .filter(Boolean),
      time: new Date().toISOString(),
    })
  );
};
