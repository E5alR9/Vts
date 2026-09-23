/**
 * 帳號 API（中轉站：註冊 / 登入 / 登出 / 我的用量）
 *
 *   POST /api/auth {action:"register", name, password}  → 建 user（初始 0 點，等管理員充值）
 *   POST /api/auth {action:"login", name, password}     → 回 session token（ses_）
 *   POST /api/auth {action:"logout"}                    → 登出（需 session）
 *   GET  /api/auth?action=me                            → 我的帳號+點數（需 user/admin）
 *   GET  /api/auth?action=usage&days=7                  → 我的用量（需 user/admin；admin 可帶 token= 看別人）
 *
 * 規則：
 *   - name 唯一（不分大小寫比對）、2~24 字、限英文數字底線中文
 *   - password 最少 6 字；只存 SHA-256(salt+password)
 *   - 註冊要驗證碼嗎？目前不用（要擋濫註冊時加 INVITE_CODE env 再說）
 */
const store = require("../lib/store");
const { auth, randomToken, hashPassword, newSalt } = require("../lib/auth");

function sendJson(res, status, obj) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(obj));
}

function parseBody(req) {
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
      try { resolve(JSON.parse(raw || "{}")); } catch { resolve({}); }
    });
    req.on("error", () => resolve({}));
  });
}

/** 舊資料修復：只有 lastCheckin 沒有 log 的，補進日曆 */
function healCheckinLog(u) {
  const log = Array.isArray(u.checkinLog) ? u.checkinLog.slice() : [];
  if (u.lastCheckin && !log.includes(u.lastCheckin)) log.push(u.lastCheckin);
  log.sort();
  return log.slice(-90);
}

/** 個人推薦碼：U-XXXX-XXXX（與管理員邀請碼 XXXX-XXXX 格式不衝突） */
function newMyCode(users) {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const crypto = require("crypto");
  for (;;) {
    const b = crypto.randomBytes(8);
    let s = "";
    for (const x of b) s += chars[x % chars.length];
    const code = `U-${s.slice(0, 4)}-${s.slice(4, 8)}`;
    if (!Object.values(users).some((u) => u.myCode === code)) return code;
  }
}

function cleanUser(token, u) {
  return { token: token || "", name: u.name, role: u.role, credits: u.credits,
    usedTokens: u.usedTokens || 0, disabled: !!u.disabled, createdAt: u.createdAt || "",
    checkinLog: healCheckinLog(u),
    myCode: u.myCode || "", refCount: u.refCount || 0, referredBy: u.referredBy || "",
    plan: u.plan || "free",
    apiKeys: (Array.isArray(u.keys) ? u.keys : []).map((k) => ({
      id: k.id, name: k.name, secret: k.secret, disabled: !!k.disabled,
      createdAt: k.createdAt || "", lastUsed: k.lastUsed || 0 })) };
}

module.exports = async (req, res) => {
  const url = new URL(req.url, "http://x");
  const body = req.method === "POST" ? await parseBody(req) : {};
  const action = (req.method === "GET" ? url.searchParams.get("action") : body.action) || "me";

  if (!store.hasKV()) {
    return sendJson(res, 503, { ok: false, error: { message: "帳號系統尚未啟用（缺 Redis）" } });
  }

  try {
    // ── 註冊 ──
    if (action === "register") {
      const name = String(body.name || "").trim();
      const password = String(body.password || "");
      if (!/^[\w\u4e00-\u9fff]{2,24}$/.test(name)) {
        return sendJson(res, 400, { ok: false, error: { message: "名稱需 2~24 字（英文數字底線中文）" } });
      }
      if (password.length < 6) {
        return sendJson(res, 400, { ok: false, error: { message: "密碼最少 6 字" } });
      }
      const users = (await store.getUsers()) || {};
      const dup = Object.values(users).some((u) => String(u.name || "").toLowerCase() === name.toLowerCase());
      if (dup) return sendJson(res, 409, { ok: false, error: { message: "這名稱已被註冊" } });
      const token = randomToken("usr");
      const salt = newSalt();
      const session = randomToken("ses");
      users[token] = { name, role: "user", credits: 0,
        passwordHash: hashPassword(password, salt), salt,
        session, usedTokens: 0, createdAt: new Date().toISOString(), disabled: false,
        myCode: newMyCode(users) };
      await store.setUsers(users);
      return sendJson(res, 200, { ok: true, session, user: cleanUser(token, users[token]),
        token, note: "API token 請妥善保存（只顯示這一次）；初始 0 點，請聯繫管理員充值" });
    }

    // ── 登入 ──
    if (action === "login") {
      const name = String(body.name || "").trim().toLowerCase();
      const password = String(body.password || "");
      const users = (await store.getUsers()) || {};
      const found = Object.entries(users).find(([t, u]) => String(u.name || "").toLowerCase() === name);
      if (!found) return sendJson(res, 401, { ok: false, error: { message: "帳號或密碼錯誤" } });
      const [token, u] = found;
      if (u.disabled) return sendJson(res, 403, { ok: false, error: { message: "帳號已停用" } });
      if (!u.passwordHash || hashPassword(password, u.salt || "") !== u.passwordHash) {
        return sendJson(res, 401, { ok: false, error: { message: "帳號或密碼錯誤" } });
      }
      u.session = randomToken("ses");          // 每次登入換新 session
      await store.setUsers(users);
      return sendJson(res, 200, { ok: true, session: u.session, user: cleanUser(token, u) });
    }

    // 以下需登入
    const a = await auth(req);
    if (!a.ok) return sendJson(res, 401, { ok: false, error: { message: "請先登入" } });

    // ── 登出 ──
    if (action === "logout") {
      if (a.session && a.user) {
        const users = (await store.getUsers()) || {};
        if (users[a.user.token]) {
          users[a.user.token].session = "";
          await store.setUsers(users);
        }
      }
      return sendJson(res, 200, { ok: true });
    }

    // ── 每日簽到（加額度；每天一次，寫死一天一次防刷）──
    if (action === "checkin") {
      if (a.kind === "legacy") {
        return sendJson(res, 400, { ok: false, error: { message: "共用入口不支援簽到，請用帳號登入" } });
      }
      if (a.kind === "admin" && !a.user) {
        return sendJson(res, 400, { ok: false, error: { message: "ADMIN_TOKEN 不用簽到" } });
      }
      const today = (() => {
        const t = new Date();
        const p = (n) => String(n).padStart(2, "0");
        return `${t.getFullYear()}-${p(t.getMonth() + 1)}-${p(t.getDate())}`;
      })();
      const users = (await store.getUsers()) || {};
      const u = users[a.user.token];
      if (!u || u.disabled) return sendJson(res, 403, { ok: false, error: { message: "帳號已停用" } });
      if (u.lastCheckin === today) {
        return sendJson(res, 200, { ok: true, checked: false, credits: u.credits,
          message: "今天已簽到過，明天再來" });
      }
      // 獎勵倍率 = 活動 × 方案（預留的活動/方案結構，預設都是 1）
      let mult = 1;
      try { const ev = store.activeEvent(await store.getEvent()); if (ev) mult *= Number(ev.mult) || 1; } catch {}
      try { const plans = await store.getPlans(); mult *= Number((plans[u.plan || "free"] || {}).rewardMult) || 1; } catch {}
      const rawAward = Number(process.env.CHECKIN_CREDITS);
      const award = ((Number.isFinite(rawAward) && rawAward > 0) ? rawAward : 10) * mult;   // 預設 10 點/天（1點=US$1）；env 可設含小數
      u.lastCheckin = today;
      u.checkinLog = [...healCheckinLog(u), today].slice(-90);
      if (u.credits !== -1) u.credits = (Number(u.credits) || 0) + award;
      await store.setUsers(users);
      return sendJson(res, 200, { ok: true, checked: true, award, credits: u.credits, mult,
        message: `簽到成功 +${award} 點${mult > 1 ? `（×${mult} 加成）` : ""}` });
    }

    // ── 模型價格表（任何登入身分可讀：官方參考價 × 站內倍率）──
    if (action === "pricing") {
      return sendJson(res, 200, { ok: true,
        pricing: await store.getPricing(), prices: store.MODEL_PRICES,
        specs: store.MODEL_SPECS,
        defaults: store.DEFAULT_PRICING, pointsPerUsd: store.POINTS_PER_USD });
    }

    // ── 逐筆請求明細（個人200筆；scope=site 全局日誌；admin 可帶 token 鑽取）──
    if (action === "reqdetail") {
      const scope = url.searchParams.get("scope");
      if (scope === "site") {
        const logs = await store.getLogs();
        return sendJson(res, 200, { ok: true, rows: logs.map((e) => ({
          t: e.t, model: e.model, tokens: e.tokens, cost: e.cost,
          user: e.user || "", key: e.key || "" })) });
      }
      const qTok = url.searchParams.get("token");
      const tok = (qTok && a.kind === "admin") ? qTok : (a.user ? a.user.token : null);
      if (!tok) return sendJson(res, 200, { ok: true, rows: [] });
      return sendJson(res, 200, { ok: true, rows: await store.getUserReqs(tok) });
    }

    // ── 實測速度：scope=site 全站；token= 指定用戶(admin 鑽取)；其餘看自己 ──
    if (action === "speed") {
      const arr = await store.getSpeed();
      const scope = url.searchParams.get("scope");
      const qTok = url.searchParams.get("token");
      let out;
      if (qTok && a.kind === "admin") out = arr.filter((e) => e.u === qTok);
      else if (scope === "site" || (a.kind === "admin" && scope !== "me")) out = arr;
      else out = arr.filter((e) => e.u === (a.user ? a.user.token : ""));
      return sendJson(res, 200, { ok: true, points: out.slice(-300) });   // 圖表最多載300點
    }

    // ── 方案：資訊（窗口用量/本月API消耗/回本ROI）＋點數訂閱 ──
    if (action === "plan.info") {
      if (!a.user) return sendJson(res, 400, { ok: false, error: { message: "此身分需帳號" } });
      const users = (await store.getUsers()) || {};
      const u = users[a.user.token];
      if (!u) return sendJson(res, 404, { ok: false, error: { message: "找不到帳號" } });
      const plans = await store.getPlans();
      const ev = store.activeEvent(await store.getEvent());
      const pid = store.activePlanOf(u, plans);
      const caps = store.planCapsFor(plans, pid, ev);
      const used5 = store.hourlySpend(u, 5), usedWk = store.hourlySpend(u, 168);
      // 本月 API 消耗（usage 日誌 points 加總，1點=US$1）
      let monthSpend = 0;
      try {
        const all = await store.getUsage(31);
        const now = new Date();
        const ym = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
        for (const d of all || []) if ((d.day || "").startsWith(ym)) {
          const e = d.data && d.data[a.user.token];
          if (e) monthSpend += Number(e.points) || 0;
        }
      } catch {}
      const fee = caps.fee;
      return sendJson(res, 200, { ok: true, plan: pid, label: caps.label,
        active: pid !== "free", subUntil: u.subUntil || "",
        caps, ev: ev ? { mult: ev.mult, label: ev.label, until: ev.until } : null,
        used5, usedWk, monthSpend, fee,
        roi: fee > 0 ? { fee, spend: monthSpend, paid: monthSpend >= fee } : null,
        plans: Object.entries(plans).map(([id, p]) => ({ id,
          label: p.label || id, fee: Number(p.fee) || 0, h5: Number(p.h5) || 0,
          wk: Number(p.wk) || 0, monthlyQuota: Number(p.monthlyQuota) || 0,
          rewardMult: Number(p.rewardMult) || 1 })) });
    }
    if (action === "plan.subscribe") {
      if (!a.user) return sendJson(res, 400, { ok: false, error: { message: "此身分需帳號" } });
      const users = (await store.getUsers()) || {};
      const u = users[a.user.token];
      if (!u || u.disabled) return sendJson(res, 403, { ok: false, error: { message: "帳號已停用" } });
      const plans = await store.getPlans();
      const want = String(body.plan || "").toLowerCase();
      const p = plans[want];
      if (!p) return sendJson(res, 400, { ok: false, error: { message: "方案不存在" } });
      const fee = Number(p.fee) || 0;
      if (u.credits !== -1 && (Number(u.credits) || 0) < fee) {
        return sendJson(res, 402, { ok: false, error: { message: `點數不足（${p.label || want} 方案費 ${fee} 點）` } });
      }
      if (fee > 0 && u.credits !== -1) u.credits = Math.round(((Number(u.credits) || 0) - fee) * 1e6) / 1e6;
      u.plan = want;
      u.monthlyQuota = Number(p.monthlyQuota) || 0;
      u.subUntil = new Date(Date.now() + 30 * 86400000).toISOString();
      await store.setUsers(users);
      return sendJson(res, 200, { ok: true, plan: want, fee, credits: u.credits,
        subUntil: u.subUntil, message: want === "free" ? "已回到 Free 方案"
        : `已訂閱 ${p.label || want} · 30天（扣 ${fee} 點）` });
    }

    // ── 我的 API 金鑰（一帳號多把子金鑰，同錢包同額度；主金鑰=帳號token不可刪）──
    if (action === "ak.create" || action === "ak.toggle" || action === "ak.delete") {
      if (!a.user) return sendJson(res, 400, { ok: false, error: { message: "此身分不用 API 金鑰" } });
      const users = (await store.getUsers()) || {};
      const u = users[a.user.token];
      if (!u || u.disabled) return sendJson(res, 403, { ok: false, error: { message: "帳號已停用" } });
      u.keys = Array.isArray(u.keys) ? u.keys : [];
      if (action === "ak.create") {
        const name = String(body.name || "").trim().slice(0, 24);
        if (!name) return sendJson(res, 400, { ok: false, error: { message: "金鑰名稱不可為空" } });
        if (u.keys.length >= 20) {
          return sendJson(res, 400, { ok: false, error: { message: "最多 20 把，先刪一把再說" } });
        }
        const ent = { id: "aki_" + require("crypto").randomBytes(5).toString("hex"),
          name, secret: randomToken("ak"), disabled: false,
          createdAt: new Date().toISOString() };
        u.keys.push(ent);
        await store.setUsers(users);
        return sendJson(res, 200, { ok: true, key: ent });   // secret 這裡回一次（/me 也會帶）
      }
      const idx = u.keys.findIndex((k) => k.id === body.id);
      if (idx < 0) return sendJson(res, 404, { ok: false, error: { message: "找不到這把金鑰" } });
      if (action === "ak.toggle") {
        u.keys[idx].disabled = body.disabled !== false;
        await store.setUsers(users);
        return sendJson(res, 200, { ok: true, disabled: u.keys[idx].disabled });
      }
      u.keys.splice(idx, 1);
      await store.setUsers(users);
      return sendJson(res, 200, { ok: true });
    }

    // ── 我的帳號 ──
    if (action === "me") {
      if (a.kind === "legacy") return sendJson(res, 200, { ok: true, kind: "legacy", note: "共用入口，不扣點" });
      if (a.kind === "admin" && !a.user) {
        return sendJson(res, 200, { ok: true, kind: "admin", name: "ADMIN_TOKEN", note: "最高權限後門" });
      }
      // 活動資訊（給前端橫幅；無活動回 null）
      let event = null;
      try { event = store.activeEvent(await store.getEvent()); } catch { event = null; }
      // 舊帳號補發個人推薦碼
      let userObj = a.user;
      try {
        if (!userObj.myCode) {
          const users = (await store.getUsers()) || {};
          const u = users[userObj.token];
          if (u && !u.myCode) {
            u.myCode = newMyCode(users);
            await store.setUsers(users);
            userObj = { ...userObj, myCode: u.myCode };
          }
        }
      } catch { /* 補發失敗不擋路 */ }
      // 簽到按鈕面額 = 基礎(CHECKIN_CREDITS, 預設10) × 活動 × 方案 —— 與實際發放同一條式
      let checkinAward = 10;
      try {
        const rawA = Number(process.env.CHECKIN_CREDITS);
        let aw = (Number.isFinite(rawA) && rawA > 0) ? rawA : 10;
        if (event) aw *= Number(event.mult) || 1;
        const plans = await store.getPlans();
        aw *= Number((plans[userObj.plan || "free"] || {}).rewardMult) || 1;
        checkinAward = aw;
      } catch { /* 顯示失敗不擋路 */ }
      return sendJson(res, 200, { ok: true, kind: a.kind, user: cleanUser(userObj.token, userObj), event, checkinAward });
    }

    // ── 用量（+ mstat 每模型：7天 tokens/請求 · 目前RPM · 平均t/s；scope=site 全站公開、scope=me 個人）──
    if (action === "usage") {
      const days = url.searchParams.get("days") || body.days;
      const all = await store.getUsage(days);
      const qToken = url.searchParams.get("token") || body.token;
      const scope = url.searchParams.get("scope") || body.scope;
      const cnt = (mm) => { const o = {}; for (const [m, v] of Object.entries(mm || {})) o[m] = typeof v === "number" ? v : (v && v.r) || 0; return o; };
      const wantAgg = scope ? scope === "site" : (a.kind === "admin" && !qToken);
      const scopeTok = wantAgg ? null : (qToken || (a.user && a.user.token) || null);
      // ① 7天 tokens/請求（per model，含舊格式相容）
      const ms = {};
      for (const d of all || []) {
        if (!d.data) continue;
        const ents = wantAgg ? Object.values(d.data) : (scopeTok && d.data[scopeTok] ? [d.data[scopeTok]] : []);
        for (const ent of ents) for (const [m, v] of Object.entries(ent.models || {})) {
          const o = ms[m] || (ms[m] = { tk: 0, r: 0, rpm: 0, ts: 0, tn: 0 });
          if (typeof v === "number") o.r += v; else { o.r += (v && v.r) || 0; o.tk += (v && v.tk) || 0; }
        }
      }
      // ② 目前RPM + 平均t/s（速度環；admin看全站、其餘看自己）
      try {
        let spd = await store.getSpeed();
        if (!wantAgg) spd = spd.filter((e) => e.u === scopeTok);
        const cut = Date.now() - 60000;
        for (const e of spd) {
          const o = ms[e.model] || (ms[e.model] = { tk: 0, r: 0, rpm: 0, ts: 0, tn: 0 });
          if (e.t >= cut) o.rpm += 1;
          o.ts += Number(e.tps) || 0; o.tn += 1;
        }
      } catch { /* 速度環讀失敗不擋 */ }
      const mstat = Object.entries(ms).map(([model, o]) => ({
        model, tokens: o.tk, reqs: o.r, rpm: o.rpm,
        tps: o.tn ? Math.round((o.ts / o.tn) * 10) / 10 : 0,
      })).sort((x, y) => y.tokens - x.tokens || y.reqs - x.reqs);

      if (a.kind === "admin" && qToken) {
        const mine = (all || []).map((d) => { const e = d.data[qToken];
          return { day: d.day, ...(e ? { ...e, models: cnt(e.models) } : { tokens: 0, reqs: 0, models: {} }) }; });
        return sendJson(res, 200, { ok: true, usage: mine, mstat });
      }
      if (wantAgg) {
        const agg = (all || []).map((d) => {
          let tokens = 0, reqs = 0;
          const users = Object.keys(d.data || {});
          const models = {};
          for (const tk of users) {
            const e = d.data[tk] || {};
            tokens += e.tokens || 0;
            reqs += e.reqs || 0;
            for (const [m, v] of Object.entries(e.models || {})) {
              models[m] = (models[m] || 0) + (typeof v === "number" ? v : (v && v.r) || 0);
            }
          }
          return { day: d.day, tokens, reqs, users: users.length, models };
        });
        return sendJson(res, 200, { ok: true, usage: agg, mstat });
      }
      if (!a.user) return sendJson(res, 200, { ok: true, usage: [], mstat: [] });
      const mine = (all || []).map((d) => { const e = d.data[a.user.token];
        return { day: d.day, ...(e ? { ...e, models: cnt(e.models) } : { tokens: 0, reqs: 0, models: {} }) }; });
      return sendJson(res, 200, { ok: true, usage: mine, mstat });
    }

    // ── 兌換邀請碼（加額度；需登入 user）──
    if (action === "invites.redeem") {
      if (a.kind === "legacy" || (a.kind === "admin" && !a.user)) {
        return sendJson(res, 400, { ok: false, error: { message: "此身分不需兌換" } });
      }
      const code = String(body.code || "").trim().toUpperCase();
      if (!code) return sendJson(res, 400, { ok: false, error: { message: "請輸入邀請碼" } });
      const users = (await store.getUsers()) || {};
      const u = users[a.user.token];
      if (!u || u.disabled) return sendJson(res, 403, { ok: false, error: { message: "帳號已停用" } });

      // ① 個人推薦碼（U-XXXX-XXXX）：雙向獎勵，每人限用一次推薦碼
      const refEntry = Object.entries(users).find(([tk, x]) => x.myCode === code && tk !== a.user.token);
      if (refEntry) {
        const refUser = refEntry[1];
        if (u.referredBy) {
          return sendJson(res, 400, { ok: false, error: { message: "已經用過推薦碼了（每人限一次）" } });
        }
        let gain = Math.max(1, Number(process.env.REFERRAL_CREDITS) || 1000);
        try { const ev = store.activeEvent(await store.getEvent()); if (ev) gain *= Number(ev.mult) || 1; } catch {}
        if (u.credits !== -1) u.credits = (Number(u.credits) || 0) + gain;
        if (refUser.credits !== -1) refUser.credits = (Number(refUser.credits) || 0) + gain;
        u.referredBy = refUser.name || "好友";
        refUser.refCount = (Number(refUser.refCount) || 0) + 1;
        await store.setUsers(users);
        return sendJson(res, 200, { ok: true, added: gain, credits: u.credits,
          message: `推薦成功：你 +${gain} 點，「${refUser.name}」也 +${gain} 點` });
      }

      // ② 管理員建立的邀請碼
      const inv = await store.getInvites();
      const v = inv[code];
      if (!v || v.disabled) return sendJson(res, 404, { ok: false, error: { message: "邀請碼無效" } });
      if ((v.used || 0) >= v.maxUses) {
        return sendJson(res, 400, { ok: false, error: { message: "邀請碼已用完" } });
      }
      v.used = (v.used || 0) + 1;
      if (u.credits !== -1) u.credits = (Number(u.credits) || 0) + v.credits;
      await store.setInvites(inv);
      await store.setUsers(users);
      return sendJson(res, 200, { ok: true, added: v.credits, credits: u.credits,
        message: `兌換成功 +${v.credits} 點` });
    }

    return sendJson(res, 400, { ok: false, error: { message: "未知 action: " + action } });
  } catch (e) {
    return sendJson(res, 500, { ok: false, error: { message: String((e && e.message) || e) } });
  }
};
