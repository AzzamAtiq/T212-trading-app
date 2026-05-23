"""
Trading 212 AI Market Intelligence App — v2.0
FIXED: T212 API auth (Authorization header not basic auth)
NEW:   AI Investment Picks with prediction scores
NEW:   Gemini (free) instead of Anthropic
Run:   python app.py  -> opens http://localhost:5000
"""

import os, json, threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response, stream_with_context
import requests
import google.generativeai as genai
import yfinance as yf

# ══════════════════════════════════════════════
#  CONFIG — fill these in
# ══════════════════════════════════════════════
T212_API_KEY   = os.getenv("T212_API_KEY",   "your Trading 212 API key")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOur API key")
T212_MODE      = os.getenv("T212_MODE",      "live")   # "live" or "demo"
# ══════════════════════════════════════════════

app  = Flask(__name__)
BASE = f"https://{T212_MODE}.trading212.com/api/v0"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    tools="google_search_retrieval"
)

# ── T212 AUTH (FIXED) ─────────────────────────
def t212_get(endpoint, params=None):
    r = requests.get(
        f"{BASE}{endpoint}",
        headers={"Authorization": T212_API_KEY, "Content-Type": "application/json"},
        params=params,
        timeout=15
    )
    r.raise_for_status()
    return r.json()

# ── MARKET DATA VIA YFINANCE ──────────────────
TICKERS = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AMD","PLTR","COIN",
    "SOFI","ARM","INTC","NFLX","UBER","SHOP","SNOW","RBLX","HOOD","GME",
    "AMC","MSTR","SMCI","IONQ","RIVN","LCID","NIO","XPEV","BABA","ORCL",
    "JPM","BAC","GS","MS","C","WFC","V","MA","PYPL","SQ",
    "XOM","CVX","SLB","OXY","COP","BP","EOG","HAL","MRO","PXD",
    "JNJ","PFE","MRNA","ABBV","UNH","LLY","GILD","BIIB","REGN","CVS"
]

def get_movers():
    try:
        data = yf.download(TICKERS, period="2d", interval="1d",
                           group_by="ticker", auto_adjust=True, progress=False)
        results = []
        for t in TICKERS:
            try:
                df = data[t].dropna()
                if len(df) >= 2:
                    prev = float(df["Close"].iloc[-2])
                    curr = float(df["Close"].iloc[-1])
                    vol  = float(df["Volume"].iloc[-1])
                    chg  = (curr - prev) / prev * 100
                    results.append({"ticker": t, "price": round(curr,2),
                                    "change": round(chg,2), "volume": int(vol)})
            except Exception:
                pass
        return sorted(results, key=lambda x: x["change"], reverse=True)
    except Exception:
        return []

# ── FLASK ROUTES ──────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def status():
    try:
        s = t212_get("/equity/account/summary")
        c = t212_get("/equity/account/cash")
        return jsonify({
            "connected": True, "mode": T212_MODE,
            "totalValue": s.get("totalValue", 0),
            "currency": s.get("currency", "GBP"),
            "available": c.get("availableToTrade", 0),
            "unrealised": s.get("investments", {}).get("unrealizedProfitLoss", 0)
        })
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})

@app.route("/api/portfolio")
def portfolio():
    try:
        return jsonify({
            "positions": t212_get("/equity/portfolio"),
            "summary":   t212_get("/equity/account/summary"),
            "cash":      t212_get("/equity/account/cash")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/market_movers")
def market_movers():
    data = get_movers()
    return jsonify({
        "winners": [x for x in data if x["change"] > 0][:10],
        "losers":  sorted([x for x in data if x["change"] < 0], key=lambda x: x["change"])[:10],
        "spikes":  [x for x in data if x["change"] > 5],
        "crashes": [x for x in data if x["change"] < -5],
        "updated": datetime.now().strftime("%H:%M:%S")
    })

@app.route("/api/ai_scan", methods=["POST"])
def ai_scan():
    body     = request.json or {}
    stype    = body.get("type", "full")
    market   = body.get("market", "All")
    question = body.get("question", "")
    portfolio_ctx = body.get("portfolio", "")
    today    = datetime.now().strftime("%A %B %d %Y")
    mkt      = f"the {market} market" if market != "All" else "all major markets (US, UK, EU)"

    PROMPTS = {

"winners": f"""Search Google now. Find the TOP 10 STOCK GAINERS today ({today}) in {mkt}.
For each: ticker, price, % gain, WHY it is up, buy now or wait verdict.
Use ▲ symbols. Format as a clear ranked list. End with market sentiment summary.""",

"losers": f"""Search Google now. Find the TOP 10 STOCK LOSERS today ({today}) in {mkt}.
For each: ticker, price, % loss, WHY it is falling, buying dip or avoid verdict.
Use ▼ symbols. Format as a clear ranked list.""",

"spikes": f"""Search Google now. Find stocks with SUDDEN UNEXPECTED SPIKES today ({today}) in {mkt}.
Unusual surges — short squeeze, FDA news, earnings beat, acquisition rumour.
For each: ticker, spike %, cause, hold or reverse, risk level.""",

"crashes": f"""Search Google now. Find stocks in SUDDEN FREEFALL today ({today}) in {mkt}.
Unexpected drops — scandal, earnings miss, downgrade, CEO news.
For each: ticker, crash %, cause, recovery chance, danger level.""",

"sectors": f"""Search Google now. SECTOR PERFORMANCE today ({today}) in {mkt}.
Sectors: Tech, Energy, Finance, Healthcare, Consumer, Industrials, Real Estate, Utilities, Materials, Crypto.
For each: % today, top stock, one-line reason.
End: Which 2 sectors are best to trade this week?""",

"full": f"""Search Google now. COMPLETE MARKET REPORT for today ({today}) in {mkt}.
1. MARKET MOOD (Bullish/Bearish/Mixed + reason)
2. TOP 5 WINNERS (ticker, % gain, reason)
3. TOP 5 LOSERS (ticker, % loss, reason)
4. SUDDEN SPIKES today
5. SUDDEN CRASHES today
6. SECTOR HEATMAP (quick rundown)
7. TOP 3 NEWS STORIES driving the market
8. ONE TRADE IDEA for today with full reasoning""",

"picks": f"""You are an elite stock trading analyst. Search Google for live data right now ({today}).

TASK: Scan all top movers today and give me the BEST AI INVESTMENT PICKS.

Step 1 — Search for top 15 gainers AND top 15 losers today in {mkt}
Step 2 — Analyse each one (news catalyst, momentum, volume, risk)
Step 3 — Pick the BEST 5 STOCKS TO INVEST IN RIGHT NOW from all of them

═══════════════════════════════════
For EACH of the 5 picks, use this exact format:

🏆 RANK #[N] — [COMPANY NAME] ([TICKER])
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action        : ✅ BUY NOW / ⏳ WAIT FOR DIP
Current Price : $XX.XX
Today's Move  : ▲/▼ X.XX%
5-Day Target  : $XX.XX (+X% to +X%)
AI Score      : [X]/10 ⭐
Confidence    : 🟢 HIGH / 🟡 MEDIUM / 🔴 LOW
Catalyst      : [what is driving it right now]
Key Risk      : [biggest risk to this trade]
Entry Point   : [ideal price to buy]
Stop Loss     : [where to cut losses]
Verdict       : [2 clear sentences — should they invest or not]
═══════════════════════════════════

After all 5 picks also give:

⛔ TOP STOCK TO AVOID TODAY:
[ticker] — [reason in 2 sentences]

📊 OVERALL MARKET SCORE: [X]/10
⏰ BEST TIME TO ENTER TODAY: [market open / mid-day / close / avoid today]
💡 ONE KEY INSIGHT: [most important thing to know right now]

Be direct, specific, use real live prices. No vague language.""",

"portfolio_analysis": f"""Search Google now. Analyse this Trading 212 portfolio for today ({today}):

{portfolio_ctx}

Give:
1. Portfolio health score (0-10)
2. Best performer today and why
3. Worst performer today and why
4. Any urgent alerts (spikes or crashes in their holdings)
5. ONE clear action to take today
6. Risk assessment""",

"custom": f"""Search Google now. Today is {today}, market: {mkt}.
{question}
Be specific. Use real tickers. Include prices and % changes where relevant."""
    }

    prompt = PROMPTS.get(stype, PROMPTS["full"])

    def generate():
        try:
            resp = model.generate_content(prompt, stream=True)
            for chunk in resp:
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'text': f'\\n\\nError: {str(e)}'})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    import webbrowser
    print("\n" + "="*54)
    print("  Trading 212 AI Market Intelligence  v2.0")
    print(f"  Mode  : {T212_MODE.upper()}")
    print("  URL   : http://localhost:5000")
    print("="*54 + "\n")
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, port=5000, threaded=True)
