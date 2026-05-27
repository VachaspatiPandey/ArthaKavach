import feedparser
import requests
from google import genai
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GEMINI_KEY = os.environ["GEMINI_KEY"]

feeds = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
]

def get_news():
    headlines = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            headlines.append(entry.title)
    return headlines[:25]

def check_impact(headlines):
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
    client = genai.Client(api_key=GEMINI_KEY)
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def main():
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
