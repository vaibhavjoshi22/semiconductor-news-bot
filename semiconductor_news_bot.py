import os
import requests
import feedparser
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# ENV VARIABLES
# ─────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# ─────────────────────────────────────────────────────────────
# RSS FEEDS
# ─────────────────────────────────────────────────────────────

RSS_FEEDS = [
    "https://www.semiconductor-today.com/rss.xml",
    "https://www.eetimes.com/rss/",
    "https://techcrunch.com/tag/semiconductors/feed/",
]

KEYWORDS = [
    "semiconductor",
    "chip",
    "tsmc",
    "nvidia",
    "intel",
    "amd",
    "gpu",
    "cpu",
    "ai chip",
    "foundry",
    "wafer",
]

# ─────────────────────────────────────────────────────────────
# FETCH NEWS
# ─────────────────────────────────────────────────────────────

def fetch_news():
    articles = []

    for feed_url in RSS_FEEDS:
        try:
            print(f"Fetching: {feed_url}")

            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:10]:

                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")

                text = f"{title} {summary}".lower()

                if any(keyword in text for keyword in KEYWORDS):
                    articles.append({
                        "title": title,
                        "summary": summary[:200],
                        "link": link
                    })

        except Exception as e:
            print(f"RSS Error: {e}")

    # Remove duplicate titles
    unique_articles = []
    seen = set()

    for article in articles:
        if article["title"] not in seen:
            seen.add(article["title"])
            unique_articles.append(article)

    return unique_articles[:8]

# ─────────────────────────────────────────────────────────────
# CLAUDE SUMMARY
# ─────────────────────────────────────────────────────────────

def summarize_with_claude(articles):

    if not articles:
        return "❌ No semiconductor news found today."

    articles_text = "\n\n".join([
        f"Title: {a['title']}\nSummary: {a['summary']}\nLink: {a['link']}"
        for a in articles
    ])

    prompt = f"""
You are a semiconductor industry analyst.

Here are today's semiconductor news articles:

{articles_text}

Create a concise Telegram news digest.

Rules:
- Start with today's date
- Give 4-6 bullet point summaries
- Keep simple language
- Add emojis
- Keep under 3000 characters
"""

    try:

        response = requests.post(
            "https://api.anthropic.com/v1/messages",

            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },

            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },

            timeout=30
        )

        data = response.json()

        print("Anthropic Response:", data)

        if "content" in data:
            return data["content"][0]["text"]

        return f"❌ Claude API Error:\n{data}"

    except requests.exceptions.Timeout:
        return "❌ Claude API timeout."

    except Exception as e:
        return f"❌ Claude API Exception: {e}"

# ─────────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────────

def send_telegram_message(text):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=20
        )

        print("Telegram Response:", response.text)

        if response.status_code == 200:
            print("✅ Telegram message sent successfully!")

        else:
            print("❌ Telegram Error:", response.text)

    except Exception as e:
        print("❌ Telegram Exception:", e)

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():

    print(f"🔍 Fetching semiconductor news — {datetime.now()}")

    articles = fetch_news()

    print(f"📰 Found {len(articles)} articles")

    print("🤖 Generating Claude summary...")

    digest = summarize_with_claude(articles)

    print("📱 Sending Telegram message...")

    send_telegram_message(digest)

# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
