import os
import sqlite3
import requests
import logging
import schedule
import time
from telegram import Bot
from dotenv import load_dotenv

# ---------------- LOAD ENV ----------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

NEWS_CATEGORY = "general"
NEWS_COUNTRY = "tr"
CHECK_INTERVAL = 15  # dakika

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("sent_news.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS sent_news (
    url TEXT PRIMARY KEY
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------
def fetch_news():
    url = f"https://newsapi.org/v2/top-headlines?country={NEWS_COUNTRY}&category={NEWS_CATEGORY}&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") != "ok":
            logging.error(f"NewsAPI error: {data}")
            return []
        return data.get("articles", [])
    except Exception as e:
        logging.error(f"Haber çekme hatası: {e}")
        return []

def send_news():
    bot = Bot(token=TELEGRAM_TOKEN)
    articles = fetch_news()
    if not articles:
        logging.info("Haber bulunamadı.")
        return

    new_count = 0
    for article in articles:
        url = article.get("url")
        title = article.get("title")
        if not url or not title:
            continue

        c.execute("SELECT 1 FROM sent_news WHERE url = ?", (url,))
        if c.fetchone():
            continue  # Haber zaten gönderilmiş

        message = f"📰 <b>{title}</b>\n{url}"
        try:
            bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
            c.execute("INSERT INTO sent_news (url) VALUES (?)", (url,))
            conn.commit()
            new_count += 1
        except Exception as e:
            logging.error(f"Mesaj gönderilemedi: {e}")

    logging.info(f"{new_count} yeni haber gönderildi.")

# ---------------- SCHEDULE ----------------
schedule.every(CHECK_INTERVAL).minutes.do(send_news)

logging.info("Haber botu başlatıldı.")
send_news()  # İlk başlatmada hemen gönder

while True:
    schedule.run_pending()
    time.sleep(3)
