import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST)
DATE_STR = TODAY.strftime("%Y%m%d")
DATE_DISPLAY = TODAY.strftime("%Y/%m/%d")

API_KEY = os.environ.get("FINNHUB_API_KEY", "")

HOLDINGS = [
    {"name": "산일전기",      "symbol": "062040.KS", "shares": 47,    "avg": 289872, "market": "KR"},
    {"name": "엘앤에프",      "symbol": "066970.KS", "shares": 80,    "avg": 186450, "market": "KR"},
    {"name": "SK하이닉스",    "symbol": "000660.KS", "shares": 3,     "avg": 199300, "market": "KR"},
    {"name": "삼성전자",      "symbol": "005930.KS", "shares": 10,    "avg": 296500, "market": "KR"},
    {"name": "코오롱티슈진",  "symbol": "950160.KS", "shares": 20,    "avg": 113300, "market": "KR"},
    {"name": "로켓 랩",       "symbol": "RKLB",      "shares": 51.13, "avg": 9.90,   "market": "US"},
    {"name": "네비우스 그룹", "symbol": "NVVS",      "shares": 15.09, "avg": 29.44,  "market": "US"},
    {"name": "인플렉션",      "symbol": "INFN",      "shares": 300,   "avg": 23.59,  "market": "US"},
    {"name": "알파벳 A",      "symbol": "GOOGL",     "shares": 7.99,  "avg": 200.35, "market": "US"},
    {"name": "TMC 더 메탈스", "symbol": "TMC",       "shares": 320,   "avg": 10.96,  "market": "US"},
    {"name": "엔비디아",      "symbol": "NVDA",      "shares": 0.81,  "avg": 110.97, "market": "US"},
    {"name": "SPYM",          "symbol": "SPYM",      "shares": 0.86,  "avg": 57.13,  "market": "US"},
    {"name": "IBM",           "symbol": "IBM",       "shares": 0.033, "avg": 223.48, "market": "US"},
]

WATCHLIST = [
    {"name": "암페놀",        "symbol": "APH",       "market": "US"},
    {"name": "SK",            "symbol": "034730.KS", "market": "KR"},
    {"name": "삼성전자우선주", "symbol": "005935.KS", "market": "KR"},
]

def get_quote(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
            c = data.get("c", 0)
            pc = data.get("pc", 0)
            if c and pc:
                return {"price": c, "change_pct": (c - pc) / pc * 100}
    except Exception:
        pass
    return {"price": 0, "change_pct": 0}

def color(pct):
    if pct > 0: return "#e53935"
    if pct < 0: return "#1565c0"
    return "#555"

def sign(pct):
    return f"+{pct:.2f}%" if pct >= 0 else f"{pct:.2f}%"

def fmt_price(p, market):
    return f"{p:,.0f}원" if market == "KR" else f"${p:,.2f}"

def collect_holdings():
    results = []
    for h in HOLDINGS:
        q = get_quote(h["symbol"])
        p = q["price"]
        pnl_pct = (p - h["avg"]) / h["avg"] * 100 if p else 0
        pnl_amt = (p - h["avg"]) * h["shares"] if p else 0
        results.append({**h, "price": p, "change_pct": q["change_pct"],
                        "pnl_pct": pnl_pct, "pnl_amt": pnl_amt})
    return results

def collect_watchlist():
    results = []
    for w in WATCHLIST:
        q = get_quote(w["symbol"])
        results.append({**w, "price": q["price"], "change_pct": q["change_pct"]})
    return results

def holding_rows(items):
    rows = ""
    for h in items:
        p = h["price"]
        if not p:
            rows += f"<tr><td>{h['name']}</td><td colspan='4' style='color:#aaa;text-align:center'>데이터 없음</td></tr>"
            continue
        rows += f"""<tr>
          <td>{h['name']}</td>
          <td style='text-align:right'>{fmt_price(p, h['market'])}</td>
          <td style='text-align:right;color:{color(h['change_pct'])};font-weight:600'>{sign(h['change_pct'])}</td>
          <td style='text-align:right;color:{color(h['pnl_pct'])};font-weight:600'>{sign(h['pnl_pct'])}</td>
          <td style='text-align:right;color:{color(h['pnl_amt'])}'>{h['pnl_amt']:+,.0f}</td>
        </tr>"""
    return rows

def watch_rows(items):
    rows = ""
    for w in items:
        p = w["price"]
        if not p:
            rows += f"<tr><td>{w['name']}</td><td colspan='2' style='color:#aaa;text-align:center'>데이터 없음</td></tr>"
            continue
        rows += f"""<tr>
          <td>{w['name']}</td>
          <td style='text-align:right'>{fmt_price(p, w['market'])}</td>
          <td style='text-align:right;color:{color(w['change_pct'])};font-weight:600'>{sign(w['change_pct'])}</td>
        </tr>"""
    return rows

def make_html(holdings, watchlist):
    kr = [h for h in holdings if h["market"] == "KR"]
    us = [h for h in holdings if h["market"] == "US"]
    total_eval = sum(h["pnl_amt"] + h["avg"] * h["shares"] for h in holdings if h["price"])

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>모닝 브리핑 {DATE_DISPLAY}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f6fa; color: #222; font-size: 14px; }}
  .wrap {{ max-width: 640px; margin: 0 auto; padding: 16px; }}
  .header {{ background: #1a237e; color: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px; }}
  .header h1 {{ font-size: 18px; font-weight: 700; margin-bottom: 4px; }}
  .header .date {{ font-size: 13px; opacity: 0.75; }}
  .card {{ background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); }}
  .card h2 {{ font-size: 13px; font-weight: 700; color: #1a237e; border-bottom: 2px solid #e8eaf6; padding-bottom: 8px; margin-bottom: 12px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ font-size: 11px; color: #888; text-align: right; padding: 4px 6px; }}
  th:first-child {{ text-align: left; }}
  td {{ padding: 7px 6px; border-bottom: 1px solid #f0f0f0; font-size: 13px; }}
  td:first-child {{ font-weight: 500; }}
  tr:last-child td {{ border-bottom: none; }}
  .total-bar {{ background: #e8eaf6; border-radius: 8px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }}
  .total-bar span {{ font-size: 12px; color: #555; }}
  .total-bar strong {{ font-size: 15px; color: #1a237e; }}
  .footer {{ text-align: center; font-size: 11px; color: #aaa; margin-top: 16px; padding-bottom: 24px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>💼 모닝 브리핑</h1>
    <div class="date">{DATE_DISPLAY} · {TODAY.strftime("%H:%M")} KST</div>
  </div>
  <div class="card">
    <h2>🇰🇷 국내 보유주식</h2>
    <table>
      <tr><th>종목</th><th>현재가</th><th>등락률</th><th>수익률</th><th>손익(원)</th></tr>
      {holding_rows(kr)}
    </table>
  </div>
  <div class="card">
    <h2>🌍 해외 보유주식</h2>
    <table>
      <tr><th>종목</th><th>현재가</th><th>등락률</th><th>수익률</th><th>손익($)</th></tr>
      {holding_rows(us)}
    </table>
    <div class="total-bar">
      <span>상장주식 총 평가금액 추정</span>
      <strong>{total_eval:,.0f}</strong>
    </div>
  </div>
  <div class="card">
    <h2>👀 관심종목</h2>
    <table>
      <tr><th>종목</th><th>현재가</th><th>등락률</th></tr>
