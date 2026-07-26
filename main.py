# ============================================
# 📁 FILE: main.py (DIRECT API LOGIN - FINAL FIX)
# 📝 DESCRIPTION: Pure Requests API Login (No Playwright)
# ============================================

import os
import json
import logging
import asyncio
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# ============================================
# LOGGING & DATA SETUP
# ============================================

logging.basicConfig(level=logging.INFO)
DATA_FILE = "bdg_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

COLORS = {"red": "🔴", "green": "🟢", "violet": "🟣"}

# ============================================
# DIRECT API BOT CLASS (No Playwright)
# ============================================

class APIBot:
    def __init__(self):
        self.auth_token = None
        self.session = requests.Session()

    def login(self):
        print("🌐 Direct API Login Starting...")
        USERNAME = os.environ.get("BDG_USERNAME")
        PASSWORD = os.environ.get("BDG_PASSWORD")
        if not USERNAME or not PASSWORD:
            raise Exception("❌ BDG Credentials missing!")

        # BDG Game ka Login API URL
        login_url = "https://api.bdg1.cc/api/login"
        
        payload = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Origin": "https://bdg1.cc",
            "Referer": "https://bdg1.cc/"
        }

        try:
            print("📡 Sending Login Request...")
            response = self.session.post(login_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Token ka naya format check karein
                if 'token' in data:
                    self.auth_token = data['token']
                elif 'data' in data and 'token' in data['data']:
                    self.auth_token = data['data']['token']
                elif 'access_token' in data:
                    self.auth_token = data['access_token']
                else:
                    # Aakhri koshish: Agar JSON format ulat-put hai
                    self.auth_token = data.get('auth_token') or data.get('token_key')

                if self.auth_token:
                    print(f"✅ Direct API Login Success! Token Captured.")
                    return self.auth_token
                else:
                    raise Exception("Token not found in JSON response.")
            else:
                print(f"❌ Login Failed. Status: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ API Login Error: {e}")
            return None

    def scrape_api(self):
        if not self.auth_token:
            return None

        url = "https://api.bdg1.cc/api/lottery/result/list?gameCode=WinGo_1M&page=1&pageSize=30"
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json"
        }

        try:
            res = self.session.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                records = []
                if 'data' in data and 'records' in data['data']:
                    records = data['data']['records']
                elif 'data' in data and isinstance(data['data'], list):
                    records = data['data']
                else:
                    records = data.get('list', [])
                return self.parse_data(records)
            else:
                print(f"❌ API Fetch Failed. Status: {res.status_code}")
                return None
        except Exception as e:
            print(f"❌ API Error: {e}")
            return None

    def parse_data(self, records):
        scraped = []
        if not records:
            return scraped

        for item in records:
            try:
                period = str(item.get('issueNumber', item.get('issue', item.get('period', ''))))
                number = int(item.get('number', item.get('num', 0)))
                
                raw_color = item.get('color', '').lower()
                color = "unknown"
                if "green" in raw_color: color = "green"
                elif "red" in raw_color: color = "red"
                elif "violet" in raw_color or "purple" in raw_color: color = "violet"

                raw_size = item.get('size', '').lower()
                size = "unknown"
                if "big" in raw_size or "large" in raw_size: size = "big"
                elif "small" in raw_size: size = "small"

                if period and number:
                    scraped.append({
                        "period": period,
                        "number": number,
                        "color": color,
                        "size": size,
                        "timestamp": str(datetime.now())
                    })
            except:
                continue
        return scraped

# ============================================
# GLOBAL INSTANCE & HANDLERS
# ============================================

bot = APIBot()

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("📥 Scrape & Fetch", callback_data="fetch")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ]
    await update.message.reply_text(
        "🎯 **BDG Direct API Bot Ready!**\n"
        "✅ Pure Requests Login (No Playwright)\n"
        "✅ Fast & 100% Token Capture\n"
        "✅ Direct API Fetch (24/7)",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def fetch_data(update, context):
    msg = await update.message.reply_text("🔄 Logging in via Direct API... Please wait.")
    try:
        token = bot.login()
        if not token:
            await msg.edit_text("❌ API Login Failed! Check Credentials or API URL.")
            return

        data = bot.scrape_api()
        if not data:
            await msg.edit_text("❌ API returned empty data.")
            return

        old_data = load_data()
        old_periods = {i['period'] for i in old_data}
        new_count = 0
        for i in data:
            if i['period'] not in old_periods:
                old_data.append(i)
                new_count += 1
        save_data(old_data)

        await msg.edit_text(
            f"✅ **Scraped via Direct API!**\n"
            f"📊 New Records: {new_count}\n"
            f"📦 Total Records: {len(old_data)}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

async def stats_cmd(update, context):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data found yet.")
        return
    total = len(data)
    red = sum(1 for i in data if i['color'] == 'red')
    green = sum(1 for i in data if i['color'] == 'green')
    violet = sum(1 for i in data if i['color'] == 'violet')
    await update.message.reply_text(
        f"📊 **Statistics**\n"
        f"📦 Total: {total}\n"
        f"{COLORS['red']} Red: {red}\n"
        f"{COLORS['green']} Green: {green}\n"
        f"{COLORS['violet']} Violet: {violet}"
    )

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "fetch":
        await fetch_data(update, context)
    elif query.data == "stats":
        await stats_cmd(update, context)

# ============================================
# MAIN LOOP
# ============================================

async def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN missing!")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fetch", fetch_data))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 Direct API Bot running 24/7 on Railway...")

    async def auto_loop():
        while True:
            try:
                print("🔄 Auto-fetching via Direct API...")
                token = bot.login()
                if token:
                    data = bot.scrape_api()
                    if data:
                        old_data = load_data()
                        old_periods = {i['period'] for i in old_data}
                        added = 0
                        for i in data:
                            if i['period'] not in old_periods:
                                old_data.append(i)
                                added += 1
                        if added > 0:
                            save_data(old_data)
                            print(f"✅ Auto-fetch added {added} new records.")
            except Exception as e:
                print(f"⚠️ Auto-fetch error: {e}")
            await asyncio.sleep(60)

    asyncio.create_task(auto_loop())
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    try:
        await asyncio.Event().wait()
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
