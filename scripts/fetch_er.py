#!/usr/bin/env python3
"""抓取健保署急診即時資料，寫入 data/latest.json 並累積到 data/history/YYYY-MM-DD.json

資料來源：衛生福利部中央健康保險署急診即時訊息
API: POST https://info.nhi.gov.tw/api/inae4000/inae4001s01/SQL0002
"""
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

API_URL = "https://info.nhi.gov.tw/api/inae4000/inae4001s01/SQL0002"
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
TAIPEI = timezone(timedelta(hours=8))


def fetch(retries=5):
    req = urllib.request.Request(
        API_URL,
        data=json.dumps({"AREA_NO": "", "CONT_TYPE": ""}).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) er-dashboard",
            "Accept": "application/json",
        },
    )
    last_err = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(5 * (i + 1))
    raise SystemExit(f"API fetch failed after {retries} tries: {last_err}")


def to_int(v):
    """數值欄位：null 表示該院未回報，保留 None 與 0 區分。"""
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def main():
    result = fetch()
    sysdate = (result.get("sysdate") or "").strip()  # e.g. "2026-07-10 20:45"
    rows = result.get("data") or []
    if not sysdate or not rows:
        raise SystemExit("API returned empty payload, nothing written")

    hosp_meta = {}
    values = {}
    for h in rows:
        hid = h.get("hosP_ID")
        if not hid:
            continue
        hosp_meta[hid] = {
            "n": h.get("hosP_NAME", "?"),
            "a": h.get("areA_NO_N", ""),
            "t": h.get("conT_TYPE", ""),
        }
        # [等看診, 推床, 等住院, 等ICU, 119滿床]
        values[hid] = [
            to_int(h.get("waiT_SEE_CNT")),
            to_int(h.get("waiT_BED_CNT")),
            to_int(h.get("waiT_GENERAL_CNT")),
            to_int(h.get("waiT_ICU_CNT")),
            1 if h.get("inform") == "Y" else 0,
        ]

    fetched_at = datetime.now(TAIPEI).strftime("%Y-%m-%d %H:%M:%S")

    DATA_DIR.mkdir(exist_ok=True)
    HISTORY_DIR.mkdir(exist_ok=True)

    (DATA_DIR / "latest.json").write_text(
        json.dumps(
            {"sysdate": sysdate, "fetched_at": fetched_at, "hosp": hosp_meta, "d": values},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    # 依 sysdate 的日期歸檔（台灣時間）
    day = sysdate.split(" ")[0].replace("/", "-")
    day_path = HISTORY_DIR / f"{day}.json"
    if day_path.exists():
        day_data = json.loads(day_path.read_text(encoding="utf-8"))
    else:
        day_data = {"date": day, "hosp": {}, "snaps": []}

    day_data["hosp"].update(hosp_meta)
    if any(s["t"] == sysdate for s in day_data["snaps"]):
        print(f"snapshot {sysdate} already stored, skip")
    else:
        day_data["snaps"].append({"t": sysdate, "d": values})
        day_data["snaps"].sort(key=lambda s: s["t"])
        day_path.write_text(
            json.dumps(day_data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"stored snapshot {sysdate} ({len(values)} hospitals) -> {day_path.name}")

    days = sorted(p.stem for p in HISTORY_DIR.glob("*.json"))
    (DATA_DIR / "days.json").write_text(json.dumps(days), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
