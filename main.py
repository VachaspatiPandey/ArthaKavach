import feedparser
import requests
from google import genai
from datetime import datetime, timezone, timedelta
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GEMINI_KEY = os.environ["GEMINI_KEY"]

IST = timezone(timedelta(hours=5, minutes=30))

feeds = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
]

def get_ist_time():
    return datetime.now(IST)

def get_news():
    headlines = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            headlines.append(entry.title)
    return headlines[:25]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def send_greeting(now):
    client = genai.Client(api_key=GEMINI_KEY)
    days = ["Somwar", "Mangalwar", "Budhwar", "Guruwar", "Shukrawar", "Shaniwar", "Raviwar"]
    day_name = days[now.weekday()]
    date_str = now.strftime("%d %B %Y")
    time_str = now.strftime("%I:%M %p")
    prompt = f"""Aaj ki date: {date_str}
Din: {day_name}
Samay: {time_str} IST

Tu VachaspatiPandey ji ki AI secretary hai — loyal, sanskari, business-focused.
Unke liye ek daily morning briefing likh.

Rules:
- "🙏 Namaskar Pandey Ji!" se shuru kar
- Phir aaj ka {day_name}, {date_str} naturally mention kar
- Ek powerful quote — Chanakya, Gita, ya Sanskrit shlok — artha ya karma se related — original quote bhi likh
- Phir bata ki ArthaKavach aaj Reuters, Economic Times aur BBC scan kar raha hai
- Tone: devoted secretary — professional warmth, bilkul robotic nahi
- Pure Hindi mein likh
- 5-6 lines max — punchy aur powerful
- Har din alag lagni chahiye"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    send_telegram(response.text)

def get_nifty_close():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1d&range=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        meta = data["chart"]["result"][0]["meta"]
        price = meta["regularMarketPrice"]
        prev = meta["chartPreviousClose"]
        change = price - prev
        pct = (change / prev) * 100
        sign = "+" if change >= 0 else ""
        return price, change, pct, sign
    except:
        return None, None, None, None

def send_closing_report(now):
    if now.weekday() >= 5:
        return
    price, change, pct, sign = get_nifty_close()
    if price is None:
        return
    msg = f"""📊 <b>ArthaKavach — Market Close Report</b>

🏦 <b>NIFTY 50:</b> {price:,.2f} pts
📈 <b>Change:</b> {sign}{change:.2f} ({sign}{pct:.2f}%)

Kal phir milenge Pandey Ji! 🙏"""
    send_telegram(msg)

def check_impact(headlines):
    client = genai.Client(api_key=GEMINI_KEY)
    text = "\n".join(headlines)
    prompt = f"""You are a financial analyst for Indian markets.
Check if ANY headline could significantly impact Nifty 50 right now.
Consider: war, geopolitical crisis, sanctions, RBI/Fed surprise action, global market crash.
Ignore: routine business news, minor updates.

Headlines:
{text}

Reply in this exact format only:
IMPACT: YES or NO
REASON: one line explanation
HEADLINE: the specific headline (if YES)"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def main():
    now = get_ist_time()

    if now.hour == 8 and now.minute >= 30:
        send_greeting(now)
        return

    if now.hour == 16 and now.minute >= 15:
        send_closing_report(now)
        return

    headlines = get_news()
    if not headlines:
        return
    result = check_impact(headlines)
    if "IMPACT: YES" in result:
        reason = ""
        headline = ""
        for line in result.strip().split("\n"):
            if line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()
            if line.startswith("HEADLINE:"):
                headline = line.replace("HEADLINE:", "").strip()
        msg = f"🔴 <b>ArthaKavach Alert</b>\n\n<b>News:</b> {headline}\n<b>Impact:</b> {reason}\n\n⚡ Check your Nifty positions!"
        send_telegram(msg)

main()
