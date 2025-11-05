# scripts/generate_params.py
# 標準ライブラリのみで parameters.json の "timestamp" を JST 現在時刻に更新
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "parameters.json"

def iso_jst_now() -> str:
    jst = timezone(timedelta(hours=9))
    # EA ログと合わせて秒精度、タイムゾーンオフセットも出す（例: 2025-11-05T09:00:00+09:00）
    return datetime.now(jst).isoformat(timespec="seconds")

def main() -> None:
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"parameters.json not found at: {JSON_PATH}")

    with JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # 既存値はそのまま、timestamp だけ更新
    data["timestamp"] = iso_jst_now()

    # 見やすい整形で保存（末尾改行あり）
    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Updated timestamp -> {data['timestamp']}")

if __name__ == "__main__":
    main()
