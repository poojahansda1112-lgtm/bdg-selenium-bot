import telebot
import os
import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# ---------- Database Setup ----------
conn = sqlite3.connect('bdg_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS results
             (id INTEGER PRIMARY KEY, slot TEXT, color TEXT, number TEXT, size TEXT, timestamp DATETIME)''')
conn.commit()

# ---------- BeautifulSoup Scraping ----------
def scrape_bdg_data():
    try:
        url = "https://bdg8.vip/#/saasLott"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ⚠️ Inspect करके सही Class Name डालें
        elements = soup.find_all('div', class_='game-result')
        
        for el in elements:
            color = el.find('span', class_='color').text.strip()
            number = el.find('span', class_='number').text.strip()
            slot = "1min"
            size = "Big"
            
            c.execute("INSERT INTO results (slot, color, number, size, timestamp) VALUES (?, ?, ?, ?, ?)",
                      (slot, color, number, size, datetime.now()))
            conn.commit()
            print(f"✅ सेव हुआ: {slot} {color} {number} {size}")
        
        return True
    except Exception as e:
        print(f"⚠️ Scraping Error: {e}")
        return False

# ---------- Commands ----------
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 नमस्ते! मैं 24/7 BDG Analysis बॉट हूँ!\n\n/scrape – Data Scrape करें\n/addresult – डेटा डालें\n/analysis – ट्रेंड देखें\n/predict – संभावना जानें")

@bot.message_handler(commands=['scrape'])
def scrape_command(message):
    bot.reply_to(message, "⏳ BDG Data Scrape हो रहा है...")
    result = scrape_bdg_data()
    if result:
        bot.reply_to(message, "✅ नया Data Database में सेव हो गया!")
    else:
        bot.reply_to(message, "⚠️ Scraping में Error आई! Logs Check करें।")

# ---------- /addresult ----------
@bot.message_handler(commands=['addresult'])
def add_result(message):
    parts = message.text.split()
    if len(parts) >= 4:
        slot, color, number = parts[1], parts[2], parts[3]
        size = parts[4] if len(parts) > 4 else 'N/A'
        c.execute("INSERT INTO results (slot, color, number, size, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (slot, color, number, size, datetime.now()))
        conn.commit()
        bot.reply_to(message, f"✅ सेव हो गया!\nSlot: {slot}\nColor: {color}\nNumber: {number}\nSize: {size}")
    else:
        bot.reply_to(message, "❌ फॉर्मेट: /addresult 1min Green 7 Big")

# ---------- /analysis ----------
@bot.message_handler(commands=['analysis'])
def analysis(message):
    c.execute("SELECT color, COUNT(*) FROM results GROUP BY color")
    data = c.fetchall()
    if not data:
        bot.reply_to(message, "📊 अभी कोई डेटा नहीं! पहले /addresult से डेटा डालें।")
        return
    total = sum(count for _, count in data)
    reply = "📊 **Real Analysis Report**\n"
    for color, count in data:
        reply += f"{color}: {count} ({count/total*100:.1f}%)\n"
    reply += f"\n📌 Total Results: {total}"
    bot.reply_to(message, reply)

# ---------- /predict ----------
@bot.message_handler(commands=['predict'])
def predict(message):
    c.execute("SELECT color, COUNT(*) FROM results GROUP BY color ORDER BY COUNT(*) DESC LIMIT 1")
    result = c.fetchone()
    if result:
        bot.reply_to(message, f"🔮 सबसे संभावित रंग: {result[0]} (पिछले डेटा के आधार पर)")
    else:
        bot.reply_to(message, "📭 अभी कोई डेटा नहीं! पहले /addresult से डेटा डालें।")

# ---------- BOT RUN ----------
bot.infinity_polling()
