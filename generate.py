import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST)
DATE_STR = TODAY.strftime("%Y%m%d")
DATE_DISPLAY = TODAY.strftime("%Y/%m/%d")
TIME_DISPLAY = TODAY.strftime("%H:%M")

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
    {"name": "암페놀",         "symbol": "APH",       "market": "US"},
    {"name": "SK",             "symbol": "034730.KS", "market": "KR"},
    {"name": "삼성전자우선주", "symbol": "005935.KS", "market": "KR"},
]

def get_quote(symbol):
    try:
        url = "https://finnhub.io/api/v1/quote?symbol=" + symbol + "&token=" + API_KEY
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
    if pct > 0:
        return "#e53935"
    if pct < 0:
        return "#1565c0"
    return "#555"

def sign(pct):
    if pct >= 0:
        return "+" + "{:.2f}".format(pct) + "%"
    return "{:.2f}".format(pct) + "%"

def fmt_price(p, market):
    if market == "KR":
        return "{:,.0f}".format(p) + "원"
    return "$" + "{:,.2f}".format(p)

def fmt_amt(a):
    if a >= 0:
        return "+" + "{:,.0f}".format(a)
    return "{:,.0f}".format(a)

def collect_holdings():
    results = []
    for h in HOLDINGS:
        q = get_quote(h["symbol"])
        p = q["price"]
        if p:
            pnl_pct = (p - h["avg"]) / h["avg"] * 100
            pnl_amt = (p - h["avg"]) * h["shares"]
        else:
            pnl_pct = 0
            pnl_amt = 0
        results.append({
            "name": h["name"], "symbol": h["symbol"],
            "shares": h["shares"], "avg": h["avg"], "market": h["market"],
            "price": p, "change_pct": q["change_pct"],
            "pnl_pct": pnl_pct, "pnl_amt": pnl_amt
        })
    return results

def collect_watchlist():
    results = []
    for w in WATCHLIST:
        q = get_quote(w["symbol"])
        results.append({
            "name": w["name"], "symbol": w["symbol"], "market": w["market"],
            "price": q["price"], "change_pct": q["change_pct"]
        })
    return results

def holding_rows(items):
    rows = ""
    for h in items:
        p = h["price"]
        if not p:
            rows += "<tr><td>" + h["name"] + "</td><td colspan='4' style='color:#aaa;text-align:center'>데이터 없음</td></tr>\n"
            continue
        rows += "<tr>"
        rows += "<td>" + h["name"] + "</td>"
        rows += "<td style='text-align:right'>" + fmt_price(p, h["market"]) + "</td>"
        rows += "<td style='text-align:right;color:" + color(h["change_pct"]) + ";font-weight:600'>" + sign(h["change_pct"]) + "</td>"
        rows += "<td style='text-align:right;color:" + color(h["pnl_pct"]) + ";font-weight:600'>" + sign(h["pnl_pct"]) + "</td>"
        rows += "<td style='text-align:right;color:" + color(h["pnl_amt"]) + "'>" + fmt_amt(h["pnl_amt"]) + "</td>"
        rows += "</tr>\n"
    return rows

def watch_rows(items):
    rows = ""
    for w in items:
        p = w["price"]
        if not p:
            rows += "<tr><td>" + w["name"] + "</td><td colspan='2' style='color:#aaa;text-align:center'>데이터 없음</td></tr>\n"
            continue
        rows += "<tr>"
        rows += "<td>" + w["name"] + "</td>"
        rows += "<td style='text-align:right'>" + fmt_price(p, w["market"]) + "</td>"
        rows += "<td style='text-align:right;color:" + color(w["change_pct"]) + ";font-weight:600'>" + sign(w["change_pct"]) + "</td>"
        rows += "</tr>\n"
    return rows

def make_html(holdings, watchlist):
    kr = [h for h in holdings if h["market"] == "KR"]
    us = [h for h in holdings if h["market"] == "US"]
    total_eval = sum(
        (h["avg"] * h["shares"] + h["pnl_amt"])
        for h in holdings if h["price"]
    )

    css = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #f5f6fa; color: #222; font-size: 14px; }
    .wrap { max-width: 640px; margin: 0 auto; padding: 16px; }
    .header { background: #1a237e; color: #fff; border-radius: 12px;
              padding: 20px; margin-bottom: 16px; }
    .header h1 { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
    .header .date { font-size: 13px; opacity: 0.75; }
    .card { background: #fff; border-radius: 12px; padding: 16px;
            margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); }
    .card h2 { font-size: 13px; font-weight: 700; color: #1a237e;
               border-bottom: 2px solid #e8eaf6; padding-bottom: 8px;
               margin-bottom: 12px; }
    table { width: 100%; border-collapse: collapse; }
    th { font-size: 11px; color: #888; text-align: right; padding: 4px 6px; }
    th:first-child { text-align: left; }
    td { padding: 7px 6px; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
    td:first-child { font-weight: 500; }
    tr:last-child td { border-bottom: none; }
    .total-bar { background: #e8eaf6; border-radius: 8px; padding: 10px 14px;
                 display: flex; justify-content: space-between; align-items: center;
                 margin-top: 10px; }
    .total-bar span { font-size: 12px; color: #555; }
    .total-bar strong { font-size: 15px; color: #1a237e; }
    .footer { text-align: center; font-size: 11px; color: #aaa;
              margin-top: 16px; padding-bottom: 24px; }
    """

    html = "<!DOCTYPE html>\n"
    html += "<html lang='ko'>\n<head>\n"
    html += "<meta charset='UTF-8'>\n"
    html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
    html += "<title>모닝 브리핑 " + DATE_DISPLAY + "</title>\n"
    html += "<style>" + css + "</style>\n"
    html += "</head>\n<body>\n<div class='wrap'>\n"

    html += "<div class='header'>"
    html += "<h1>💼 모닝 브리핑</h1>"
    html += "<div class='date'>" + DATE_DISPLAY + " · " + TIME_DISPLAY + " KST</div>"
    html += "</div>\n"

    html += "<div class='card'>"
    html += "<h2>🇰🇷 국내 보유주식</h2>"
    html += "<table><tr><th>종목</th><th>현재가</th><th>등락률</th><th>수익률</th><th>손익(원)</th></tr>"
    html += holding_rows(kr)
    html += "</table></div>\n"

    html += "<div class='card'>"
    html += "<h2>🌍 해외 보유주식</h2>"
    html += "<table><tr><th>종목</th><th>현재가</th><th>등락률</th><th>수익률</th><th>손익($)</th></tr>"
    html += holding_rows(us)
    html += "</table>"
    html += "<div class='total-bar'><span>상장주식 총 평가금액 추정</span>"
    html += "<strong>" + "{:,.0f}".format(total_eval) + "</strong></div>"
    html += "</div>\n"

    html += "<div class='card'>"
    html += "<h2>👀 관심종목</h2>"
    html += "<table><tr><th>종목</th><th>현재가</th><th>등락률</th></tr>"
    html += watch_rows(watchlist)
    html += "</table></div>\n"

    html += "<div class='footer'>"
    html += "본 페이지는 투자 참고용이며, 모든 투자 판단과 책임은 본인에게 있습니다.<br>"
    html += "데이터 생성: " + TODAY.strftime("%Y-%m-%d %H:%M") + " KST"
    html += "</div>\n"

    html += "</div>\n</body>\n</html>"
    return html

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    print("데이터 수집 중...")
    holdings = collect_holdings()
    watchlist = collect_watchlist()
    html = make_html(holdings, watchlist)
    with open("docs/" + DATE_STR + ".html", "w", encoding="utf-8") as f:
        f.write(html)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("완료: docs/" + DATE_STR + ".html")
