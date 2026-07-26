# ============================================
# 📁 FILE: main.py (FINAL HYBRID SETUP)
# 📝 DESCRIPTION: Playwright Login + API Fetch (No Timeout, 24/7)
# ============================================

import os
import json
import logging
import asyncio
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from playwright.async_api import async_playwright

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

# ============================================
# COLOR CODES
# ============================================

COLORS = {"red": "🔴", "green": "🟢", "violet": "🟣"}

# ============================================
# HYBRID BOT CLASS (Login via Browser + Fetch via API)
# ============================================

class HybridBot:
    def __init__(self):
        self.auth_token = None

    async def get_token(self):
        """1. Playwright से लॉगिन करें और Token लें (5 सेकंड में)"""
        print("🌐 Playwright Login Starting...")
        p = await async_playwright().start()
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        page = await browser.new_page()

        USERNAME = os.environ.get("BDG_USERNAME")
        PASSWORD = os.environ.get("BDG_PASSWORD")
        if not USERNAME or not PASSWORD:
            raise Exception("❌ BDG_USERNAME/PASSWORD missing in Environment Variables!")

        # Login Page
        print("🌐 Going to login page...")
        await page.goto("https://bdg1.cc/?pwa=1", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Fill Credentials
        print("📝 Filling username & password...")
        await page.fill("input[type='text']", USERNAME)
        await page.fill("input[type='password']", PASSWORD)

        # Click Login
        print("🖱️ Clicking login button...")
        await page.click("button[type='submit']")
        await page.wait_for_timeout(5000)

        # Extract Token
        print("🔑 Extracting Token...")
        self.auth_token = await page.evaluate("localStorage.getItem('token')")
        
        if not self.auth_token:
            # Fallback: Cookies से Token निकालें
            cookies = await page.context.cookies()
            for c in cookies:
                if 'token' in c['name']:
                    self.auth_token = c['value']
                    break

        await browser.close()
        print(f"✅ Login Success! Token Captured: {self.auth_token[:15]}...")
        return self.auth_token

    def scrape_api(self):
        """2. Token से बिना ब्राउज़र के API Fetch करें"""
        if not self.auth_token:
            return None

        # BDG का असली API एंडपॉइंट (वही जो मोबाइल ऐप इस्तेमाल करता है)
        url = "https://api.bdg1.cc/api/lottery/result/list?gameCode=WinGo_1M&page=1&pageSize=30"
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                # API के नए फॉर्मेट को Handle करें
                if 'data' in data and 'records' in data['data']:
                    records = data['data']['records']
                elif 'data' in data and isinstance(data['data'], list):
                    records = data['data']
                else:
                    records = data.get('list', [])
                return self.parse_data(records)
            else:
                print(f"❌ API Status: {res.status_code}")
                return None
        except Exception as e:
            print(f"❌ API Error: {e}")
            return None

    def parse_data(self, records):
        scraped = []
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
# GLOBAL INSTANCE
# ============================================

bot = HybridBot()

# ============================================
# TELEGRAM HANDLERS
# ============================================

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("📥 Scrape & Fetch", callback_data="fetch")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ]
    await update.message.reply_text(
        "🎯 **BDG Hybrid Bot Setup Complete!**\n\n"
        "✅ Login via Playwright (No Timeout)\n"
        "✅ Fetch via Direct API (Fast & 24/7)\n\n"
        "Use the buttons below to get started:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def fetch_data(update, context):
    msg = await update.message.reply_text("🔄 Logging in and fetching data via API... Please wait.")
    try:
        # Step 1: Playwright Login (Token लें)
        token = await bot.get_token()
        if not token:
            await msg.edit_text("❌ Login Failed! Check your BDG_USERNAME and BDG_PASSWORD.")
            return

        # Step 2: API Fetch (बिना ब्राउज़र के डेटा लें)
        data = bot.scrape_api()
        if not data:
            await msg.edit_text("❌ API Failed to fetch data. Check Token or URL.")
            return

        # Step 3: Data Save करें
        old_data = load_data()
        old_periods = {i['period'] for i in old_data}
        new_count = 0
        for i in data:
            if i['period'] not in old_periods:
                old_data.append(i)
                new_count += 1
        save_data(old_data)

        await msg.edit_text(
            f"✅ **Scraped Successfully!**\n\n"
            f"📊 New Records: {new_count}\n"
            f"📦 Total Records: {len(old_data)}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

async def stats_cmd(update, context):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data found yet. Use /fetch first.")
        return
    
    total = len(data)
    red = sum(1 for i in data if i['color'] == 'red')
    green = sum(1 for i in data if i['color'] == 'green')
    violet = sum(1 for i in data if i['color'] == 'violet')
    
    await update.message.reply_text(
        f"📊 **Statistics**\n\n"
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
# MAIN LOOP (24/7 Auto-Fetch)
# ============================================

async def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not set in Environment Variables!")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fetch", fetch_data))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 Hybrid Bot is running 24/7 on Railway...")

    # 24/7 Background Auto-Fetch (हर 60 सेकंड में)
    async def auto_loop():
        while True:
            try:
                print("🔄 Auto-fetching via Hybrid method...")
                token = await bot.get_token()
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
                            print(f"✅ Auto-fetch added {added} new records. Total: {len(old_data)}")
            except Exception as e:
                print(f"⚠️ Auto-fetch error: {e}")
            await asyncio.sleep(60)  # 60 seconds wait (IP Ban se bachne ke liye)

    # Background task start karein
    asyncio.create_task(auto_loop())

    # Bot polling start karein
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    print("🟢 Bot is now active and listening...")
    try:
        await asyncio.Event().wait()  # Run forever
    finally:
        await app.stop()
        await app.shutdown()

# ============================================
# ENTRY POINT
# ============================================

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
