# -*- coding: utf-8 -*-
"""
毎朝 09:00 JST に実行され、XAUUSD と BTCUSD の
Support/Resistance/BreakUp/BreakDown/SL/TP/Trail/RetestRange を自動算出して
repo 直下の parameters.json を上書き保存する。

ロジック（シンプルで安定動作を優先）:
- データ: yfinance
  - XAUUSD: "XAUUSD=X"
  - BTCUSD: "BTC-USD"
- 期間: 過去90日（足りない時も動くように広め）
- 基本水準:
  - 昨日の High/Low を BreakUp/BreakDown
  - ピボットの S1/R1 を Support/Resistance
- 変動幅:
  - ATR(14) を日足で近似、SL/TP/Trail は ATR の倍率で決定
- 端数: 2桁（XAUUSD は 2、小数有; BTC は整数に丸め）

必要: pip install yfinance pandas pytz
"""

import json
from datetime import datetime
import pytz
import pandas as pd
import yfinance as yf
from pathlib import Path

# ===== チューニング係数（必要に応じて調整） =====
ATR_LEN = 14

# XAU のリスク幅（USD）
XAU_SL_ATR_K = 0.9
XAU_TP_ATR_K = 1.1
XAU_TR_ATR_K = 0.7
XAU_RETEST   = 3.0

# BTC のリスク幅（USD）
BTC_SL_ATR_K = 0.8
BTC_TP_ATR_K = 1.0
BTC_TR_ATR_K = 0.6
BTC_RETEST   = 90.0

# スプレッド上限（EA 側の input と整合を取るならここも管理可能）
XAU_MAX_SPREAD = 6.0
BTC_MAX_SPREAD = 1200.0

# 出力ファイル
OUT = Path("parameters.json")

def atr(df: pd.DataFrame, n=14):
    # True Range = max(High-Low, abs(High-PrevClose), abs(Low-PrevClose))
    h, l, c = df["High"], df["Low"], df["Close"]
    prev_c = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()

def pivot_levels(y):
    """前日データから ピボット P, R1, S1 を返す"""
    high, low, close = float(y["High"]), float(y["Low"]), float(y["Close"])
    p  = (high + low + close) / 3.0
    r1 = 2 * p - low
    s1 = 2 * p - high
    return p, r1, s1, high, low

def fetch(ticker):
    df = yf.download(ticker, period="90d", interval="1d", auto_adjust=False, progress=False)
    df = df.dropna()
    return df

def round_xau(x):
    # XAU は 2桁で丸め
    return round(float(x), 2)

def round_btc(x):
    # BTC は整数で丸め（必要なら 1桁などに変更）
    return int(round(float(x)))

def build_symbol_block(sym, r_sup, r_res, r_bu, r_bd, sl, tp, tr, ret):
    return {
        "Support":    r_sup,
        "Resistance": r_res,
        "BreakUp":    r_bu,
        "BreakDown":  r_bd,
        "SL":         sl,
        "TP":         tp,
        "Trail":      tr,
        "RetestRange": ret
    }

def main():
    # ===== データ取得 =====
    xau = fetch("XAUUSD=X")
    btc = fetch("BTC-USD")

    if len(xau) < 2 or len(btc) < 2:
        raise SystemExit("Not enough data fetched from yfinance.")

    # ===== 前日データ =====
    y_xau = xau.iloc[-2]
    y_btc = btc.iloc[-2]

    # ===== ATR =====
    xau_atr = float(atr(xau, ATR_LEN).iloc[-1])
    btc_atr = float(atr(btc, ATR_LEN).iloc[-1])

    # ===== ピボット & ブレイク水準 =====
    _, xau_r1, xau_s1, xau_high, xau_low = pivot_levels(y_xau)
    _, btc_r1, btc_s1, btc_high, btc_low = pivot_levels(y_btc)

    # ===== レベル算出 =====
    XAU = build_symbol_block(
        "XAUUSD",
        r_sup = round_xau(xau_s1),
        r_res = round_xau(xau_r1),
        r_bu  = round_xau(xau_high),
        r_bd  = round_xau(xau_low),
        sl    = round_xau(xau_atr * XAU_SL_ATR_K),
        tp    = round_xau(xau_atr * XAU_TP_ATR_K),
        tr    = round_xau(xau_atr * XAU_TR_ATR_K),
        ret   = round_xau(XAU_RETEST),
    )

    BTC = build_symbol_block(
        "BTCUSD",
        r_sup = round_btc(btc_s1),
        r_res = round_btc(btc_r1),
        r_bu  = round_btc(btc_high),
        r_bd  = round_btc(btc_low),
        sl    = round_btc(btc_atr * BTC_SL_ATR_K),
        tp    = round_btc(btc_atr * BTC_TP_ATR_K),
        tr    = round_btc(btc_atr * BTC_TR_ATR_K),
        ret   = round_btc(BTC_RETEST),
    )

    # ===== タイムスタンプ（JST） =====
    jst = pytz.timezone("Asia/Tokyo")
    ts  = datetime.now(jst).strftime("%Y-%m-%dT%H:%M:%S%z")
    # 例: 2025-11-05T09:00:00+0900 → EA 側では +09:00 でも +0900 でもOK

    payload = {
        "timestamp": ts,
        "XAUUSD": XAU,
        "BTCUSD": BTC
    }

    # 変更がある時だけ上書き（commit noise を抑制）
    new = json.dumps(payload, ensure_ascii=False, indent=2)
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if new != old:
        OUT.write_text(new, encoding="utf-8")
        print("parameters.json updated")
    else:
        print("parameters.json unchanged")

if __name__ == "__main__":
    main()
