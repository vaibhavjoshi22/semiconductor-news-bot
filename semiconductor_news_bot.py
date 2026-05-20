import os
import requests
import feedparser
from datetime import datetime

# ─── CONFIG — fill these in ───────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY",  "YOUR_ANTHROPIC_KEY_HERE")
# ─────────────────────────────────────────────────────────────────────────────

# Free RSS feeds for semiconductor news (no API key needed)
RSS_FEEDS = [
    "https://www.semiconductor-today.com/rss.xml",
    "https://feeds.feedburner.com/electronicdesign/news",
    "https://www.eetimes.com/rss/",
    "https://techcrunch.com/tag/semiconductors/feed/",
    "https://www.tomshardware.com/feeds/all",
]

KEYWORDS = [
    "semiconductor", "chip", "tsmc", "nvidia", "intel", "amd",
    "foundry", "wafer", "node", "fab", "soc", "gpu", "cpu", "ai chip",
    "samsung semiconductor", "arm chip", "memory chip"
]


def fetch_news():
    """Fetch latest semiconductor news from RSS feeds."""
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                link = entry.get("link", "")
                # Only include semiconductor-relevant articles
                text_to_check = (title + " " + summary).lower()
                if any(kw in text_to_check for kw in KEYWORDS):
                    articles.append({
                        "title": title,
                        "summary": summary[:300],
                        "link": link
                    })
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
    # Deduplicate by title and take top 8
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:8]


def summarize_with_claude(articles):
    """Use Claude AI to create a clean news digest."""
    if not articles:
        return "No semiconductor news found today."

    articles_text = "\n\n".join([
        f"Title: {a['title']}\nSummary: {a['summary']}\nLink: {a['link']}"
        for a in articles
    ])

    prompt = f"""You are a semiconductor industry analyst. Here are today's semiconductor news articles:

{articles_text}

Create a concise daily digest for a Telegram message. Format it like this:
- Start with a 1-line intro with today's date
- List 4-6 key stories as bullet points (1-2 sentences each, include the link)
- End with a 1-line market insight or trend observation
- Keep total under 3000 characters for Telegram
- Use simple language, no jargon overload
- Add relevant emojis to make it readable"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": ""model": "claude-3-haiku-20240307"",  # cheapest model — perfect for summaries
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    data = response.json()
    return data["content"][0]["text"]


def send_telegram_message(text):
    """Send message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    resp = requests.post(url, json=payload)
    if resp.status_code == 200:
        print("✅ Message sent to Telegram!")
    else:
        print(f"❌ Telegram error: {resp.text}")


def main():
    print(f"🔍 Fetching semiconductor news — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    articles = fetch_news()
    print(f"📰 Found {len(articles)} relevant articles")

    print("🤖 Summarizing with Claude AI...")
    digest = summarize_with_claude(articles)

    print("📱 Sending to Telegram...")
    send_telegram_message(digest)


if __name__ == "__main__":
    main()
