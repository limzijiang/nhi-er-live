# 台灣急診即時壅塞看板

全國重度級急救責任醫院急診即時與歷史壅塞資料看板。

- **網站**：https://limzijiang.github.io/nhi-er-live/
- **資料來源**：[衛福部健保署急診即時訊息](https://info.nhi.gov.tw/INAE4000/INAE4001S01)（公開 API，每 15 分鐘更新）
- **作法參考**：[KJT125/Nhi-er-open-data](https://github.com/KJT125/Nhi-er-open-data)

## 運作方式

1. GitHub Actions（[fetch.yml](.github/workflows/fetch.yml)）每 15 分鐘執行 [scripts/fetch_er.py](scripts/fetch_er.py)
2. 最新快照寫入 `data/latest.json`，歷史依日期累積到 `data/history/YYYY-MM-DD.json`
3. [index.html](index.html) 為純靜態前端（無外部依賴），由 GitHub Pages 提供

## 資料格式

`data/history/YYYY-MM-DD.json`：

```json
{
  "date": "2026-07-10",
  "hosp": { "醫院代碼": { "n": "醫院名", "a": "地區代碼", "t": "層級" } },
  "snaps": [ { "t": "2026-07-10 20:45", "d": { "醫院代碼": [等看診, 推床, 等住院, 等ICU, 119滿床] } } ]
}
```

數值為 `null` 表示該院該時段未回報。**推床數各院填報標準不一，不可靠，僅供參考。**

## 授權與聲明

資料為去識別化之機構層級統計，來源為衛生福利部中央健康保險署。數字僅供參考，實際狀況以各院及 119 為準。
