# aivtuber-yt

YouTube Live 聊天室，免 API 金鑰。給 AI VTuber 用的觀眾留言輸入。

```bash
npx aivtuber-yt @你的頻道
```

## 用法

```bash
# 頻道在播 → 即時印留言（不在播就報狀態）
aivtuber-yt @LofiGirl

# 只查目前直播（不輪詢）
aivtuber-yt resolve @LofiGirl
# {"videoId": "3PFJ9SETS4M", "isLive": true, "title": "lofi radio", "ok": true}

# 直接輪詢指定直播
aivtuber-yt chat 3PFJ9SETS4M
```

頻道支援三種：`@handle` / 完整網址 / `UC` 開頭的 channel id。

## 程式用法

```js
const yt = require("aivtuber-yt");

// 頻道 → 目前直播
const live = await yt.resolveLive("@LofiGirl");
if (!live.isLive) { console.log("沒在播"); return; }

// 持續監聽
const { stop } = await yt.watch(live.videoId,
  (m) => console.log(`[${m.user}] ${m.message}`),
  { onError: (e) => console.error(e.message) });
// … stop();
```

## 原理

- 頻道 → `{channel}/live` 頁：canonical 取 videoId +
  `ytInitialPlayerResponse.videoDetails.isLiveContent` 判在播
- 聊天 → `live_chat` 頁拿 continuation → InnerTube `get_live_chat` 輪詢
  （載荷欄位是 `continuation`；下一代 token 在
  `continuations[0].invalidationContinuationData.continuation`）

## 注意

非官方端點：YouTube 改版可能失效。失效時 `watch()` 會持續重試並回報，
不會拋錯中斷（除非你 `stop()`）。
