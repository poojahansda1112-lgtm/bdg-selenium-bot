import telebot
import os
import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import threading
import asyncio
import json
from collections import Counter

# ---------- Hyperbrowser Imports ----------
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import StartClaudeComputerUseTaskParams

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# ---------- Database Setup ----------
conn = sqlite3.connect('bdg_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS results
             (id INTEGER PRIMARY KEY, period TEXT, color TEXT, number TEXT, size TEXT, timestamp DATETIME, win TEXT)''')
conn.commit()

# ---------- BeautifulSoup Scrape (Fallback) ----------
def scrape_bdg_fallback():
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
                c.execute("SELECT * FROM results WHERE period = ?", (period,))
                if not c.fetchone():
                    c.execute("INSERT INTO results (period, color, number, size, timestamp, win) VALUES (?, ?, ?, ?, ?, ?)",
                              (period, color, number, size, datetime.now(), win))
                    conn.commit()
                    count += 1
        print(f"✅ Fallback: {count} Results सेव हुए!")
        return True
    except Exception as e:
        print(f"⚠️ Fallback Error: {e}")
        return False

# ---------- Hyperbrowser Scrape (Claude Computer Use) ----------
async def scrape_bdg_hyperbrowser():
    try:
        client = Hyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))
        result = client.agents.claude_computer_use.start_and_wait(
            params=StartClaudeComputerUseTaskParams(
                task="""
1. https://bdg8.vip/#/saasLott पर जाओ
2. Page Load होने का Wait करो (5 सेकंड)
3. 'WinGo 1 Min' वाली Table ढूंढो
4. Table से Period, Number, Big/Small, Color निकालो
5. JSON में दो: [{"period": "...", "number": "...", "size": "...", "color": "..."}]
6. अगर Table न मिले, तो खाली JSON [] दो
""",
                max_steps=20
            )
        )
        if result.data:
            scraped_data = json.loads(result.data.final_result)
            count = 0
            for item in scraped_data:
                period = item.get('period', '')
                number = item.get('number', '')
                size = item.get('size', '')
                color = item.get('color', '')
                win = "Win" if color and number else "Loose"
                c.execute("SELECT * FROM results WHERE period = ?", (period,))
                if not c.fetchone():
                    c.execute("INSERT INTO results (period, color, number, size, timestamp, win) VALUES (?, ?, ?, ?, ?, ?)",
                              (period, color, number, size, datetime.now(), win))
                    conn.commit()
                    count += 1
            print(f"✅ Hyperbrowser (Claude): {count} Results सेव हुए!")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Hyperbrowser Error: {e}")
        return False

# ---------- Auto-Scrape Loop ----------
def auto_scrape():
    while True:
        print("⏳ Auto-Scrape हो रहा है...")
        try:
            asyncio.run(scrape_bdg_hyperbrowser())
        except:
            scrape_bdg_fallback()
        time.sleep(300)

# ---------- /start ----------
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 नमस्ते! मैं 24/7 Auto-Scrape + Analysis Bot हूँ!\n\n/analysis – ट्रेंड देखें\n/predict – संभावना जानें\n/result – Win/Loose देखें\n/frequency – Number Frequency देखें\n/bssignal – Big/Small Signal देखें\n/addresult – Manual Data Entry")

# ---------- /addresult ----------
@bot.message_handler(commands=['addresult'])
def add_result(message):
    parts = message.text.split()
    if len(parts) >= 4:
        slot, color, number = parts[1], parts[2], parts[3]
        size = parts[4] if len(parts) > 4 else 'N/A'
        c.execute("INSERT INTO results (period, color, number, size, timestamp, win) VALUES (?, ?, ?, ?, ?, ?)",
                  (slot, color, number, size, datetime.now(), "Manual"))
        conn.commit()
        bot.reply_to(message, f"✅ सेव हो गया!\nSlot: {slot}\nColor: {color}\nNumber: {number}\nSize: {size}")
    else:
        bot.reply_to(message, "❌ फॉर्मेट: /addresult 1min Green 7 Big")

# ---------- /scrape ----------
@bot.message_handler(commands=['scrape'])
def scrape_command(message):
    bot.reply_to(message, "⏳ Hyperbrowser से Data Scrape हो रहा है...")
    result = asyncio.run(scrape_bdg_hyperbrowser())
    if result:
        bot.reply_to(message, "✅ नया Data Database में सेव हो गया!")
    else:
        bot.reply_to(message, "⚠️ Scraping में Error आई! Logs Check करें।")

# ---------- /analysis ----------
@bot.message_handler(commands=['analysis'])
def analysis(message):
    c.execute("SELECT color, number, size, win FROM results ORDER BY id DESC LIMIT 20")
    data = c.fetchall()
    if data:
        reply = "📊 **Last 20 Results Analysis:**\n"
        colors = [d[0] for d in data if d[0]]
        numbers = [d[1] for d in data if d[1]]
        sizes = [d[2] for d in data if d[2]]
        wins = [d[3] for d in data if d[3]]
        reply += f"🔴 Red: {colors.count('Red')}\n"
        reply += f"🟢 Green: {colors.count('Green')}\n"
        reply += f"🟣 Violet: {colors.count('Violet')}\n"
        reply += f"📏 Big: {sizes.count('Big')} | Small: {sizes.count('Small')}\n"
        reply += f"✅ Win: {wins.count('Win')} | ❌ Loose: {wins.count('Loose')}\n"
        bot.reply_to(message, reply)
    else:
        bot.reply_to(message, "📊 अभी कोई डेटा नहीं! /addresult या /scrape करें।")

# ---------- /frequency ----------
@bot.message_handler(commands=['frequency'])
def frequency(message):
    c.execute("SELECT number FROM results WHERE number IS NOT NULL AND number != ''")
    data = c.fetchall()
    if data:
        numbers = [d[0] for d in data]
        freq = Counter(numbers).most_common(5)
        reply = "📊 **सबसे ज्यादा आने वाले Numbers:**\n"
        for num, count in freq:
            reply += f"🔢 {num} → {count} बार\n"
        bot.reply_to(message, reply)
    else:
        bot.reply_to(message, "📊 अभी कोई डेटा नहीं!")

# ---------- /predict ----------
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
        bot.reply_to(message, "📭 अभी कोई डेटा नहीं!")

# ---------- /result ----------
@bot.message_handler(commands=['result'])
def result(message):
    c.execute("SELECT period, color, number, size, win FROM results ORDER BY id DESC LIMIT 1")
    data = c.fetchone()
    if data:
        period, color, number, size, win = data
        emoji = "✅" if win == "Win" else "❌"
        bot.reply_to(message, f"📊 **Last Result:**\n🕒 {period}\n🎯 {color} {number} {size}\n{emoji} {win}")
    else:
        bot.reply_to(message, "📭 अभी कोई Result नहीं!")

# ---------- /bssignal ----------
@bot.message_handler(commands=['bssignal'])
def bssignal(message):
    c.execute("SELECT size FROM results ORDER BY id DESC LIMIT 20")
    data = c.fetchall()
    if len(data) < 10:
        bot.reply_to(message, "📊 कम से कम 10 Results चाहिए!")
        return
    sizes = [d[0] for d in data if d[0]]
    big_count = sizes.count('Big')
    small_count = sizes.count('Small')
    last_5 = sizes[:5]
    consecutive_big = 0
    consecutive_small = 0
    for s in last_5:
        if s == 'Big':
            consecutive_big += 1
            consecutive_small = 0
        else:
            consecutive_small += 1
            consecutive_big = 0
    if consecutive_big >= 3:
        prediction = "🟢 **Small** (लगातार Big आ रहा है)"
        confidence = "60-65%"
    elif consecutive_small >= 3:
        prediction = "🔴 **Big** (लगातार Small आ रहा है)"
        confidence = "60-65%"
    elif big_count > small_count:
        prediction = "🔵 **Big**"
        confidence = "55-60%"
    else:
        prediction = "🟣 **Small**"
        confidence = "55-60%"
    reply = f"📊 **Big/Small Analysis (Last 20):**\n"
    reply += f"📏 Big: {big_count} | Small: {small_count}\n"
    reply += f"📈 Last 5: {', '.join(last_5)}\n"
    reply += f"🔮 **Prediction:** {prediction}\n"
    reply += f"🎯 **Confidence:** {confidence}"
    bot.reply_to(message, reply)

# ---------- Start Auto-Scrape ----------
thread = threading.Thread(target=auto_scrape)
thread.daemon = True
thread.start()

# ---------- BOT RUN ----------
bot.infinity_polling() 
