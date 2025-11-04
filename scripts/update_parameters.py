# scripts/update_parameters.py
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

PARAM_FILE = Path("parameters.json")

def jst_now_iso():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).replace(microsecond=0).isoformat()

def main():
    if not PARAM_FILE.exists():
        raise FileNotFoundError("parameters.json が見つかりません。リポジトリ直下に置いてください。")

    with PARAM_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # timestamp を JST の ISO8601 で更新
    data["timestamp"] = jst_now_iso()

    # ここで必要なら値の自動調整ロジックを入れられます（例：据え置き/微調整など）
    # 例）data["XAUUSD"]["Support"] = round(data["XAUUSD"]["Support"], 1)

    with PARAM_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Updated timestamp to:", data["timestamp"])

if __name__ == "__main__":
    main()
