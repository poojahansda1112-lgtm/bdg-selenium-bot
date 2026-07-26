# ============================================
# 📁 FILE: main.py (ULTIMATE INPUT FIX)
# 📝 DESCRIPTION: Fixed Username Input Timeout (3 Ways)
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

COLORS = {"red": "🔴", "green": "🟢", "violet": "🟣"}

# ============================================
# HYBRID BOT CLASS (Fixed Input)
# ============================================

class HybridBot:
    def __init__(self):
        self.auth_token = None

    async def get_token(self):
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
            raise Exception("❌ BDG_USERNAME/PASSWORD missing!")

        print("🌐 Going to login page...")
        await page.goto("https://bdg1.cc/?pwa=1", wait_until="networkidle")
        await page.wait_for_timeout(5000)  # पेज को पूरी तरह लोड होने दें (5 सेकंड)

        # ==========================================================
        # 🔥 ULTIMATE INPUT FIX: 3 अलग-अलग तरीकों से यूज़रनेम ढूँढें
        # ==========================================================
        print("🔍 Searching for Username input box...")
        
        # Attempt 1: सबसे आम (Mobile site)
        try:
            await page.wait_for_selector("input[placeholder*='username']", timeout=3000)
            await page.fill("input[placeholder*='username']", USERNAME)
            print("✅ Username filled via Placeholder (Mobile)")
        except:
            # Attempt 2: सीधा टेक्स्ट इनपुट (Desktop fallback)
            try:
                await page.wait_for_selector("input[type='text']", timeout=3000)
                await page.fill("input[type='text']", USERNAME)
                print("✅ Username filled via Type='text'")
            except:
                # Attempt 3: अगर सब कुछ फेल हो, तो पेज का स्क्रीनशॉट लेकर क्रैश होने से बचाएं
                try:
                    # सबसे लास्ट रास्ता: किसी भी इनपुट को खोजें और पहले में डालें
                    await page.fill("input", USERNAME)
                    print("✅ Username filled via Fallback Input")
                except Exception as e:
                    await page.screenshot(path="debug_login.png")
                    raise Exception(f"❌ Username box NOT FOUND! Screenshot saved. Error: {e}")

        # ==========================================================
        # 🔥 ULTIMATE INPUT FIX: पासवर्ड (Password)
        # ==========================================================
        print("🔑 Searching for Password input box...")
        try:
            await page.wait_for_selector("input[placeholder*='password']", timeout=3000)
            await page.fill("input[placeholder*='password']", PASSWORD)
            print("✅ Password filled via Placeholder")
        except:
            try:
                await page.wait_for_selector("input[type='password']", timeout=3000)
                await page.fill("input[type='password']", PASSWORD)
                print("✅ Password filled via Type='password'")
            except:
                # अगर पासवर्ड बॉक्स नहीं मिला, तो पेज रीफ्रेश करके कोशिश करें
                await page.reload()
                await page.wait_for_timeout(3000)
                await page.fill("input[type='password']", PASSWORD)
                print("✅ Password filled after Reload")

        print("🖱️ Clicking login button...")
        try:
            await page.click("button[type='submit']")
        except:
            # Login button अलग हो सकता है
            await page.click("button:has-text('Sign'), button:has-text('Login')")
        
        await page.wait_for_timeout(8000)  # Dashboard लोड होने का इंतज़ार

        # Extract Token
        print("🔑 Extracting Token...")
        self.auth_token = await page.evaluate("localStorage.getItem('token')")
        
        if not self.auth_token:
            cookies = await page.context.cookies()
            for c in cookies:
                if 'token' in c['name']:
                    self.auth_token = c['value']
                    break

        await browser.close()
        print(f"✅ Login Success! Token Captured.")
        return self.auth_token

    def scrape_api(self):
        if not self.auth_token:
            return None

        url = "https://api.bdg1.cc/api/lottery/result/list?gameCode=WinGo_1M&page=1&pageSize=30"
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "User-Agent": "Mozilla/5.0"
        }

        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
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
# GLOBAL INSTANCE & TELEGRAM HANDLERS
# ============================================

bot = HybridBot()

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("📥 Scrape & Fetch", callback_data="fetch")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ]
    await update.message.reply_text(
        "🎯 **BDG Hybrid Bot Setup Complete!**\n\n"
        "✅ Login via Playwright (Ultimate Input Fix)\n"
        "✅ Fetch via Direct API (Fast & 24/7)\n\n"
        "Use the buttons below to get started:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def fetch_data(update, context):
    msg = await update.message.reply_text("🔄 Logging in... Please wait.")
    try:
        token = await bot.get_token()
        if not token:
            await msg.edit_text("❌ Login Failed! Check your BDG_USERNAME and BDG_PASSWORD.")
            return

        data = bot.scrape_api()
        if not data:
            await msg.edit_text("❌ API Failed to fetch data.")
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
            f"✅ **Scraped Successfully!**\n\n"
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
# MAIN LOOP
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
                            print(f"✅ Auto-fetch added {added} new records.")
            except Exception as e:
                print(f"⚠️ Auto-fetch error: {e}")
            await asyncio.sleep(60)

    asyncio.create_task(auto_loop())

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    print("🟢 Bot is now active and listening...")
    try:
        await asyncio.Event().wait()
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
