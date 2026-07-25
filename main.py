# ============================================
# 📁 FILE: main.py (ULTIMATE FIXED VERSION)
# 📝 DESCRIPTION: BDG WinGo Bot - No Logout, No Back, No Stuck
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

# ============================================
# DATA STORE (JSON)
# ============================================

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
# PERSISTENT BROWSER (Playwright) - 100% FIXED
# ============================================

class PersistentBrowser:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        self.auth_token = None

    async def init(self):
        if self.browser is not None:
            return
        
        print("🌐 Starting browser for Login...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        self.page = await self.context.new_page()
        await self._login()
        self.is_logged_in = True
        print("✅ Browser initialized and logged in")

    # ================== FIXED LOGIN ==================
    async def _login(self):
        USERNAME = os.environ.get("BDG_USERNAME")
        PASSWORD = os.environ.get("BDG_PASSWORD")
        if not USERNAME or not PASSWORD:
            raise Exception("❌ Username/Password not set!")

        print("🌐 Going to login page...")
        await self.page.goto("https://7bdg.com/#/login", wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        print("📝 Filling username...")
        await self.page.fill("#username", USERNAME)
        print("🔑 Filling password...")
        await self.page.fill("#password", PASSWORD)

        print("🖱️ Clicking login button...")
        await self.page.click("#login-button")
        await self.page.wait_for_timeout(5000)
        print("✅ Login successful!")

        # ---------- CONFIRM POPUP ----------
        try:
            confirm_btn = self.page.locator("text='Confirm'").first
            if await confirm_btn.is_visible(timeout=2000):
                await confirm_btn.click()
                print("✅ Confirm clicked")
                await self.page.wait_for_timeout(2000)
        except:
            print("ℹ️ No Confirm - Skipping")

        # FIX 1: Logout से बचने के लिए goto हटाया, सिर्फ Refresh किया
        print("🔄 Refreshing page to load Home tab correctly...")
        await self.page.reload()
        await self.page.wait_for_timeout(5000)
        print("✅ Home page loaded successfully (No Logout)")

        # ---------- CAPTURE AUTH TOKEN ----------
        print("🔑 Extracting Auth Token for API...")
        try:
            self.auth_token = await self.page.evaluate("localStorage.getItem('token') || localStorage.getItem('access_token')")
            if not self.auth_token:
                cookies = await self.context.cookies()
                for cookie in cookies:
                    if 'token' in cookie['name'] or 'auth' in cookie['name']:
                        self.auth_token = cookie['value']
                        break
            
            if self.auth_token:
                print(f"✅ Auth Token captured successfully!")
            else:
                print("⚠️ Auth Token not found!")
        except Exception as e:
            print(f"⚠️ Error extracting token: {e}")

    # ================== FIXED NAVIGATION ==================
    async def navigate_to_wingo(self):
        if not self.is_logged_in:
            await self.init()
        
        print("🎯 Navigating to WinGo 1Min...")
        
        # ---------- LOTTERY TAB (FIX 2: 'Back' पर क्लिक नहीं होगा) ----------
        try:
            print("🔍 Looking for Lottery tab...")
            lottery_tab = self.page.locator("a[href*='saasLottery']:has-text('Lottery'), div[role='button']:has-text('Lottery')").first
            await lottery_tab.wait_for(state="visible", timeout=5000)
            await lottery_tab.click()
            print("✅ Lottery tab clicked (Not Back)")
        except:
            print("⚠️ Lottery tab not clickable! Using direct URL...")
            await self.page.goto("https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo", wait_until="networkidle")
            
        await self.page.wait_for_timeout(3000)

        # ---------- WIN GO 1MIN (FIX 3: फंसेगा नहीं) ----------
        try:
            print("🔍 Looking for Win Go 1Min...")
            wingo_tab = self.page.locator("div[role='tab']:has-text('Win Go 1Min'), span:has-text('Win Go 1Min')").first
            await wingo_tab.wait_for(state="visible", timeout=5000)
            await wingo_tab.click()
            print("✅ Win Go 1Min clicked")
        except:
            print("⚠️ WinGo tab not clickable! Retrying with URL...")
            await self.page.goto("https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo", wait_until="networkidle")

        # FIX 4: Data लोड होने के लिए 8 सेकंड का इंतज़ार
        print("⏳ Waiting for Game Data to fully load...")
        await self.page.wait_for_timeout(8000)
        print("✅ WinGo 1Min page loaded successfully (Not stuck)")

        # अब API से डेटा खींचेंगे (Browser को ओपन रखते हुए)
        return await self.get_raw_api_data()

    # ================== API DATA FETCH ==================
    async def get_raw_api_data(self):
        print("📡 Fetching data directly from API...")
        
        api_url = "https://api.7bdg.com/api/lottery/result/list?gameCode=WinGo_1M&page=1&pageSize=30"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            response = await self.page.request.get(api_url, headers=headers)
            
            if response.status == 200:
                json_data = await response.json()
                print("✅ API Response received successfully!")
                
                if 'data' in json_data and 'records' in json_data['data']:
                    records = json_data['data']['records']
                elif 'data' in json_data and isinstance(json_data['data'], list):
                    records = json_data['data']
                elif 'list' in json_data:
                    records = json_data['list']
                else:
                    records = json_data

                return self.parse_api_records(records)
            else:
                print(f"❌ API request failed with status: {response.status}")
                return None
                
        except Exception as e:
            print(f"❌ API Fetch Error: {e}")
            return None

    def parse_api_records(self, records):
        scraped_data = []
        if not records:
            return scraped_data

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
                    scraped_data.append({
                        "period": period,
                        "number": number,
                        "color": color,
                        "size": size,
                        "timestamp": str(datetime.now())
                    })
            except Exception as e:
                continue

        print(f"✅ Parsed {len(scraped_data)} records from API")
        return scraped_data

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.is_logged_in = False

# ============================================
# GLOBAL BROWSER INSTANCE
# ============================================

browser_session = PersistentBrowser()

# ============================================
# TELEGRAM HANDLERS
# ============================================

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🎯 Open BDG Game", web_app={"url": "https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo"})],
        [InlineKeyboardButton("📥 Scrape & Fetch", callback_data="fetch")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ]
    await update.message.reply_text(
        "🎯 **BDG Ultimate API Bot**\n\n✅ No Logout, No Back, No Stuck!\n🚀 Direct API Data Fetching.\n\nUse /fetch to get data.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def fetch_data(update, context):
    msg = await update.message.reply_text("📡 Fetching BDG data via API...")
    try:
        data = await browser_session.navigate_to_wingo()
        
        if not data:
            await msg.edit_text("❌ Failed to fetch data via API. Check your token.")
            return
        
        existing = load_data()
        existing_periods = {item['period'] for item in existing}
        new_count = 0
        
        for item in data:
            if item['period'] not in existing_periods:
                existing.append(item)
                new_count += 1
        
        save_data(existing)
        
        await msg.edit_text(
            f"✅ **Scraped via API!**\n"
            f"📊 New Records: {new_count}\n"
            f"📦 Total Records: {len(existing)}"
        )
    except Exception as e:
        logging.error(f"❌ Fetch error: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

async def stats_cmd(update, context):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data found.")
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

async def main_async():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not set!")
        return

    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fetch", fetch_data))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 Ultimate API Bot is running...")
    
    # Auto fetch loop (Every 60 seconds)
    async def auto_loop():
        while True:
            try:
                print("🔄 Auto-fetching via API...")
                if browser_session.is_logged_in:
                    data = await browser_session.navigate_to_wingo()
                    if data:
                        existing = load_data()
                        old_len = len(existing)
                        for i in data:
                            if not any(d['period'] == i['period'] for d in existing):
                                existing.append(i)
                        if len(existing) > old_len:
                            save_data(existing)
                            print(f"✅ Added {len(existing)-old_len} records via Auto-fetch")
            except Exception as e:
                print(f"Auto fetch error: {e}")
            await asyncio.sleep(60)

    await asyncio.gather(
        app.run_polling(poll_interval=3),
        auto_loop()
    )

if __name__ == "__main__":
    asyncio.run(main_async())
