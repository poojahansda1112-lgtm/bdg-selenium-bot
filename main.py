# ============================================
# 📁 FILE: main.py
# 📝 DESCRIPTION: BDG WinGo Scrape Bot + News Bot
# 🔗 GAME: WinGo 1Min (Playwright)
# 📰 NEWS: BBC / Any URL (BeautifulSoup)
# 🆕 NEW: debug_page.html save karega
# ============================================

import os
import json
import logging
import asyncio
import random
import requests
from bs4 import BeautifulSoup
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

COLORS = {"red": "🔴", "green": "🟢", "violet": "🟣", "big": "📈", "small": "📉"}
def get_color_emoji(color):
    return COLORS.get(color.lower(), "⚪")

# ============================================
# PERSISTENT BROWSER SESSION (Playwright)
# ============================================

class PersistentBrowser:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False

    async def init(self):
        if self.browser is not None:
            print("✅ Browser already initialized")
            return
        
        print("🌐 Starting browser...")
        self.playwright = await async_playwright().start()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1280, 'height': 720}
        )
        self.page = await self.context.new_page()
        await self._login()
        self.is_logged_in = True
        print("✅ Browser initialized and logged in")

    async def _login(self):
        USERNAME = os.environ.get("BDG_USERNAME")
        PASSWORD = os.environ.get("BDG_PASSWORD")
        if not USERNAME or not PASSWORD:
            raise Exception("❌ Username/Password not set!")

        print("🌐 Going to login page...")
        await self.page.goto("https://7bdg.com/#/login", timeout=60000)
        await self.page.wait_for_timeout(5000 + random.randint(1000, 3000))

        print("📝 Filling username...")
        username_input = await self.page.query_selector("#username") or await self.page.query_selector("input[type='text']")
        if username_input:
            await username_input.fill(USERNAME)
            print(f"✅ Username filled: {USERNAME}")

        print("🔑 Filling password...")
        password_input = await self.page.query_selector("#password") or await self.page.query_selector("input[type='password']")
        if password_input:
            await password_input.fill(PASSWORD)
            print("✅ Password filled")

        print("🖱️ Clicking login button...")
        login_button = (
            await self.page.query_selector("#login-button") or
            await self.page.query_selector("button[type='submit']") or
            await self.page.query_selector("[class*='login']")
        )
        if login_button:
            await login_button.click()
            print("✅ Login button clicked")
        else:
            raise Exception("⚠️ Login button not found!")

        await self.page.wait_for_timeout(5000 + random.randint(1000, 3000))
        print("✅ Login successful!")

        # Confirm popup (if exists)
        print("🎯 Looking for Confirm button...")
        confirm_clicked = False
        try:
            xpath = "//*[contains(text(),'Confirm') or contains(text(),'confirm')]"
            element = self.page.locator(xpath).first
            if await element.is_visible():
                await element.click()
                confirm_clicked = True
                print("✅ Confirm clicked via XPath")
                await self.page.wait_for_timeout(3000)
        except Exception as e:
            print(f"⚠️ Confirm error (XPath): {e}")

        if not confirm_clicked:
            try:
                element = self.page.locator(":has-text('Confirm')").first
                if await element.is_visible():
                    await element.click()
                    confirm_clicked = True
                    print("✅ Confirm clicked via :has-text")
                    await self.page.wait_for_timeout(3000)
            except Exception as e:
                print(f"⚠️ Confirm error (:has-text): {e}")

        if not confirm_clicked:
            try:
                await self.page.evaluate("""
                    const elements = document.querySelectorAll('*');
                    for (let el of elements) {
                        if (el.textContent.includes('Confirm')) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                """)
                confirm_clicked = True
                print("✅ Confirm clicked via JavaScript")
                await self.page.wait_for_timeout(3000)
            except Exception as e:
                print(f"⚠️ Confirm error (JS): {e}")

        if not confirm_clicked:
            print("ℹ️ No Confirm - Skipping")

        await self.page.goto("https://7bdg.com/#/home", timeout=60000)
        await self.page.wait_for_timeout(3000)
        print("✅ Navigated to home page")

    async def navigate_to_wingo(self):
        if not self.is_logged_in:
            await self.init()
        
        print("🎯 Navigating to WinGo 1Min...")
        
        # ---------- LOTTERY TAB ----------
        print("🎯 Looking for Lottery tab...")
        lottery_clicked = False
        lottery_selectors = [
            "//*[contains(text(),'Lottery')]",
            "//a[contains(text(),'Lottery')]",
            "//span[contains(text(),'Lottery')]",
            "//div[contains(text(),'Lottery')]",
            "//li[contains(text(),'Lottery')]",
            "a:has-text('Lottery')",
            "span:has-text('Lottery')",
            "div:has-text('Lottery')",
            "li:has-text('Lottery')",
            "[class*='lottery']",
            "[class*='Lottery']",
            "button:has-text('Lottery')"
        ]
        for sel in lottery_selectors:
            try:
                if sel.startswith("//"):
                    element = self.page.locator(sel).first
                else:
                    element = await self.page.query_selector(sel)
                if element and await element.is_visible():
                    await element.click()
                    lottery_clicked = True
                    print(f"✅ Lottery clicked via selector: {sel}")
                    break
            except:
                continue
        if not lottery_clicked:
            print("⚠️ Lottery not clickable! Using direct URL...")
            await self.page.goto("https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo", timeout=60000)
            await self.page.wait_for_timeout(3000 + random.randint(500, 1500))
            lottery_clicked = True
        if lottery_clicked:
            await self.page.wait_for_timeout(3000 + random.randint(500, 1500))

        # ---------- WIN GO 1MIN ----------
        print("🎯 Looking for Win Go 1Min...")
        wingo_clicked = False
        wingo_selectors = [
            "//*[contains(text(),'Win Go 1Min')]",
            "//*[contains(text(),'WinGo 1Min')]",
            "//*[contains(text(),'Win Go 1 Min')]",
            "//*[contains(text(),'WinGo 1 Min')]",
            "span:has-text('Win Go 1Min')",
            "div:has-text('Win Go 1Min')",
            "a:has-text('Win Go 1Min')",
            "li:has-text('Win Go 1Min')",
            "[class*='WinGo']"
        ]
        for sel in wingo_selectors:
            try:
                if sel.startswith("//"):
                    element = self.page.locator(sel).first
                else:
                    element = await self.page.query_selector(sel)
                if element and await element.is_visible():
                    await element.click()
                    wingo_clicked = True
                    print(f"✅ Win Go 1Min clicked via selector: {sel}")
                    break
            except:
                continue
        if not wingo_clicked:
            print("⚠️ Win Go 1Min not clickable! Using direct URL...")
            await self.page.goto("https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo", timeout=60000)
            await self.page.wait_for_timeout(5000 + random.randint(1000, 3000))
            wingo_clicked = True
        if wingo_clicked:
            await self.page.wait_for_timeout(5000 + random.randint(1000, 3000))

        # ---------- WAIT + SCROLL ----------
        print("⏳ Waiting for page to fully load...")
        await self.page.wait_for_timeout(8000)
        print("📜 Scrolling down...")
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.page.wait_for_timeout(5000)

        # Wait for table
        try:
            await self.page.wait_for_selector("table", timeout=30000)
            print("✅ Table appeared after wait")
        except:
            print("⚠️ Table did not appear within 30 seconds")

        # ---------- TABLE SCRAPE ----------
        print("📊 Looking for table...")
        table_selectors = [
            "table",
            "table tbody",
            ".game-history table",
            ".history-table",
            "[class*='history'] table",
            "div[class*='table']",
            ".ant-table",
            ".MuiTable-root",
            "div[class*='game-history']",
            "div[role='table']"
        ]
        table = None
        for sel in table_selectors:
            try:
                table = await self.page.query_selector(sel)
                if table:
                    print(f"✅ Table found with selector: {sel}")
                    break
            except:
                continue

        if not table:
            print("❌ Table not found!")
            # 🔍 DEBUG: Screenshot + HTML save
            await self.page.screenshot(path="debug_table.png")
            print("📸 Debug screenshot saved")
            content = await self.page.content()
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("📄 HTML saved to debug_page.html")
            return None

        rows = await table.query_selector_all("tbody tr")
        if not rows:
            rows = await table.query_selector_all("tr")
        if not rows:
            print("⚠️ No rows!")
            return None

        print(f"✅ Found {len(rows)} rows")
        data = []
        for row in rows[:20]:
            cols = await row.query_selector_all("td")
            if len(cols) >= 4:
                try:
                    period = await cols[0].text_content()
                    number = await cols[1].text_content()
                    size_text = await cols[3].text_content()
                    size = size_text.strip().lower() if size_text else "unknown"

                    color_value = "unknown"
                    color_elem = await cols[2].query_selector("span, div, i")
                    if color_elem:
                        class_name = await color_elem.get_attribute("class") or ""
                        style = await color_elem.get_attribute("style") or ""
                        combined = (class_name + style).lower()
                        if "green" in combined:
                            color_value = "green"
                        elif "red" in combined:
                            color_value = "red"
                        elif "violet" in combined or "purple" in combined:
                            color_value = "violet"

                    if period and number:
                        data.append({
                            "period": period.strip(),
                            "number": int(number.strip()),
                            "color": color_value,
                            "size": size,
                            "timestamp": str(datetime.now())
                        })
                except Exception as e:
                    print(f"⚠️ Row parsing error: {e}")
                    continue

        return data

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
            self.is_logged_in = False
            print("🔒 Browser closed")


# ============================================
# GLOBAL BROWSER INSTANCE (Playwright)
# ============================================

browser_session = PersistentBrowser()

# ============================================
# BEAUTIFULSOUP HELPERS
# ============================================

def fetch_headlines(url, tag="h2", limit=10):
    """Fetch headlines from a static website using BeautifulSoup."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = []
        # Try common headline tags
        for t in soup.find_all(['h1', 'h2', 'h3']):
            text = t.get_text(strip=True)
            if text and len(text) > 10:
                headlines.append(text)
        if not headlines:
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True)
                if text and len(text) > 15:
                    headlines.append(text)
        return headlines[:limit]
    except Exception as e:
        return None

# ============================================
# TELEGRAM COMMANDS
# ============================================

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🎯 Open BDG Game", web_app={"url": "https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo"})],
        [InlineKeyboardButton("📥 Scrape & Fetch", callback_data="fetch")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🔮 Prediction", callback_data="predict")]
    ]
    data = load_data()
    total = len(data)
    await update.message.reply_text(
        f"🎯 **BDG WinGo Scrape Bot + News Bot**\n\n📦 Total Records: {total}\n\n"
        f"**Commands:**\n"
        f"/add <color> <number> <size> - Single entry\n"
        f"/addbulk color num, ... - Bulk entry\n"
        f"/fetch - Auto scrape BDG Game\n"
        f"/news - Get latest headlines (BBC)\n"
        f"/scrape <url> - Get headlines from any URL\n"
        f"/view - Last 10 records\n"
        f"/pattern - Pattern analysis\n"
        f"/predict - Prediction\n"
        f"/stats - Statistics\n"
        f"/reset - Delete all data\n\n"
        f"📌 Example: /add green 7 big",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- BEAUTIFULSOUP COMMANDS ----------
async def news_cmd(update, context):
    """📰 Fetch BBC headlines using BeautifulSoup."""
    msg = await update.message.reply_text("📡 Fetching latest BBC headlines...")
    headlines = fetch_headlines("https://www.bbc.com/news", tag="h2", limit=10)
    if not headlines:
        await msg.edit_text("❌ Could not fetch headlines. BBC might have changed structure.")
        return
    reply = "📰 **Latest Headlines (BBC):**\n\n"
    for i, h in enumerate(headlines, 1):
        reply += f"{i}. {h}\n"
    await msg.edit_text(reply)

async def scrape_url_cmd(update, context):
    """📰 Scrape headlines from a given URL."""
    if not context.args:
        await update.message.reply_text("❗ Please provide a URL.\nExample: `/scrape https://www.bbc.com/news`")
        return
    url = context.args[0]
    msg = await update.message.reply_text(f"📡 Scraping: {url}...")
    headlines = fetch_headlines(url, limit=10)
    if not headlines:
        await msg.edit_text("❌ No headlines found or URL might be dynamic. Try another site.")
        return
    reply = f"📰 **Headlines from {url}:**\n\n"
    for i, h in enumerate(headlines, 1):
        reply += f"{i}. {h}\n"
    await msg.edit_text(reply)

# ---------- EXISTING COMMANDS ----------
async def add_result(update, context):
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❗ Use: /add <color> <number> <size>")
            return
        color = context.args[0].lower()
        number = int(context.args[1])
        size = context.args[2].lower() if len(context.args) > 2 else "unknown"
        if color not in ['red','green','violet']:
            await update.message.reply_text("❗ Colors: red, green, violet")
            return
        data = load_data()
        data.append({
            "color": color,
            "number": number,
            "size": size,
            "period": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "timestamp": str(datetime.now())
        })
        save_data(data)
        emoji = get_color_emoji(color)
        size_emoji = "📈" if size == "big" else "📉" if size == "small" else ""
        await update.message.reply_text(f"{emoji} **Saved:** {color.upper()} {number} {size_emoji} ({size})\n📦 Total: {len(data)}")
    except:
        await update.message.reply_text("❌ Error! Use: /add green 7 big")

async def add_bulk(update, context):
    try:
        text = ' '.join(context.args)
        entries = text.split(',')
        data = load_data()
        count = 0
        for entry in entries:
            entry = entry.strip()
            if not entry: continue
            parts = entry.split()
            if len(parts) >= 2:
                color = parts[0].lower()
                number = int(parts[1])
                size = parts[2].lower() if len(parts) > 2 else "unknown"
                if color in ['red','green','violet']:
                    data.append({
                        "color": color,
                        "number": number,
                        "size": size,
                        "period": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                        "timestamp": str(datetime.now())
                    })
                    count += 1
        save_data(data)
        await update.message.reply_text(f"✅ {count} records saved!\n📦 Total: {len(data)}")
    except:
        await update.message.reply_text("❌ Error! Use: /addbulk red 5 big, green 3 small")

async def fetch_data(update, context):
    global browser_session
    msg = await update.message.reply_text("📡 Scraping BDG Game data...")
    try:
        if not browser_session.is_logged_in:
            await browser_session.init()
        else:
            print("✅ Session already active, reusing browser...")
        data = await browser_session.navigate_to_wingo()
        if not data:
            await msg.edit_text("❌ Failed to scrape data. Table not found.")
            return
        existing = load_data()
        existing_periods = {item.get('period') for item in existing}
        new_count = 0
        for item in data:
            if item['period'] not in existing_periods:
                existing.append(item)
                new_count += 1
        save_data(existing)
        await msg.edit_text(
            f"✅ **Scraped Successfully!**\n"
            f"📊 New Records: {new_count}\n"
            f"📦 Total Records: {len(existing)}"
        )
    except Exception as e:
        logging.error(f"❌ Fetch error: {e}")
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")

async def view_data(update, context):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data.")
        return
    last_10 = data[-10:] if len(data) >= 10 else data
    msg = "📊 **Last 10 Records:**\n\n"
    for idx, item in enumerate(last_10, 1):
        emoji = get_color_emoji(item['color'])
        size_emoji = "📈" if item.get('size') == 'big' else "📉" if item.get('size') == 'small' else ""
        msg += f"{idx}. {emoji} {item['color'].upper()} {item['number']} {size_emoji} ({item.get('size', 'N/A')})\n"
    msg += f"\n📦 **Total:** {len(data)} records"
    await update.message.reply_text(msg)

async def stats(update, context):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data.")
        return
    total = len(data)
    red = sum(1 for i in data if i['color'] == 'red')
    green = sum(1 for i in data if i['color'] == 'green')
    violet = sum(1 for i in data if i['color'] == 'violet')
    await update.message.reply_text(
        f"📊 **Full Statistics**\n\n📦 Total: {total}\n"
        f"{get_color_emoji('red')} Red: {red} ({red/total*100:.1f}%)\n"
        f"{get_color_emoji('green')} Green: {green} ({green/total*100:.1f}%)\n"
        f"{get_color_emoji('violet')} Violet: {violet} ({violet/total*100:.1f}%)"
    )

async def pattern(update, context):
    data = load_data()
    if len(data) < 5:
        await update.message.reply_text("⚠️ Need 5+ records.")
        return
    last_50 = data[-50:] if len(data) >= 50 else data
    color_count = {}
    number_count = {}
    for item in last_50:
        color = item['color']
        num = item['number']
        color_count[color] = color_count.get(color, 0) + 1
        number_count[num] = number_count.get(num, 0) + 1
    streak_color = last_50[-1]['color']
    streak_count = 1
    for i in range(len(last_50)-2, -1, -1):
        if last_50[i]['color'] == streak_color:
            streak_count += 1
        else:
            break
    hot_color = max(color_count, key=color_count.get) if color_count else 'N/A'
    hot_number = max(number_count, key=number_count.get) if number_count else 0
    await update.message.reply_text(
        f"🎯 **Pattern Analysis**\n\n"
        f"📊 Last 50 Distribution:\n{get_color_emoji('red')} Red: {color_count.get('red', 0)}\n"
        f"{get_color_emoji('green')} Green: {color_count.get('green', 0)}\n"
        f"{get_color_emoji('violet')} Violet: {color_count.get('violet', 0)}\n\n"
        f"📈 Streak: {streak_count}x {streak_color.upper()}\n"
        f"🔥 Hot Color: {hot_color.upper()} ({color_count.get(hot_color, 0)}x)\n"
        f"🎯 Hot Number: {hot_number} ({number_count.get(hot_number, 0)}x)"
    )

async def predict(update, context):
    data = load_data()
    if len(data) < 5:
        await update.message.reply_text("⚠️ Need 5+ records.")
        return
    last_100 = data[-100:] if len(data) >= 100 else data
    total = len(last_100)
    red = sum(1 for i in last_100 if i['color'] == 'red')
    green = sum(1 for i in last_100 if i['color'] == 'green')
    violet = sum(1 for i in last_100 if i['color'] == 'violet')
    probs = {
        'RED': (red/total)*100,
        'GREEN': (green/total)*100,
        'VIOLET': (violet/total)*100
    }
    best = max(probs, key=probs.get)
    await update.message.reply_text(
        f"🔮 **Prediction**\n\n{get_color_emoji(best.lower())} **Best Bet:** {best} ({probs[best]:.1f}%)\n\n"
        f"📊 Probability:\n{get_color_emoji('red')} Red: {probs['RED']:.1f}%\n"
        f"{get_color_emoji('green')} Green: {probs['GREEN']:.1f}%\n"
        f"{get_color_emoji('violet')} Violet: {probs['VIOLET']:.1f}%\n\n"
        f"📦 Based on {total} rounds\n⚠️ Not financial advice."
    )

async def reset_data(update, context):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data to delete.")
        return
    save_data([])
    await update.message.reply_text(f"🗑️ {len(data)} records deleted!")

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "fetch":
        await query.edit_message_text("📡 Scraping BDG data...")
        global browser_session
        try:
            if not browser_session.is_logged_in:
                await browser_session.init()
            data = await browser_session.navigate_to_wingo()
            if data:
                existing = load_data()
                existing_periods = {item.get('period') for item in existing}
                count = 0
                for item in data:
                    if item['period'] not in existing_periods:
                        existing.append(item)
                        count += 1
                save_data(existing)
                await query.edit_message_text(f"✅ {count} new records saved!\n📦 Total: {len(existing)}")
            else:
                await query.edit_message_text("❌ No data scraped.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)[:100]}")
    elif query.data == "stats":
        data = load_data()
        if not data:
            await query.edit_message_text("📭 No data.")
            return
        total = len(data)
        red = sum(1 for i in data if i['color'] == 'red')
        green = sum(1 for i in data if i['color'] == 'green')
        violet = sum(1 for i in data if i['color'] == 'violet')
        await query.edit_message_text(
            f"📊 **Stats**\n📦 Total: {total}\n🔴 Red: {red} ({red/total*100:.1f}%)\n🟢 Green: {green} ({green/total*100:.1f}%)\n🟣 Violet: {violet} ({violet/total*100:.1f}%)"
        )
    elif query.data == "predict":
        data = load_data()
        if len(data) < 5:
            await query.edit_message_text("⚠️ Need 5+ records.")
            return
        last_100 = data[-100:] if len(data) >= 100 else data
        total = len(last_100)
        red = sum(1 for i in last_100 if i['color'] == 'red')
        green = sum(1 for i in last_100 if i['color'] == 'green')
        violet = sum(1 for i in last_100 if i['color'] == 'violet')
        probs = {'RED': (red/total)*100, 'GREEN': (green/total)*100, 'VIOLET': (violet/total)*100}
        best = max(probs, key=probs.get)
        await query.edit_message_text(
            f"🔮 **Prediction**\n🎯 Best: {best} ({probs[best]:.1f}%)\n🔴 Red: {probs['RED']:.1f}%\n🟢 Green: {probs['GREEN']:.1f}%\n🟣 Violet: {probs['VIOLET']:.1f}%"
        )

# ============================================
# AUTO FETCH (Playwright)
# ============================================

async def auto_fetch():
    global browser_session
    while True:
        try:
            if not browser_session.is_logged_in:
                await browser_session.init()
            data = await browser_session.navigate_to_wingo()
            if data:
                existing = load_data()
                existing_periods = {item.get('period') for item in existing}
                count = 0
                for item in data:
                    if item['period'] not in existing_periods:
                        existing.append(item)
                        count += 1
                if count > 0:
                    save_data(existing)
                    print(f"✅ Auto-scraped {count} new records | Total: {len(existing)}")
        except Exception as e:
            logging.error(f"Auto-fetch error: {e}")
        await asyncio.sleep(30)

# ============================================
# MAIN
# ============================================

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not set!")
        return
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_result))
    app.add_handler(CommandHandler("addbulk", add_bulk))
    app.add_handler(CommandHandler("fetch", fetch_data))
    app.add_handler(CommandHandler("news", news_cmd))
    app.add_handler(CommandHandler("scrape", scrape_url_cmd))
    app.add_handler(CommandHandler("view", view_data))
    app.add_handler(CommandHandler("pattern", pattern))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("reset", reset_data))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("✅ BDG WinGo Scrape Bot + News Bot is running...")
    loop = asyncio.get_event_loop()
    loop.create_task(auto_fetch())
    app.run_polling()

if __name__ == "__main__":
    main()
