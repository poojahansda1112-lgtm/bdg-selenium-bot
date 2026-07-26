# ============================================
# 📁 FILE: main.py (ULTIMATE COOKIE HIJACK - FINAL MASTER)
# 📝 DESCRIPTION: Playwright Login + Cookie Hijack + API Fetch
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
# ULTIMATE COOKIE HIJACK BOT
# ============================================

class CookieHijackBot:
    def __init__(self):
        self.cookie_string = None

    async def login_and_get_cookies(self):
        print("🌐 Playwright Starting (Cookie Hijack Mode)...")
        p = await async_playwright().start()
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()

        USERNAME = os.environ.get("BDG_USERNAME")
        PASSWORD = os.environ.get("BDG_PASSWORD")
        if not USERNAME or not PASSWORD:
            await browser.close()
            raise Exception("❌ BDG Credentials missing!")

        print("🌐 Going to login page...")
        await page.goto("https://bdg1.cc/?pwa=1", wait_until="networkidle")
        await page.wait_for_timeout(8000)

        # ---------------- Keyboard Login ----------------
        print("⌨️ Activating Keyboard...")
        await page.click("body")
        await page.wait_for_timeout(1000)

        print("⌨️ Typing Username...")
        await page.keyboard.type(USERNAME)
        await page.wait_for_timeout(1000)
        await page.keyboard.press("Tab")
        await page.wait_for_timeout(1000)

        print("⌨️ Typing Password...")
        await page.keyboard.type(PASSWORD)
        await page.wait_for_timeout(1000)

        print("⏳ Pressing Enter...")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(10000)

        # ---------------- COOKIE HIJACK ----------------
        print("🍪 Hijacking Cookies from Browser...")
        cookies = await context.cookies()
        await browser.close()

        if not cookies:
            raise Exception("❌ No cookies found after login!")

        # Convert cookies to a string format for API requests
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        self.cookie_string = cookie_str
        
        print(f"✅ Cookie Hijack Success! {len(cookies)} cookies captured.")
        return self.cookie_string

    def scrape_api(self):
        if not self.cookie_string:
            return None

        url = "https://api.bdg1.cc/api/lottery/result/list?gameCode=WinGo_1M&page=1&pageSize=30"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json",
            "Cookie": self.cookie_string
        }

        try:
            res = requests.get(url, headers=headers)
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
                print(f"❌ API Fetch Status: {res.status_code}")
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

bot = CookieHijackBot()

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("📥 Scrape & Fetch", callback_data="fetch")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ]
    await update.message.reply_text(
        "🎯 **BDG Cookie Hijack Bot Ready!**\n"
        "✅ Login + Cookie Hijack\n"
        "✅ Token-Free API Fetch\n"
        "✅ 100% Working Final Fix",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def fetch_data(update, context):
    msg = await update.message.reply_text("🔄 Logging in via Playwright to hijack cookies...")
    try:
        cookie_str = await bot.login_and_get_cookies()
        if not cookie_str:
            await msg.edit_text("❌ Login Failed! Check Credentials.")
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
            f"✅ **Final Success!**\n"
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

    print("🚀 Cookie Hijack Bot running 24/7...")

    async def auto_loop():
        while True:
            try:
                print("🔄 Auto-fetching via Cookie Hijack...")
                cookie_str = await bot.login_and_get_cookies()
                if cookie_str:
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
                            print(f"✅ Auto added {added} new records.")
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
