# ============================================
# 📁 FILE: main.py
# 📝 DESCRIPTION: Auto Scrape + Data Store Bot
# 🎯 FEATURES: Auto Scrape, Manual Add, Pattern, Prediction
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
# 📁 DATA STORE - JSON File
# ============================================

DATA_FILE = "bdg_data.json"

def load_data():
    """📥 JSON file se data load karein"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    """📤 Data ko JSON file mein save karein"""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ============================================
# 🤖 PLAYWRIGHT SCRAPER - Auto Scrape
# ============================================

async def scrape_bdg_live():
    """
    🌐 BDG Game se live data scrape karein
    📌 Returns: current_period, history (last 20 results)
    """
    try:
        async with async_playwright() as p:
            # Browser launch
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Multiple mirror URLs (agar ek kaam na kare toh doosra try kare)
            urls = [
                "https://bdg7963.com",
                "https://7bdg.com",
                "https://bdg5840.com",
                "https://bdg5945.com",
                "https://bdgarchery.com"
            ]
            
            data = None
            current_period = "N/A"
            
            for url in urls:
                try:
                    print(f"🌐 Trying URL: {url}")
                    await page.goto(url, timeout=15000)
                    await page.wait_for_timeout(3000)
                    
                    # Check if page loaded
                    period_element = await page.query_selector(".period-number")
                    if period_element:
                        current_period = await period_element.text_content() or "N/A"
                        print(f"✅ Period found: {current_period}")
                    
                    # Table se data nikaalna
                    rows = await page.query_selector_all("table tbody tr")
                    if rows and len(rows) > 0:
                        print(f"✅ Found {len(rows)} rows")
                        data = []
                        for row in rows[:20]:  # Sirf last 20 entries
                            cols = await row.query_selector_all("td")
                            if len(cols) >= 4:
                                period = await cols[0].text_content()
                                number = await cols[1].text_content()
                                color = await cols[2].text_content()
                                size = await cols[3].text_content()
                                
                                data.append({
                                    "period": period.strip(),
                                    "number": int(number.strip()),
                                    "color": color.strip().lower(),
                                    "size": size.strip().lower(),
                                    "timestamp": str(datetime.now())
                                })
                        break  # Data mil gaya toh loop break
                    else:
                        print(f"⚠️ No rows found on {url}")
                except Exception as e:
                    print(f"❌ URL failed: {url} - {e}")
                    continue  # Yeh URL kaam nahi kiya, next try karo
            
            await browser.close()
            
            if data:
                print(f"✅ Scraped {len(data)} records")
                return {
                    "current_period": current_period.strip(),
                    "history": data
                }
            else:
                print("❌ No data scraped from any URL")
                return None
    except Exception as e:
        logging.error(f"❌ Scrape error: {e}")
        return None

# ============================================
# 📝 MANUAL DATA ENTRY
# ============================================

async def add_result(update, context):
    """📝 /add command - Manual data store"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "❗ **Use:** /add <color> <number> <size>\n"
                "📌 **Example:** /add green 7 big\n\n"
                "🟢 Colors: red, green, violet\n"
                "📊 Size: big, small (optional)"
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
        
        await update.message.reply_text(
            f"✅ Saved: {color.upper()} {number} ({size})\n"
            f"📦 Total: {len(data)} records"
        )
    except ValueError:
        await update.message.reply_text("❗ Number invalid hai. Use: /add green 7 big")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ============================================
# 📊 BULK DATA ENTRY
# ============================================

async def add_bulk(update, context):
    """📊 /addbulk command - Multiple records ek saath"""
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

# ============================================
# 📥 AUTO FETCH / SCRAPE COMMAND
# ============================================

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
            f"📦 Total Records: {len(existing)}\n\n"
            f"💡 Use /view to see data"
        )
    else:
        await msg.edit_text("❌ No data found on website.")

# ============================================
# 📋 VIEW DATA
# ============================================

async def view_data(update, context):
    """📋 /view command - Last 10 records"""
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data yet. Use /add or /fetch")
        return
    
    last_10 = data[-10:] if len(data) >= 10 else data
    msg = "📊 **Last 10 Records:**\n\n"
    for idx, item in enumerate(last_10, 1):
        msg += f"{idx}. {item['color'].upper()} {item['number']} ({item['size']}) - {item.get('period', 'N/A')}\n"
    
    msg += f"\n📦 **Total:** {len(data)} records"
    await update.message.reply_text(msg)

# ============================================
# 📊 STATISTICS
# ============================================

async def stats(update, context):
    """📊 /stats command - Full statistics"""
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data yet.")
        return
    
    total = len(data)
    red = sum(1 for i in data if i['color'] == 'red')
    green = sum(1 for i in data if i['color'] == 'green')
    violet = sum(1 for i in data if i['color'] == 'violet')
    
    # Last 100 analysis
    last_100 = data[-100:] if total >= 100 else data
    
    # Color frequency
    color_count = {}
    for item in last_100:
        color = item['color']
        color_count[color] = color_count.get(color, 0) + 1
    
    # Streak
    streak_color = last_100[-1]['color'] if last_100 else 'N/A'
    streak_count = 1
    for i in range(len(last_100)-2, -1, -1):
        if last_100[i]['color'] == streak_color:
            streak_count += 1
        else:
            break
    
    hot_color = max(color_count, key=color_count.get) if color_count else 'N/A'
    
    msg = f"""
📊 **Full Statistics**

📦 Total Records: {total}

🔴 Red: {red} ({red/total*100:.1f}%)
🟢 Green: {green} ({green/total*100:.1f}%)
🟣 Violet: {violet} ({violet/total*100:.1f}%)

📈 Current Streak: {streak_count}x {streak_color.upper()}
🔥 Hot Color (Last 100): {hot_color.upper()}
"""
    await update.message.reply_text(msg)

# ============================================
# 🧠 PATTERN DETECTION
# ============================================

async def pattern(update, context):
    """🎯 /pattern command - Pattern analysis"""
    data = load_data()
    if len(data) < 5:
        await update.message.reply_text("⚠️ Need 5+ records. Use /add or /fetch")
        return
    
    last_50 = data[-50:] if len(data) >= 50 else data
    
    color_count = {}
    number_count = {}
    for item in last_50:
        color = item['color']
        num = item['number']
        color_count[color] = color_count.get(color, 0) + 1
        number_count[num] = number_count.get(num, 0) + 1
    
    # Streak
    streak_color = last_50[-1]['color']
    streak_count = 1
    for i in range(len(last_50)-2, -1, -1):
        if last_50[i]['color'] == streak_color:
            streak_count += 1
        else:
            break
    
    hot_color = max(color_count, key=color_count.get) if color_count else 'N/A'
    hot_number = max(number_count, key=number_count.get) if number_count else 0
    
    # Pattern sequence (last 20)
    last_20 = last_50[-20:] if len(last_50) >= 20 else last_50
    pattern_seq = " → ".join([item['color'].upper() for item in last_20])
    
    msg = f"""
🎯 **Pattern Analysis**

📊 Last 50 Distribution:
🔴 Red: {color_count.get('red', 0)}
🟢 Green: {color_count.get('green', 0)}
🟣 Violet: {color_count.get('violet', 0)}

📈 Streak: {streak_count}x {streak_color.upper()}
🔥 Hot Color: {hot_color.upper()} ({color_count.get(hot_color, 0)}x)
🎯 Hot Number: {hot_number} ({number_count.get(hot_number, 0)}x)

📋 Last 20 Pattern:
{pattern_seq}
"""
    await update.message.reply_text(msg)

# ============================================
# 🔮 PREDICTION
# ============================================

async def predict(update, context):
    """🔮 /predict command - Prediction based on data"""
    data = load_data()
    if len(data) < 5:
        await update.message.reply_text("⚠️ Need 5+ records. Use /add or /fetch")
        return
    
    # Last 100 for probability
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
    
    # Number prediction
    number_count = {}
    for item in last_100:
        num = item['number']
        number_count[num] = number_count.get(num, 0) + 1
    hot_number = max(number_count, key=number_count.get) if number_count else 0
    
    # Streak
    streak_color = data[-1]['color']
    streak_count = 1
    for i in range(len(data)-2, -1, -1):
        if data[i]['color'] == streak_color:
            streak_count += 1
        else:
            break
    
    msg = f"""
🔮 **Prediction**

🎯 Best Bet: **{best}** ({probs[best]:.1f}%)

📊 Probability Distribution:
🔴 Red: {prob_red:.1f}%
🟢 Green: {prob_green:.1f}%
🟣 Violet: {prob_violet:.1f}%

🎯 Hot Number: {hot_number}
📈 Current Streak: {streak_count}x {streak_color.upper()}

📦 Based on {total} rounds
⚠️ Not financial advice. Play responsibly.
"""
    await update.message.reply_text(msg)

# ============================================
# 🗑️ RESET
# ============================================

async def reset_data(update, context):
    """🗑️ /reset command - Delete all data"""
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data to delete.")
        return
    
    save_data([])
    await update.message.reply_text(f"🗑️ {len(data)} records deleted!")

# ============================================
# 🚀 START
# ============================================

async def start(update, context):
    """🚀 /start command"""
    keyboard = [
        [InlineKeyboardButton("📥 Scrape & Fetch", callback_data="fetch")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🔮 Prediction", callback_data="predict")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    data = load_data()
    total = len(data)
    
    await update.message.reply_text(
        f"🎯 **BDG Auto Scrape + Data Store Bot**\n\n"
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

# ============================================
# BUTTON CALLBACK
# ============================================

async def button_callback(update, context):
    """🔄 Button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "fetch":
        await query.edit_message_text("📡 Scraping live data from BDG Game...")
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
            await query.edit_message_text(
                f"✅ {count} new records saved!\n"
                f"📦 Total: {len(existing)} records"
            )
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
            f"📊 Red: {probs['RED']:.1f}%\n"
            f"📊 Green: {probs['GREEN']:.1f}%\n"
            f"📊 Violet: {probs['VIOLET']:.1f}%"
        )

# ============================================
# ⏰ AUTO FETCH BACKGROUND (Har 30 Seconds)
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
        await asyncio.sleep(30)  # Har 30 seconds

# ============================================
# 🚀 MAIN
# ============================================

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not set! Please set BOT_TOKEN in Railway variables.")
        return
    
    app = Application.builder().token(token).build()
    
    # Commands
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
    
    print("✅ BDG Auto Scrape Bot is running...")
    print(f"📁 Data file: {DATA_FILE}")
    
    # Auto-fetch background task
    loop = asyncio.get_event_loop()
    loop.create_task(auto_fetch())
    
    app.run_polling()

if __name__ == "__main__":
    main()
