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

HOLDINGS_KR = [
    {"name": "산일전기",     "code": "062040", "shares": 47,    "avg": 289872},
    {"name": "엘앤에프",     "code": "066970", "shares": 80,    "avg": 186450},
    {"name": "SK하이닉스",   "code": "000660", "shares": 3,     "avg": 1993000},
    {"name": "삼성전자",     "code": "005930", "shares": 10,    "avg": 296500},
    {"name": "코오롱티슈진", "code": "950160", "shares": 20,    "avg": 113300},
]

HOLDINGS_US = [
    {"name": "로켓 랩",       "symbol": "RKLB",  "shares": 51.13, "avg": 64.44},
    {"name": "네비우스 그룹", "symbol": "NBIS",  "shares": 15.09, "avg": 191.41},
    {"name": "인플렉션",      "symbol": "INFN",  "shares": 300,   "avg": 15.33},
    {"name": "알파벳 A",      "symbol": "GOOGL", "shares": 7.99,  "avg": 325.25},
    {"name": "TMC 더 메탈스", "symbol": "TMC",   "shares": 320,   "avg": 7.13},
    {"name": "엔비디아",      "symbol": "NVDA",  "shares": 0.81,  "avg": 185.29},
    {"name": "SPYM",          "symbol": "SPYM",  "shares": 0.86,  "avg": 74.34},
    {"name": "IBM",           "symbol": "IBM",   "shares": 0.033, "avg": 290.07},
]

WATCHLIST = [
    {"name": "암페놀",         "symbol": "APH",       "market": "US"},
    {"name": "SK",             "code": "034730",      "market": "KR"},
    {"name": "삼성전자우선주", "code": "005935",      "market": "KR"},
]

def get_naver_price(code):
    try:
        url = "https://finance.naver.com/item/main.nhn?code=" + code
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            html = r.read().decode("euc-kr", errors="ignore")
        import re
        m = re.search(r'<p class="no_today">.*?<span class="blind">현재가</span>.*?<span[^>]*>([\d,]+)</span>', html, re.DOTALL)
        if m:
            return float(m.group(1).replace(",", ""))
        m2 = re.search(r'"신고가[^"]*"[^>]*>[\s\S]*?<strong[^>]*id="chart_area"[\s\S]*?<em[^>]*>([\d,]+)<', html)
        if m2:
            return float(m2.group(1).replace(",", ""))
        m3 = re.search(r'<dd class="today">.*?<span class="blind">현재가</span>([\d,]+)', html, re.DOTALL)
        if m3:
            return float(m3.group(1).replace(",", ""))
        m4 = re.search(r'현재가.*?([\d]{4,7})', html)
        if m4:
            return float(m4.group(1).replace(",", ""))
    except Exception as e:
        print("naver error", code, e)
    return 0

def get_naver_price_api(code):
    try:
        url = "https://polling.finance.naver.com/api/realtime/domestic/stock/" + code
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        price = data.get("result", {}).get("dealTrendInfos", [{}])[0].get("closePrice", 0)
        prev  = data.get("result", {}).get("dealTrendInfos", [{}])[0].get("openPrice", 0)
        if not price:
            price = data.get("result", {}).get("stock", {}).get("closePrice", 0)
            prev  = data.get("result", {}).get("stock", {}).get("compareToPreviousClosePrice", 0)
        if price:
            price = float(str(price).replace(",", ""))
            return {"price": price, "change_pct": 0}
    except Exception as e:
        print("naver api error", code, e)
    return {"price": 0, "change_pct": 0}

def get_kr_quote(code):
    try:
        url = "https://m.stock.naver.com/api/stock/" + code + "/basic"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
            "Referer": "https://m.stock.naver.com"
        })
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        price = float(str(data.get("closePrice", "0")).replace(",", ""))
        change_pct = float(str(data.get("fluctuationsRatio", "0")).replace(",", ""))
        return {"price": price, "change_pct": change_pct}
    except Exception as e:
        print("kr quote error", code, e)
    return {"price": 0, "change_pct": 0}

def get_us_quote(symbol):
    try:
        url = "https://finnhub.io/api/v1/quote?symbol=" + symbol + "&token=" + API_KEY
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
        c = data.get("c", 0)
        pc = data.get("pc", 0)
        if c and pc:
            return {"price": c, "change_pct": (c - pc) / pc * 100}
    except Exception as e:
        print("us quote error", symbol, e)
    return {"price": 0, "change_pct": 0}

def color(pct):
    if pct > 0: return "#e53935"
    if pct < 0: return "#1565c0"
    return "#555"

def sign(pct):
    if pct >= 0: return "+" + "{:.2f}".format(pct) + "%"
    return "{:.2f}".format(pct) + "%"

def fmt_kr(p):
    return "{:,.0f}".format(p) + "원"

def fmt_us(p):
    return "$" + "{:,.2f}".format(p)

def fmt_amt(a):
    if a >= 0: return "+" + "{:,.0f}".format(a)
    return "{:,.0f}".format(a)

def holding_rows_kr(items):
    rows = ""
    for h in items:
        q = get_kr_quote(h["code"])
        p = q["price"]
        cp = q["change_pct"]
        if not p:
            rows += "<tr><td>" + h["name"] + "</td><td colspan='4' style='color:#aaa;text-align:center'>데이터 없음</td></tr>\n"
            continue
        pnl_pct = (p - h["avg"]) / h["avg"] * 100
        pnl_amt = (p - h["avg"]) * h["shares"]
        rows += "<tr>"
        rows += "<td>" + h["name"] + "</td>"
        rows += "<td style='text-align:right'>" + fmt_kr(p) + "</td>"
        rows += "<td style='text-align:right;color:" + color(cp) + ";font-weight:600'>" + sign(cp) + "</td>"
        rows += "<td style='text-align:right;color:" + color(pnl_pct) + ";font-weight:600'>" + sign(pnl_pct) + "</td>"
        rows += "<td style='text-align:right;color:" + color(pnl_amt) + "'>" + fmt_amt(pnl_amt) + "</td>"
        rows += "</tr>\n"
    return rows

def holding_rows_us(items):
    rows = ""
    for h in items:
        q = get_us_quote(h["symbol"])
        p = q["price"]
        cp = q["change_pct"]
        if not p:
            rows += "<tr><td>" + h["name"] + "</td><td colspan='4' style='color:#aaa;text-align:center'>데이터 없음</td></tr>\n"
            continue
        pnl_pct = (p - h["avg"]) / h["avg"] * 100
        pnl_amt = (p - h["avg"]) * h["shares"]
        rows += "<tr>"
        rows += "<td>" + h["name"] + "</td>"
        rows += "<td style='text-align:right'>" + fmt_us(p) + "</td>"
        rows += "<td style='text-align:right;color:" + color(cp) + ";font-weight:600'>" + sign(cp) + "</td>"
        rows += "<td style='text-align:right;color:" + color(pnl_pct) + ";font-weight:600'>" + sign(pnl_pct) + "</td>"
        rows += "<td style='text-align:right;color:" + color(pnl_amt) + "'>" + fmt_amt(pnl_amt) + "</td>"
        rows += "</tr>\n"
    return rows

def watch_rows(items):
    rows = ""
    for w in items:
        if w["market"] == "KR":
            q = get_kr_quote(w["code"])
            price_str = fmt_kr(q["price"]) if q["price"] else ""
        else:
            q = get_us_quote(w["symbol"])
            price_str = fmt_us(q["price"]) if q["price"] else ""
        if not q["price"]:
            rows += "<tr><td>" + w["name"] + "</td><td colspan='2' style='color:#aaa;text-align:center'>데이터 없음</td></tr>\n"
            continue
        rows += "<tr>"
        rows += "<td>" + w["name"] + "</td>"
        rows += "<td style='text-align:right'>" + price_str + "</td>"
        rows += "<td style='text-align:right;color:" + color(q["change_pct"]) + ";font-weight:600'>" + sign(q["change_pct"]) + "</td>"
        rows += "</tr>\n"
    return rows

def make_html():
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
    .footer { text-align: center; font-size: 11px; color: #aaa;
              margin-top: 16px; padding-bottom: 24px; }
    """

    html = "<!DOCTYPE html>\n<html lang='ko'>\n<head>\n"
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
    html += holding_rows_kr(HOLDINGS_KR)
    html += "</table></div>\n"

    html += "<div class='card'>"
    html += "<h2>🌍 해외 보유주식</h2>"
    html += "<table><tr><th>종목</th><th>현재가</th><th>등락률</th><th>수익률</th><th>손익($)</th></tr>"
    html += holding_rows_us(HOLDINGS_US)
    html += "</table></div>\n"

    html += "<div class='card'>"
    html += "<h2>👀 관심종목</h2>"
    html += "<table><tr><th>종목</th><th>현재가</th><th>등락률</th></tr>"
    html += watch_rows(WATCHLIST)
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
    html = make_html()
    with open("docs/" + DATE_STR + ".html", "w", encoding="utf-8") as f:
        f.write(html)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("완료: docs/" + DATE_STR + ".html")
