#!/usr/bin/env node
/**
 * aivtuber-yt CLI
 *   npx aivtuber-yt @頻道            頻道在播就即時印留言（不在播就報狀態）
 *   npx aivtuber-yt resolve @頻道     只查目前直播（不輪詢）
 *   npx aivtuber-yt chat <videoId>    直接輪詢指定直播
 */
const yt = require("../src/index.js");

function help() {
  console.log(`aivtuber-yt — YouTube Live 聊天室（免 API 金鑰）

用法：
  aivtuber-yt @頻道            頻道在播即時印留言
  aivtuber-yt resolve @頻道     只查目前直播
  aivtuber-yt chat <videoId>    輪詢指定直播

頻道支援：@handle / 完整網址 / UC 開頭的 channel id`);
}

async function main() {
  const [cmd, arg] = process.argv.slice(2);
  if (!cmd || cmd === "-h" || cmd === "--help") return help();

  if (cmd === "resolve") {
    if (!arg) { console.error("請給頻道（例：aivtuber-yt resolve @LofiGirl）"); process.exit(1); }
    const live = await yt.resolveLive(arg);
    console.log(JSON.stringify(live, null, 1));
    return;
  }

  if (cmd === "chat") {
    if (!arg) { console.error("請給 videoId"); process.exit(1); }
    const vid = yt.normalizeVideoId(arg) || arg;
    console.log(`監聽 ${vid}（Ctrl+C 停止）…`);
    await yt.watch(vid, (m) => console.log(`[${m.user}] ${m.message}`),
      { onError: (e) => console.error("!", e.message) });
    return;
  }

  // 預設：當成頻道
  const live = await yt.resolveLive(cmd);
  if (!live.ok || !live.videoId) {
    console.error("頻道解析失敗（YouTube 改版或網路問題）");
    process.exit(1);
  }
  if (!live.isLive) {
    console.log(`目前沒在播（最近：${live.title || live.videoId}）`);
    return;
  }
  console.log(`正在播：${live.title}（${live.videoId}），留言如下（Ctrl+C 停止）…`);
  await yt.watch(live.videoId, (m) => console.log(`[${m.user}] ${m.message}`),
    { onError: (e) => console.error("!", e.message) });
}

main().catch((e) => { console.error("失敗：", e.message); process.exit(1); });
