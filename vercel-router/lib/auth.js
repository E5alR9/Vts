/**
 * lib/auth.js — 帳號與權限
 *
 * 兩種身分：
 *   1. ADMIN_TOKEN（env）：全部權限（管理 keys/users/credits/seed）
 *   2. user token（KV gr:users）：role=admin|user；role=user 受點數限制
 *
 * 舊的 ROUTER_TOKEN（共用入口）：相容保留，視為無限點數、不記名。
 *   建議上線後把新用戶都發 user token，ROUTER_TOKEN 只留給自己的服務。
 */
const { getUsers } = require("./store");

function adminToken() {
  return process.env.ADMIN_TOKEN || "";
}

function bearer(req) {
  const h = req.headers.authorization || "";
  return h.startsWith("Bearer ") ? h.slice(7) : "";
}

/**
 * 鑑權。回傳 {ok, kind: 'admin'|'user'|'legacy'|'none', user?}
 * kind=admin：ADMIN_TOKEN 本人（全部權限）
 * kind=user：KV 裡的帳號（含 role；admin role 同樣全權限）
 * kind=legacy：舊 ROUTER_TOKEN（相容，不扣點）
 */
async function auth(req) {
  const tok = bearer(req);
  if (!tok) return { ok: false, kind: "none" };
  if (adminToken() && tok === adminToken()) return { ok: true, kind: "admin" };
  const users = await getUsers();
  if (users && users[tok]) {
    const u = users[tok];
    if (u.disabled) return { ok: false, kind: "none", reason: "帳號已停用" };
    return { ok: true, kind: u.role === "admin" ? "admin" : "user", user: { token: tok, ...u } };
  }
  const legacy = process.env.ROUTER_TOKEN;
  if (legacy && tok === legacy) return { ok: true, kind: "legacy" };
  return { ok: false, kind: "none" };
}

function requireAdmin(a) {
  return a.ok && a.kind === "admin";
}

function randomToken(prefix = "gr") {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  let s = "";
  const buf = require("crypto").randomBytes(32);
  for (const b of buf) s += chars[b % chars.length];
  return `${prefix}_${s}`;
}

module.exports = { adminToken, bearer, auth, requireAdmin, randomToken };
