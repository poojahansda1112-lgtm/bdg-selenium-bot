# ============================================
# 📁 FILE: main.py
# 📝 DESCRIPTION: BDG WinGo Scrape Bot (Final)
# 🔗 GAME: WinGo 1 Minute (WinGo_1M)
# 🆕 NEW COMMAND: /screenshot
# ============================================

import os
import json
import logging
import asyncio
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)

# ============================================
# DATA STORE
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
# SCREENSHOT HELPER
# ============================================

async def take_screenshot(page, path="screenshot.png"):
    await page.screenshot(path=path)
    return path

# ============================================
# MAIN SCRAPER (UPDATED)
# ============================================

async def scrape_bdg_live(screenshot_mode=False):
    """
    If screenshot_mode=True, it will just take a screenshot of the home page and return the file path.
    Otherwise, it will perform full scrape.
    """
    try:
        async with async_playwright() as p:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1280, 'height': 720}
            )
            page = await context.new_page()

            USERNAME = os.environ.get("BDG_USERNAME")
            PASSWORD = os.environ.get("BDG_PASSWORD")
            if not USERNAME or not PASSWORD:
                print("❌ Username/Password not set!")
                await browser.close()
                return None

            # ---------- LOGIN ----------
            print("🌐 Going to login page...")
            await page.goto("https://7bdg.com/#/login", timeout=60000)
            await page.wait_for_timeout(5000 + random.randint(1000, 3000))

            print("📝 Filling username...")
            username_input = await page.query_selector("#username") or await page.query_selector("input[type='text']")
            if username_input:
                await username_input.fill(USERNAME)
                print(f"✅ Username filled: {USERNAME}")

            print("🔑 Filling password...")
            password_input = await page.query_selector("#password") or await page.query_selector("input[type='password']")
            if password_input:
                await password_input.fill(PASSWORD)
                print("✅ Password filled")

            print("🖱️ Clicking login button...")
            login_button = (
                await page.query_selector("#login-button") or
                await page.query_selector("button[type='submit']") or
                await page.query_selector("[class*='login']")
            )
            if login_button:
                await login_button.click()
                print("✅ Login button clicked")
            else:
                print("⚠️ Login button not found!")
                await browser.close()
                return None

            await page.wait_for_timeout(5000 + random.randint(1000, 3000))
            print("✅ Login successful!")

            # ---------- CONFIRM POPUP ----------
            print("🎯 Looking for Confirm button...")
            confirm_clicked = False

            try:
                xpath = "//*[contains(text(),'Confirm') or contains(text(),'confirm')]"
                element = await page.locator(xpath).first
                if element and await element.is_visible():
                    await element.click()
                    confirm_clicked = True
                    print("✅ Confirm clicked via XPath")
            except:
                pass

            if not confirm_clicked:
                try:
                    element = await page.locator(":has-text('Confirm')").first
                    if element:
                        await element.click()
                        confirm_clicked = True
                        print("✅ Confirm clicked via :has-text")
                except:
                    pass

            if not confirm_clicked:
                try:
                    await page.evaluate("""
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
                except:
                    pass

            if confirm_clicked:
                await page.wait_for_timeout(3000 + random.randint(500, 1500))
            else:
                print("ℹ️ No Confirm - Skipping")

            # ---------- IF SCREENSHOT MODE ----------
            if screenshot_mode:
                print("📸 Taking screenshot of home page...")
                # Wait a bit for the page to fully load
                await page.wait_for_timeout(2000)
                screenshot_path = "home_page.png"
                await page.screenshot(path=screenshot_path)
                await browser.close()
                return screenshot_path

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
                "[data-tab*='lottery']",
                "[data-tab*='Lottery']",
                "button:has-text('Lottery')"
            ]

            for sel in lottery_selectors:
                try:
                    if sel.startswith("//"):
                        element = await page.locator(sel).first
                    else:
                        element = await page.query_selector(sel)
                    if element and await element.is_visible():
                        await element.click()
                        lottery_clicked = True
                        print(f"✅ Lottery clicked via selector: {sel}")
                        break
                except:
                    continue

            if not lottery_clicked:
                try:
                    element = await page.locator("text=Lottery").first
                    if element:
                        parent = await element.locator("xpath=..")
                        if parent:
                            await parent.click()
                            lottery_clicked = True
                            print("✅ Lottery clicked via parent element")
                except:
                    pass

            if not lottery_clicked:
                print("⚠️ Lottery not clickable! Using direct URL...")
                await page.goto("https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo", timeout=60000)
                await page.wait_for_timeout(3000 + random.randint(500, 1500))
                lottery_clicked = True

            if lottery_clicked:
                await page.wait_for_timeout(3000 + random.randint(500, 1500))

            # ---------- WIN GO 1MIN ----------
            print("🎯 Looking for Win Go 1Min...")
            wingo_clicked = False

            wingo_selectors = [
                "//*[contains(text(),'Win Go 1Min')]",
                "span:has-text('Win Go 1Min')",
                "div:has-text('Win Go 1Min')",
                "a:has-text('Win Go 1Min')",
                "li:has-text('Win Go 1Min')"
            ]

            for sel in wingo_selectors:
                try:
                    if sel.startswith("//"):
                        element = await page.locator(sel).first
                    else:
                        element = await page.query_selector(sel)
                    if element and await element.is_visible():
                        await element.click()
                        wingo_clicked = True
                        print(f"✅ Win Go 1Min clicked via selector: {sel}")
                        break
                except:
                    continue

            if not wingo_clicked:
                print("⚠️ Win Go 1Min not clickable! Using direct URL...")
                await page.goto("https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo", timeout=60000)
                await page.wait_for_timeout(5000 + random.randint(1000, 3000))
                wingo_clicked = True

            if wingo_clicked:
                await page.wait_for_timeout(5000 + random.randint(1000, 3000))

            # ---------- DIRECT NAVIGATION ----------
            print("🌐 Navigating directly to WinGo 1 Min page...")
            await page.goto("https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo", timeout=60000)

            print("⏳ Waiting for page to load...")
            await page.wait_for_timeout(10000)

            # Debug info
            title = await page.title()
            url = page.url
            print(f"📄 Page title: {title}")
            print(f"🌐 Final URL: {url}")

            # Wait for table
            try:
                await page.wait_for_selector("table", timeout=30000)
                print("✅ Table appeared after wait")
            except:
                print("⚠️ Table did not appear within 30 seconds")

            # ---------- SCROLL DOWN ----------
            print("📜 Scrolling down...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000 + random.randint(500, 1500))

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
                    table = await page.query_selector(sel)
                    if table:
                        print(f"✅ Table found: {sel}")
                        break
                except:
                    continue

            if not table:
                print("❌ Table not found!")
                await page.screenshot(path="debug_table.png")
                print("📸 Debug screenshot saved")
                await browser.close()
                return None

            rows = await table.query_selector_all("tbody tr")
            if not rows:
                rows = await table.query_selector_all("tr")
            if not rows:
                print("⚠️ No rows!")
                await browser.close()
                return None

            print(f"✅ Found {len(rows)} rows")
            data = []
            for row in rows[:20]:
                cols = await row.query_selector_all("td")
                if len(cols) >= 4:
                    try:
                        period = await cols[0].text_content()
                        number = await cols[1].text_content()
                        size = await cols[3].text_content()

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
                                "size": size.strip().lower() if size else "unknown",
                                "timestamp": str(datetime.now())
                            })
                    except:
                        continue

            await browser.close()
            if data:
                print(f"✅ Scraped {len(data)} records")
                return {"current_period": data[0]['period'], "history": data}
            else:
                print("❌ No data scraped")
                return None

    except Exception as e:
        logging.error(f"❌ Scrape error: {e}")
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
        f"🎯 **BDG WinGo Scrape Bot**\n\n📦 Total Records: {total}\n\n"
        f"**Commands:**\n/add <color> <number> <size>\n/addbulk color num, ...\n"
        f"/fetch - Auto scrape\n/view - Last 10\n/pattern - Pattern\n/predict - Prediction\n"
        f"/stats - Statistics\n/reset - Delete all\n"
        f"/screenshot - 📸 Take home page screenshot\n\n"
        f"📌 Example: /add green 7 big",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def screenshot_cmd(update, context):
    """📸 Take a screenshot of the home page after login."""
    msg = await update.message.reply_text("📸 Logging in and capturing home page...")
    result = await scrape_bdg_live(screenshot_mode=True)
    if result and isinstance(result, str) and result.endswith(".png"):
        with open(result, "rb") as f:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=f,
                caption="📸 Home page screenshot captured!"
            )
            await msg.edit_text("✅ Screenshot sent!")
    else:
        await msg.edit_text("❌ Failed to capture screenshot. Check logs.")

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
    msg = await update.message.reply_text("📡 Scraping live data...")
    result = await scrape_bdg_live()
    if not result:
        await msg.edit_text("❌ Failed to scrape.")
        return
    data = result['history']
    current_period = result['current_period']
    if data:
        existing = load_data()
        existing_periods = {item.get('period') for item in existing}
        new_count = 0
        for item in data:
            if item['period'] not in existing_periods:
                existing.append(item)
                new_count += 1
        save_data(existing)
        await msg.edit_text(f"✅ **Scraped Successfully!**\n📌 Period: {current_period}\n📊 New: {new_count}\n📦 Total: {len(existing)}")
    else:
        await msg.edit_text("❌ No data found.")

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
        await query.edit_message_text("📡 Scraping...")
        result = await scrape_bdg_live()
        if result and result['history']:
            existing = load_data()
            existing_periods = {item.get('period') for item in existing}
            count = 0
            for item in result['history']:
                if item['period'] not in existing_periods:
                    existing.append(item)
                    count += 1
            save_data(existing)
            await query.edit_message_text(f"✅ {count} new records saved!\n📦 Total: {len(existing)}")
        else:
            await query.edit_message_text("❌ No data scraped.")
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
# AUTO FETCH
# ============================================

async def auto_fetch():
    while True:
        try:
            result = await scrape_bdg_live()
            if result and result['history']:
                existing = load_data()
                existing_periods = {item.get('period') for item in existing}
                count = 0
                for item in result['history']:
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
    app.add_handler(CommandHandler("screenshot", screenshot_cmd))
    app.add_handler(CommandHandler("add", add_result))
    app.add_handler(CommandHandler("addbulk", add_bulk))
    app.add_handler(CommandHandler("fetch", fetch_data))
    app.add_handler(CommandHandler("view", view_data))
    app.add_handler(CommandHandler("pattern", pattern))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("reset", reset_data))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("✅ BDG WinGo Scrape Bot is running...")
    loop = asyncio.get_event_loop()
    loop.create_task(auto_fetch())
    app.run_polling()

if __name__ == "__main__":
    main() 
