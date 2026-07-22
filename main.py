# ============================================
# 📁 FILE: main.py
# 📝 DESCRIPTION: BDG WinGo Scrape Bot - Table Fix
# 🎯 FEATURES: Auto Scrape, Manual Add, Pattern, Prediction, Colors
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
# 🤖 SMART SCRAPER - Multiple Selectors
# ============================================

async def scrape_bdg_live():
    """
    🌐 BDG Game WinGo page se live data scrape karein
    📌 Multiple selectors try karega
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # ✅ Exact URL
            url = "https://7bdg.com/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo"
            
            print(f"🌐 Trying URL: {url}")
            
            # 📄 Page load
            await page.goto(url, timeout=30000)
            
            # ⏳ Wait for JavaScript to render
            await page.wait_for_timeout(8000)
            
            # 📸 Debug: Page screenshot
            await page.screenshot(path="page_load.png")
            print("📸 Page screenshot saved")
            
            # 📊 Multiple selectors try karein
            selectors = [
                "table",
                "table tbody",
                ".game-history table",
                ".history-table",
                "[class*='history'] table",
                ".MuiTable-root",
                ".ant-table",
                ".table-striped",
                "div[class*='table'] table",
                "div[class*='history'] table"
            ]
            
            table = None
            used_selector = None
            
            for selector in selectors:
                try:
                    table = await page.query_selector(selector)
                    if table:
                        used_selector = selector
                        print(f"✅ Table found with selector: {selector}")
                        break
                except Exception as e:
                    print(f"⚠️ Selector failed: {selector} - {e}")
                    continue
            
            if not table:
                print("❌ Table not found with any selector")
                
                # 📄 Print page title and URL for debugging
                title = await page.title()
                print(f"📄 Page title: {title}")
                print(f"🌐 Current URL: {page.url}")
                
                # 📸 Save full page HTML for debugging
                html = await page.content()
                with open("page_debug.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("📄 HTML saved to page_debug.html")
                
                await browser.close()
                return None
            
            # 📊 Rows extract karein
            rows = await table.query_selector_all("tbody tr")
            if not rows:
                rows = await table.query_selector_all("tr")
            
            if not rows or len(rows) == 0:
                print("⚠️ No rows found in table")
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
                        color_elem = await cols[2].query_selector("span") or await cols[2].query_selector("div") or await cols[2].query_selector("i")
                        size = await cols[3].text_content()
                        
                        # 🎨 Color extract
                        color_value = "unknown"
                        if color_elem:
                            class_name = await color_elem.get_attribute("class") or ""
                            style = await color_elem.get_attribute("style") or ""
                            combined = (class_name + style).lower()
                            
                            if "green" in combined or "#00ff00" in combined or "#008000" in combined:
                                color_value = "green"
                            elif "red" in combined or "#ff0000" in combined or "#ff4444" in combined:
                                color_value = "red"
                            elif "violet" in combined or "purple" in combined or "#800080" in combined:
                                color_value = "violet"
                        
                        # Color text content se bhi try karein
                        if color_value == "unknown":
                            color_text = await cols[2].text_content()
                            if color_text:
                                color_text = color_text.strip().lower()
                                if "green" in color_text:
                                    color_value = "green"
                                elif "red" in color_text:
                                    color_value = "red"
                                elif "violet" in color_text or "purple" in color_text:
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
                        print(f"⚠️ Row parsing error: {e}")
                        continue
            
            await browser.close()
            
            if data:
                print(f"✅ Scraped {len(data)} records")
                return {
                    "current_period": data[0]['period'] if data else "N/A",
                    "history": data
                }
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
    """📡 /fetch command"""
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
