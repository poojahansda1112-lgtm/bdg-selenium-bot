# ============================================
# 📁 FILE: main.py
# 📝 DESCRIPTION: BDG WinGo Scrape Bot - Complete Flow
# 🎯 FEATURES: Login -> Confirm -> Lottery -> WinGo 1 Min -> Scroll -> Scrape
# ============================================

import os
import json
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from playwright.async_api import async_playwright

# 📊 Logging
logging.basicConfig(level=logging.INFO)

# ============================================
# 📁 DATA STORE
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
# 🎨 COLOR CODES
# ============================================

COLORS = {
    "red": "🔴",
    "green": "🟢",
    "violet": "🟣",
    "big": "📈",
    "small": "📉"
}

def get_color_emoji(color):
    return COLORS.get(color.lower(), "⚪")

# ============================================
# 🤖 MAIN SCRAPER - Complete Flow
# ============================================

async def scrape_bdg_live():
    """
    🌐 BDG Game se data scrape karein
    📌 Login -> Confirm -> Lottery -> WinGo 1 Min -> Scroll -> Table Scrape
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            USERNAME = os.environ.get("BDG_USERNAME")
            PASSWORD = os.environ.get("BDG_PASSWORD")
            
            if not USERNAME or not PASSWORD:
                print("❌ Username/Password not set!")
                await browser.close()
                return None
            
            # ============================================
            # 1. LOGIN
            # ============================================
            print("🌐 Going to login page...")
            await page.goto("https://7bdg.com/#/login", timeout=60000)
            await page.wait_for_timeout(5000)
            
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
            login_button = await page.query_selector("#login-button") or await page.query_selector("button[type='submit']") or await page.query_selector("[class*='login']")
            if login_button:
                await login_button.click()
                print("✅ Login button clicked")
            else:
                print("⚠️ Login button not found!")
                await browser.close()
                return None
            
            await page.wait_for_timeout(5000)
            print("✅ Login successful!")
            
            # ============================================
            # 2. "Login Welcome" POP-UP - CONFIRM CLICK
            # ============================================
            print("🎯 Looking for Confirm button...")
            
            confirm_selectors = [
                "button:has-text('Confirm')",
                "button:has-text('confirm')",
                "button:has-text('OK')",
                "button:has-text('ok')",
                "[class*='confirm']",
                "[class*='Confirm']",
                ".confirm-btn",
                "button[class*='confirm']",
                "button[class*='Confirm']",
                "//button[contains(text(),'Confirm')]",
                "//button[contains(text(),'confirm')]",
                "//button[contains(text(),'OK')]"
            ]
            
            confirm_button = None
            for selector in confirm_selectors:
                try:
                    if selector.startswith("//"):
                        confirm_button = await page.locator(selector).first
                    else:
                        confirm_button = await page.query_selector(selector)
                    if confirm_button:
                        print(f"✅ Confirm button found with selector: {selector}")
                        break
                except:
                    continue
            
            if confirm_button:
                await confirm_button.click()
                print("✅ Confirm button clicked")
                await page.wait_for_timeout(3000)
            else:
                print("⚠️ Confirm button not found! Continuing...")
            
            # ============================================
            # 3. LOTTERY TAB CLICK
            # ============================================
            print("🎯 Looking for Lottery tab...")
            
            lottery_selectors = [
                "a:has-text('Lottery')",
                "span:has-text('Lottery')",
                "div:has-text('Lottery')",
                "button:has-text('Lottery')",
                "[class*='lottery']",
                "[class*='Lottery']",
                "li:has-text('Lottery')",
                "//a[contains(text(),'Lottery')]",
                "//span[contains(text(),'Lottery')]",
                "//div[contains(text(),'Lottery')]",
                "//*[contains(text(),'Lottery')]"
            ]
            
            lottery_tab = None
            for selector in lottery_selectors:
                try:
                    if selector.startswith("//"):
                        lottery_tab = await page.locator(selector).first
                    else:
                        lottery_tab = await page.query_selector(selector)
                    if lottery_tab:
                        print(f"✅ Lottery tab found with selector: {selector}")
                        break
                except:
                    continue
            
            if lottery_tab:
                await lottery_tab.click()
                print("✅ Lottery tab clicked")
                await page.wait_for_timeout(3000)
            else:
                print("⚠️ Lottery tab not found! Trying URL directly...")
                await page.goto("https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo", timeout=60000)
                await page.wait_for_timeout(3000)
            
            # ============================================
            # 4. WIN GO 1 MIN SELECT
            # ============================================
            print("🎯 Looking for WinGo 1 Min...")
            
            wingo_selectors = [
                "a:has-text('WinGo 1 Min')",
                "span:has-text('WinGo 1 Min')",
                "div:has-text('WinGo 1 Min')",
                "button:has-text('WinGo 1 Min')",
                "li:has-text('WinGo 1 Min')",
                "[class*='WinGo']:has-text('1 Min')",
                "//a[contains(text(),'WinGo 1 Min')]",
                "//span[contains(text(),'WinGo 1 Min')]",
                "//div[contains(text(),'WinGo 1 Min')]",
                "//*[contains(text(),'WinGo') and contains(text(),'1 Min')]"
            ]
            
            wingo_tab = None
            for selector in wingo_selectors:
                try:
                    if selector.startswith("//"):
                        wingo_tab = await page.locator(selector).first
                    else:
                        wingo_tab = await page.query_selector(selector)
                    if wingo_tab:
                        print(f"✅ WinGo 1 Min found with selector: {selector}")
                        break
                except:
                    continue
            
            if wingo_tab:
                await wingo_tab.click()
                print("✅ WinGo 1 Min clicked")
                await page.wait_for_timeout(5000)
            else:
                print("⚠️ WinGo 1 Min not found! Trying fallback...")
                await page.goto("https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo", timeout=60000)
                await page.wait_for_timeout(5000)
            
            # ============================================
            # 5. SCROLL DOWN
            # ============================================
            print("📜 Scrolling down...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)
            
            # ============================================
            # 6. TABLE SCRAPE
            # ============================================
            print("📊 Looking for table...")
            table_selectors = [
                "table",
                "table tbody",
                ".game-history table",
                ".history-table",
                "[class*='history'] table",
                "div[class*='table']",
                ".ant-table",
                ".MuiTable-root"
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    table = await page.query_selector(selector)
                    if table:
                        print(f"✅ Table found with selector: {selector}")
                        break
                except:
                    continue
            
            if not table:
                print("❌ Table not found!")
                content = await page.content()
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("📄 HTML saved to debug.html")
                await browser.close()
                return None
            
            rows = await table.query_selector_all("tbody tr")
            if not rows:
                rows = await table.query_selector_all("tr")
            
            if not rows:
                print("⚠️ No rows found!")
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
                    except Exception as e:
                        print(f"⚠️ Row error: {e}")
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
# 📝 COMMANDS
# ============================================

async def start(update, context):
    """🚀 /start command"""
    keyboard = [
        [InlineKeyboardButton("🎯 Open BDG Game", web_app={"url": "https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo"})],
        [InlineKeyboardButton("📥 Scrape & Fetch", callback_data="fetch")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🔮 Prediction", callback_data="predict")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    data = load_data()
    total = len(data)
    
    await update.message.reply_text(
        f"🎯 **BDG WinGo Scrape Bot**\n\n"
        f"📦 Total Records: {total}\n\n"
        f"**Commands:**\n"
        f"/add <color> <number> <size> - Single entry\n"
        f"/addbulk color num, ... - Bulk entry\n"
        f"/fetch - Auto scrape from game\n"
        f"/view - View last 10 records\n"
        f"/pattern - Pattern analysis\n"
        f"/predict - Prediction\n"
        f"/stats - Statistics\n"
        f"/reset - Delete all data\n\n"
        f"📌 Example: /add green 7 big",
        reply_markup=reply_markup
    )

async def add_result(update, context):
    """📝 /add command"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "❗ **Use:** /add <color> <number> <size>\n"
                "📌 **Example:** /add green 7 big"
            )
            return
        
        color = context.args[0].lower()
        number = int(context.args[1])
        size = context.args[2].lower() if len(context.args) > 2 else "unknown"
        
        if color not in ['red', 'green', 'violet']:
            await update.message.reply_text("❗ Use: red, green, violet")
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
        await update.message.reply_text(
            f"{emoji} **Saved:** {color.upper()} {number} {size_emoji} ({size})\n"
            f"📦 **Total:** {len(data)} records"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def add_bulk(update, context):
    """📊 /addbulk command"""
    try:
        text = ' '.join(context.args)
        entries = text.split(',')
        
        data = load_data()
        count = 0
        
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split()
            if len(parts) >= 2:
                color = parts[0].lower()
                number = int(parts[1])
                size = parts[2].lower() if len(parts) > 2 else "unknown"
                
                if color in ['red', 'green', 'violet']:
                    data.append({
                        "color": color,
                        "number": number,
                        "size": size,
                        "period": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                        "timestamp": str(datetime.now())
                    })
                    count += 1
        
        save_data(data)
        await update.message.reply_text(
            f"✅ {count} records saved!\n"
            f"📦 Total: {len(data)} records"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def fetch_data(update, context):
    """📡 /fetch command - Auto scrape from BDG Game"""
    msg = await update.message.reply_text("📡 Scraping live data from BDG Game...")
    
    result = await scrape_bdg_live()
    
    if not result:
        await msg.edit_text("❌ Failed to scrape data. Please try again.")
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
        
        await msg.edit_text(
            f"✅ **Scraped Successfully!**\n"
            f"📌 Live Period: {current_period}\n"
            f"📊 New Records: {new_count}\n"
            f"📦 Total Records: {len(existing)}"
        )
    else:
        await msg.edit_text("❌ No data found on website.")

async def view_data(update, context):
    """📋 /view command"""
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data yet.")
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
    """📊 /stats command"""
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data yet.")
        return
    
    total = len(data)
    red = sum(1 for i in data if i['color'] == 'red')
    green = sum(1 for i in data if i['color'] == 'green')
    violet = sum(1 for i in data if i['color'] == 'violet')
    
    msg = f"""
📊 **Full Statistics**

📦 Total Records: {total}

{get_color_emoji('red')} Red: {red} ({red/total*100:.1f}%)
{get_color_emoji('green')} Green: {green} ({green/total*100:.1f}%)
{get_color_emoji('violet')} Violet: {violet} ({violet/total*100:.1f}%)
"""
    await update.message.reply_text(msg)

async def pattern(update, context):
    """🎯 /pattern command"""
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
    
    msg = f"""
🎯 **Pattern Analysis**

📊 Last 50 Distribution:
{get_color_emoji('red')} Red: {color_count.get('red', 0)}
{get_color_emoji('green')} Green: {color_count.get('green', 0)}
{get_color_emoji('violet')} Violet: {color_count.get('violet', 0)}

📈 Streak: {streak_count}x {streak_color.upper()}
🔥 Hot Color: {hot_color.upper()} ({color_count.get(hot_color, 0)}x)
🎯 Hot Number: {hot_number} ({number_count.get(hot_number, 0)}x)
"""
    await update.message.reply_text(msg)

async def predict(update, context):
    """🔮 /predict command"""
    data = load_data()
    if len(data) < 5:
        await update.message.reply_text("⚠️ Need 5+ records.")
        return
    
    last_100 = data[-100:] if len(data) >= 100 else data
    total = len(last_100)
    
    red = sum(1 for i in last_100 if i['color'] == 'red')
    green = sum(1 for i in last_100 if i['color'] == 'green')
    violet = sum(1 for i in last_100 if i['color'] == 'violet')
    
    prob_red = (red / total) * 100
    prob_green = (green / total) * 100
    prob_violet = (violet / total) * 100
    
    probs = {'RED': prob_red, 'GREEN': prob_green, 'VIOLET': prob_violet}
    best = max(probs, key=probs.get)
    
    msg = f"""
🔮 **Prediction**

{get_color_emoji(best.lower())} **Best Bet:** {best} ({probs[best]:.1f}%)

📊 **Probability:**
{get_color_emoji('red')} Red: {prob_red:.1f}%
{get_color_emoji('green')} Green: {prob_green:.1f}%
{get_color_emoji('violet')} Violet: {prob_violet:.1f}%

📦 Based on {total} rounds
⚠️ Not financial advice.
"""
    await update.message.reply_text(msg)

async def reset_data(update, context):
    """🗑️ /reset command"""
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data to delete.")
        return
    
    save_data([])
    await update.message.reply_text(f"🗑️ {len(data)} records deleted!")

async def button_callback(update, context):
    """🔄 Button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "fetch":
        await query.edit_message_text("📡 Scraping live data...")
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
            await query.edit_message_text("📭 No data yet.")
            return
        total = len(data)
        red = sum(1 for i in data if i['color'] == 'red')
        green = sum(1 for i in data if i['color'] == 'green')
        violet = sum(1 for i in data if i['color'] == 'violet')
        await query.edit_message_text(
            f"📊 **Stats**\n"
            f"📦 Total: {total}\n"
            f"🔴 Red: {red} ({red/total*100:.1f}%)\n"
            f"🟢 Green: {green} ({green/total*100:.1f}%)\n"
            f"🟣 Violet: {violet} ({violet/total*100:.1f}%)"
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
        probs = {
            'RED': (red/total)*100,
            'GREEN': (green/total)*100,
            'VIOLET': (violet/total)*100
        }
        best = max(probs, key=probs.get)
        await query.edit_message_text(
            f"🔮 **Prediction**\n"
            f"🎯 Best: {best} ({probs[best]:.1f}%)\n"
            f"🔴 Red: {probs['RED']:.1f}%\n"
            f"🟢 Green: {probs['GREEN']:.1f}%\n"
            f"🟣 Violet: {probs['VIOLET']:.1f}%"
        )

# ============================================
# ⏰ AUTO FETCH
# ============================================

async def auto_fetch():
    """⏰ Auto fetch every 30 seconds"""
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
# 🚀 MAIN
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
