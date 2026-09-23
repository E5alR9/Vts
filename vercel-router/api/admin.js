/**
 * 管理 API（全部需 admin：ADMIN_TOKEN 或 role=admin 的 user token）
 *
 *   GET  /api/admin?action=status   KV 狀態、keys 數、users 數、點數總覽
 *   POST /api/admin {action:"seed", name?}            建第一個 admin 帳號（限一次，force 可重建）
 *   GET  /api/admin?action=keys     keys 清單（遮蔽顯示）
 *   POST /api/admin {action:"keys.add", key, label?}
 *   POST /api/admin {action:"keys.remove", id}
 *   POST /api/admin {action:"keys.toggle", id, disabled}
 *   GET  /api/admin?action=users    帳號清單
 *   POST /api/admin {action:"users.create", name, role?, credits?}  → 回 token（只顯示一次）
 *   POST /api/admin {action:"users.add-credits", token, delta}
 *   POST /api/admin {action:"users.set", token, fields:{name?,role?,credits?,disabled?}}
 *
 * 無 KV（沒開通 Vercel KV）時：status 回 kv:false，其他寫入類回 503。
 */
const store = require("../lib/store");
const { auth, requireAdmin, randomToken, adminToken } = require("../lib/auth");

function sendJson(res, status, obj) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(obj));
}

function parseBody(req) {
  // Vercel 會自動解析 JSON；本地測試 server 也會先塞 req.body
  if (req.body !== undefined) {
    if (typeof req.body === "string") {
      try { return Promise.resolve(JSON.parse(req.body)); } catch { return Promise.resolve({}); }
    }
    return Promise.resolve(req.body || {});
  }
  return new Promise((resolve) => {
    let raw = "";
    req.on("data", (c) => { raw += c; });
    req.on("end", () => {
      if (!raw) return resolve({});
      try { resolve(JSON.parse(raw)); } catch { resolve({ _raw: raw }); }
    });
    req.on("error", () => resolve({}));
  });
}

function keyId(key) {
  const h = require("crypto").createHash("sha256").update(key).digest("hex");
  return "k_" + h.slice(0, 12);
}

module.exports = async (req, res) => {
  const url = new URL(req.url, "http://x");
  const body = req.method === "POST" ? await parseBody(req) : {};
  const action = (req.method === "GET" ? url.searchParams.get("action") : body.action) || "status";
  if (process.env.ADMIN_TEST_LOG) console.log("ADMIN action=", action, "method=", req.method);

  // seed 允許用 ADMIN_TOKEN（還沒有任何 admin 時）
  const a = await auth(req);
  if (!requireAdmin(a)) {
    return sendJson(res, 401, { ok: false, error: { message: "需要管理員權限（ADMIN_TOKEN 或 admin 帳號）" } });
  }

  const needKV = action !== "status";
  if (needKV && !store.hasKV()) {
    return sendJson(res, 503, { ok: false, error: { message: "未接 Redis：到 Vercel Dashboard → Storage → Create → Redis（Marketplace），把 UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN 設進環境變數後重部署" } });
  }

  try {
    // ── 狀態 ──
    if (action === "status") {
      const kv = store.hasKV();
      const users = kv ? await store.getUsers() : null;
      const managed = kv ? await store.getManagedKeys() : null;
      const list = users ? Object.values(users) : [];
      return sendJson(res, 200, { ok: true, kv,
        envKeys: store.envKeys().length,
        managedKeys: managed ? managed.filter((k) => !k.disabled).length : 0,
        users: list.length,
        creditsTotal: list.reduce((s, u) => s + (Number(u.credits) || 0), 0),
        hasAdminToken: Boolean(adminToken()),
      });
    }

    // ── 建第一個 admin ──
    if (action === "seed") {
      const users = (await store.getUsers()) || {};
      const hasAdmin = Object.values(users).some((u) => u.role === "admin" && !u.disabled);
      if (hasAdmin && !body.force) {
        return sendJson(res, 409, { ok: false, error: { message: "已存在 admin 帳號（要重建請帶 force:true）" } });
      }
      const token = randomToken("adm");
      users[token] = { name: String(body.name || "admin"), role: "admin",
        credits: -1, createdAt: new Date().toISOString(), disabled: false };
      await store.setUsers(users);
      await store.markSeeded();
      return sendJson(res, 200, { ok: true, name: users[token].name, role: "admin",
        token, note: "token 只顯示這一次，請妥善保存" });
    }

    // ── keys ──
    if (action === "keys") {
      const managed = (await store.getManagedKeys()) || [];
      return sendJson(res, 200, { ok: true,
        env: store.envKeys().map((k) => ({ id: "env:" + k.slice(-6), prefix: store.mask(k), label: "env", managed: false })),
        managed: managed.map((k) => ({ id: k.id, prefix: k.prefix || store.mask(k.key), label: k.label || "", disabled: !!k.disabled, addedAt: k.addedAt || "" })),
      });
    }
    if (action === "keys.add") {
      const key = String(body.key || "").trim();
      if (!key || !key.startsWith("gsk_")) {
        return sendJson(res, 400, { ok: false, error: { message: "key 格式不對（應為 gsk_ 開頭）" } });
      }
      const managed = (await store.getManagedKeys()) || [];
      if (managed.some((k) => k.key === key) || store.envKeys().includes(key)) {
        return sendJson(res, 409, { ok: false, error: { message: "這把 key 已存在" } });
      }
      managed.push({ id: keyId(key), prefix: store.mask(key), key,
        label: String(body.label || ""), addedAt: new Date().toISOString(), disabled: false });
      await store.setManagedKeys(managed);
      return sendJson(res, 200, { ok: true, count: managed.length });
    }
    if (action === "keys.remove") {
      const managed = ((await store.getManagedKeys()) || []).filter((k) => k.id !== body.id);
      await store.setManagedKeys(managed);
      return sendJson(res, 200, { ok: true, count: managed.length });
    }
    if (action === "keys.toggle") {
      const managed = (await store.getManagedKeys()) || [];
      const k = managed.find((x) => x.id === body.id);
      if (!k) return sendJson(res, 404, { ok: false, error: { message: "找不到這把 key" } });
      k.disabled = body.disabled !== false;
      await store.setManagedKeys(managed);
      return sendJson(res, 200, { ok: true, disabled: k.disabled });
    }

    // ── users ──
    if (action === "users") {
      const users = (await store.getUsers()) || {};
      const list = Object.entries(users).map(([token, u]) => ({
        token, name: u.name, role: u.role, credits: u.credits,
        disabled: !!u.disabled, createdAt: u.createdAt || "",
      }));
      return sendJson(res, 200, { ok: true, users: list });
    }
    if (action === "users.create") {
      const name = String(body.name || "").trim();
      if (!name) return sendJson(res, 400, { ok: false, error: { message: "name 不可為空" } });
      const role = body.role === "admin" ? "admin" : "user";
      const credits = body.credits === undefined ? 10000 : Number(body.credits);
      if (!Number.isFinite(credits) || (credits < 0 && credits !== -1)) {
        return sendJson(res, 400, { ok: false, error: { message: "credits 需為 >=0 的數字（-1 = 無限）" } });
      }
      const token = randomToken(role === "admin" ? "adm" : "usr");
      const users = (await store.getUsers()) || {};
      users[token] = { name, role, credits, createdAt: new Date().toISOString(), disabled: false };
      await store.setUsers(users);
      return sendJson(res, 200, { ok: true, name, role, credits, token, note: "token 只顯示這一次" });
    }
    if (action === "users.add-credits") {
      const users = (await store.getUsers()) || {};
      const u = users[body.token];
      if (!u) return sendJson(res, 404, { ok: false, error: { message: "找不到帳號" } });
      const delta = Number(body.delta);
      if (!Number.isFinite(delta)) return sendJson(res, 400, { ok: false, error: { message: "delta 需為數字" } });
      if (u.credits === -1) return sendJson(res, 200, { ok: true, credits: -1, note: "無限點數帳號" });
      u.credits = Math.max(0, (Number(u.credits) || 0) + delta);
      await store.setUsers(users);
      return sendJson(res, 200, { ok: true, credits: u.credits });
    }
    if (action === "users.set") {
      const users = (await store.getUsers()) || {};
      const u = users[body.token];
      if (!u) return sendJson(res, 404, { ok: false, error: { message: "找不到帳號" } });
      const f = body.fields || {};
      if (f.name !== undefined) u.name = String(f.name);
      if (f.role === "admin" || f.role === "user") u.role = f.role;
      if (f.credits !== undefined) {
        const c = Number(f.credits);
        if (!Number.isFinite(c) || (c < 0 && c !== -1)) {
          return sendJson(res, 400, { ok: false, error: { message: "credits 需為 >=0（-1 = 無限）" } });
        }
        u.credits = c;
      }
      if (f.disabled !== undefined) u.disabled = !!f.disabled;
      await store.setUsers(users);
      return sendJson(res, 200, { ok: true, user: { name: u.name, role: u.role, credits: u.credits, disabled: !!u.disabled } });
    }

    return sendJson(res, 400, { ok: false, error: { message: "未知 action: " + action } });
  } catch (e) {
    return sendJson(res, 500, { ok: false, error: { message: String((e && e.message) || e) } });
  }
};
