#!/usr/bin/env python3
"""抓取健保署醫療品質指標 1652「急診轉住院暫留急診超過四十八小時案件比率」（季更新）

資料來源：健保醫療品質資訊公開網
https://med.nhi.gov.tw/ihqe0000/pepC_Search001.html?ind=1652&type=2
寫入 data/boarding48.json：{quarter, national, rates: {院所代碼: {r: 比率%, n: 分子, d: 分母}}}
"""
import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://med.nhi.gov.tw/ihqe0000"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "boarding48.json"


def get_json(url, retries=3):
    last_err = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise SystemExit(f"fetch failed: {url}: {last_err}")


def main():
    quarters = get_json(f"{BASE}/IHQE0020S17.ashx?q5id=2&ind=1652")
    latest = quarters[-1]["DataTimeID"]  # e.g. "114Q3"

    rows = get_json(
        f"{BASE}/IHQE0020S12.ashx?year={latest}&city=&name=&hosp=&special=&q5id=2&ind=1652&bc="
    )
    if not rows:
        raise SystemExit(f"no rows for {latest}")

    rates = {}
    national = None
    for r in rows:
        hid = r.get("HOSP_ID")
        if not hid:
            continue
        try:
            rate = float(r.get("INDEX1"))
        except (TypeError, ValueError):
            continue
        rates[hid] = {
            "r": rate,
            "n": r.get("NUMERATOR"),
            "d": r.get("DENOMINATOR"),
        }
        if national is None and r.get("INDEX3"):
            try:
                national = float(r["INDEX3"])
            except ValueError:
                pass

    OUT.write_text(
        json.dumps(
            {"quarter": latest, "national": national, "rates": rates},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    print(f"boarding48: {latest}, {len(rates)} hospitals, national {national}%")


if __name__ == "__main__":
    sys.exit(main())
