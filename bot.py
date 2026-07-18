import telebot
import os
import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import threading

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# ---------- Database Setup ----------
conn = sqlite3.connect('bdg_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS results
             (id INTEGER PRIMARY KEY, period TEXT, color TEXT, number TEXT, size TEXT, timestamp DATETIME, win TEXT)''')
conn.commit()

# ---------- Scrape Function ----------
def scrape_bdg_data():
    try:
        url = "https://bdg8.vip/#/saasLott"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr')
        count = 0
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                period = cols[0].text.strip()
                number = cols[1].text.strip()
                size = cols[2].text.strip()
                color = cols[3].text.strip()
                win = "Win" if color and number else "Loose"
                
                # Check if period already exists
                c.execute("SELECT * FROM results WHERE period = ?", (period,))
                if not c.fetchone():
                    c.execute("INSERT INTO results (period, color, number, size, timestamp, win) VALUES (?, ?, ?, ?, ?, ?)",
                              (period, color, number, size, datetime.now(), win))
                    conn.commit()
                    count += 1
        print(f"✅ {count} नए Results सेव हुए!")
        return True
    except Exception as e:
        print(f"⚠️ Scraping Error: {e}")
        return False

# ---------- Auto-Scrape Loop (हर 5 मिनट) ----------
def auto_scrape():
    while True:
        print("⏳ Auto-Scrape हो रहा है...")
        scrape_bdg_data()
        time.sleep(300)  # 5 मिनट

# ---------- Commands ----------
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 नमस्ते! मैं 24/7 Auto-Scrape BDG Wingo 1 Minute Bot हूँ!\n\n/analysis – ट्रेंड देखें\n/predict – संभावना जानें\n/result – Win/Loose देखें")

@bot.message_handler(commands=['analysis'])
def analysis(message):
    c.execute("SELECT period, color, number, size, win FROM results ORDER BY id DESC LIMIT 10")
    data = c.fetchall()
    if data:
        reply = "📊 **Wingo 1 Minute Analysis (Last 10):**\n"
        for period, color, number, size, win in data:
            reply += f"🕒 {period} | {color} {number} {size} | {win}\n"
        bot.reply_to(message, reply)
    else:
        bot.reply_to(message, "📊 अभी कोई डेटा नहीं! Auto-Scrape शुरू हो गया है, कुछ मिनट में Data आ जाएगा.")

@bot.message_handler(commands=['predict'])
def predict(message):
    c.execute("SELECT color, number, size, COUNT(*) FROM results WHERE color IS NOT NULL AND color != '' GROUP BY color, number, size ORDER BY COUNT(*) DESC LIMIT 3")
    data = c.fetchall()
    if data:
        reply = "🔮 **सबसे संभावित Results:**\n"
        for color, number, size, count in data:
            reply += f"🎯 {color} {number} {size} → {count} बार\n"
        bot.reply_to(message, reply)
    else:
        bot.reply_to(message, "📭 अभी कोई डेटा नहीं! Auto-Scrape शुरू हो गया है.")

@bot.message_handler(commands=['result'])
def result(message):
    c.execute("SELECT period, color, number, size, win FROM results ORDER BY id DESC LIMIT 1")
    data = c.fetchone()
    if data:
        period, color, number, size, win = data
        emoji = "✅" if win == "Win" else "❌"
        bot.reply_to(message, f"📊 **Last Result:**\n🕒 Period: {period}\n🎯 {color} {number} {size}\n{emoji} {win}")
    else:
        bot.reply_to(message, "📭 अभी कोई Result नहीं! Auto-Scrape शुरू हो गया है.")

# ---------- Start Auto-Scrape in Background ----------
thread = threading.Thread(target=auto_scrape)
thread.daemon = True
thread.start()

# ---------- BOT RUN ----------
bot.infinity_polling()
