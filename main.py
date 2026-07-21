# ============================================
# 📁 FILE: main.py
# 📝 DESCRIPTION: Main Telegram Bot Code
# 🎯 FEATURES: Auto Fetch, Pattern Detection, Live Prediction
# ============================================

import os
import json
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from playwright.async_api import async_playwright

# 📊 Logging setup
logging.basicConfig(level=logging.INFO)

# ============================================
# 📁 DATA STORE - JSON File Ke Saath Kaam Karega
# ============================================

DATA_FILE = "bdg_data.json"  # 📂 Data store file

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
# 🤖 PLAYWRIGHT SCRAPER - BDG Game Se Data Fetch Karega
# ============================================

async def scrape_bdg_live():
    """
    🌐 BDG Game se live data scrape karein
    📌 Returns: current_period, history (last 20 results)
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 🔗 BDG Game URL (working mirror)
            await page.goto("https://bdg7963.com", timeout=30000)
            
            # ⏳ Page load hone ka wait
            await page.wait_for_timeout(5000)
            
            # 📌 Live period number
            period_element = await page.query_selector(".period-number")
            current_period = await period_element.text_content() if period_element else "N/A"
            
            # 📊 Table se data nikaalna
            rows = await page.query_selector_all("table tbody tr")
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
            
            await browser.close()
            
            return {
                "current_period": current_period.strip(),
                "history": data
            }
    except Exception as e:
        logging.error(f"❌ Scrape error: {e}")
        return None

# ============================================
# 🧠 PATTERN DETECTION - Khud Pattern Samjhega
# ============================================

def detect_pattern(data):
    """
    🎯 Data ke hisaab se pattern detect karein
    📊 Returns: pattern_type, streak, best_color, probability
    """
    if len(data) < 5:
        return None
    
    # 📊 Last 20 results
    last_20 = data[-20:] if len(data) >= 20 else data
    
    # 🔢 Color frequency count
    color_count = {}
    for item in last_20:
        color = item['color']
        color_count[color] = color_count.get(color, 0) + 1
    
    # 📈 Current streak
    streak_color = last_20[-1]['color']
    streak_count = 1
    for i in range(len(last_20)-2, -1, -1):
        if last_20[i]['color'] == streak_color:
            streak_count += 1
        else:
            break
    
    # 🎯 Pattern type detect karein
    pattern_type = "Mixed"
    if streak_count >= 3:
        pattern_type = f"{streak_color.upper()} Streak"
    elif len(set([item['color'] for item in last_20[-5:]])) == 1:
        pattern_type = f"{last_20[-1]['color'].upper()} Dominating"
    elif len(set([item['color'] for item in last_20[-10:]])) == 3:
        pattern_type = "Balanced"
    
    # 🔮 Prediction (Probability)
    total = len(last_20)
    probs = {}
    for color in ['red', 'green', 'violet']:
        count = color_count.get(color, 0)
        # 🎯 Streak bonus
        if color == streak_color:
            count += streak_count * 2
        probs[color] = (count / (total + streak_count * 2)) * 100
    
    # 🏆 Best color
    best_color = max(probs, key=probs.get)
    
    # 🔢 Expected number (average)
    avg_number = sum([item['number'] for item in last_20]) / len(last_20)
    expected_number = round(avg_number)
    
    return {
        "pattern_type": pattern_type,
        "streak_color": streak_color,
        "streak_count": streak_count,
        "best_color": best_color,
        "best_probability": round(probs[best_color], 1),
        "expected_number": expected_number,
        "color_count": color_count,
        "last_20": last_20
    }

# ============================================
# 🤖 TELEGRAM BOT COMMANDS
# ============================================

async def start(update, context):
    """🚀 /start command - Welcome message with buttons"""
    keyboard = [
        [InlineKeyboardButton("🎯 Open BDG Game", web_app={"url": "https://bdg7963.com"})],
        [InlineKeyboardButton("📊 Auto Detect Pattern", callback_data="pattern")],
        [InlineKeyboardButton("🔮 Live Prediction", callback_data="predict")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎯 **BDG Smart Prediction Bot Active!**\n\n"
        "🤖 Bot automatically detects patterns\n"
        "📡 Fetches live data from BDG Game\n"
        "🔮 Gives predictions with live period\n\n"
        "**Commands:**\n"
        "/fetch - Fetch latest data\n"
        "/pattern - Show current pattern\n"
        "/predict - Live prediction\n"
        "/round - Current round status\n"
        "/stats - Total statistics",
        reply_markup=reply_markup
    )

async def fetch_data(update, context):
    """📡 /fetch command - Live data fetch karein"""
    await update.message.reply_text("📡 Fetching live data from BDG Game...")
    
    result = await scrape_bdg_live()
    if not result:
        await update.message.reply_text("❌ Failed to fetch data. Please try again.")
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
        
        # 🔮 Pattern detect automatically
        pattern = detect_pattern(existing)
        
        msg = f"""
✅ **Data Fetched Successfully!**
📌 Live Period: {current_period}
📊 New Records: {new_count}
📦 Total Records: {len(existing)}

🔮 **Auto Pattern Detection:**
🎯 Pattern Type: {pattern['pattern_type'] if pattern else 'Need more data'}
📈 Current Streak: {pattern['streak_count']}x {pattern['streak_color'].upper() if pattern else 'N/A'} in a row
🔥 Hot Color: {pattern['best_color'].upper() if pattern else 'N/A'} ({pattern['best_probability']}% chance)
"""
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ No data found.")

async def show_pattern(update, context):
    """📊 /pattern command - Current pattern dikhaye"""
    data = load_data()
    if len(data) < 5:
        await update.message.reply_text("⚠️ Need at least 5 records for pattern detection. Use /fetch first.")
        return
    
    pattern = detect_pattern(data)
    if not pattern:
        await update.message.reply_text("⚠️ Not enough data for pattern detection.")
        return
    
    # 🎨 Last 20 pattern
    colors = [item['color'].upper() for item in pattern['last_20']]
    pattern_sequence = " → ".join(colors)
    
    msg = f"""
🎯 **Auto Pattern Analysis**

📌 **Current Pattern Type:** {pattern['pattern_type']}

📊 **Last 20 Results:**
{pattern_sequence}

📈 **Current Streak:** {pattern['streak_count']}x {pattern['streak_color'].upper()} in a row

🔥 **Hot Color:** {pattern['best_color'].upper()} ({pattern['best_probability']}% chance)

🔢 **Expected Number:** {pattern['expected_number']}

📊 **Distribution (Last 20):**
🔴 Red: {pattern['color_count'].get('red', 0)}
🟢 Green: {pattern['color_count'].get('green', 0)}
🟣 Violet: {pattern['color_count'].get('violet', 0)}
"""
    await update.message.reply_text(msg)

async def predict_live(update, context):
    """🔮 /predict command - Live prediction with period"""
    await update.message.reply_text("📡 Fetching live data for prediction...")
    
    result = await scrape_bdg_live()
    if not result:
        await update.message.reply_text("❌ Failed to fetch live data. Please try again.")
        return
    
    current_period = result['current_period']
    data = result['history']
    
    if data:
        existing = load_data()
        existing_periods = {item.get('period') for item in existing}
        for item in data:
            if item['period'] not in existing_periods:
                existing.append(item)
        save_data(existing)
    
    all_data = load_data()
    if len(all_data) < 5:
        await update.message.reply_text("⚠️ Need more data for prediction. Use /fetch first.")
        return
    
    pattern = detect_pattern(all_data)
    if not pattern:
        await update.message.reply_text("⚠️ Not enough data for prediction.")
        return
    
    msg = f"""
🔮 **LIVE PREDICTION**

📌 **Live Period:** {current_period}

🎯 **Pattern Type:** {pattern['pattern_type']}

🎲 **Best Bet:** {pattern['best_color'].upper()} 
📊 **Win Probability:** {pattern['best_probability']}%

🔢 **Expected Number:** {pattern['expected_number']}

📈 **Current Streak:** {pattern['streak_count']}x {pattern['streak_color'].upper()} in a row

📊 **Probability Distribution:**
🔴 Red: {pattern['best_color']} → {pattern['best_probability']}%

💡 Based on last {len(pattern['last_20'])} rounds
⚠️ Not financial advice. Play responsibly.
"""
    await update.message.reply_text(msg)

async def current_round(update, context):
    """🎯 /round command - Current round status"""
    data = load_data()
    total = len(data)
    
    if total == 0:
        await update.message.reply_text("📭 No data yet. Use /fetch first.")
        return
    
    result = await scrape_bdg_live()
    current_period = result['current_period'] if result else "N/A"
    
    pattern = detect_pattern(data)
    
    msg = f"""
🎯 **Current Round Status**

📌 **Live Period:** {current_period}
📦 **Total Records:** {total}

📈 **Pattern Type:** {pattern['pattern_type'] if pattern else 'Need more data'}
📊 **Current Streak:** {pattern['streak_count']}x {pattern['streak_color'].upper() if pattern else 'N/A'}

🔥 **Hot Color:** {pattern['best_color'].upper() if pattern else 'N/A'} ({pattern['best_probability']}% chance)

💡 Use /predict for live prediction
"""
    await update.message.reply_text(msg)

async def stats(update, context):
    """📊 /stats command - Total statistics"""
    data = load_data()
    if not data:
        await update.message.reply_text("📭 No data yet. Use /fetch first.")
        return
    
    total = len(data)
    red = sum(1 for i in data if i['color'] == 'red')
    green = sum(1 for i in data if i['color'] == 'green')
    violet = sum(1 for i in data if i['color'] == 'violet')
    
    msg = f"""
📊 **Total Statistics**

📦 Total Records: {total}
🔴 Red: {red} ({red/total*100:.1f}%)
🟢 Green: {green} ({green/total*100:.1f}%)
🟣 Violet: {violet} ({violet/total*100:.1f}%)
"""
    await update.message.reply_text(msg)

async def reset_data(update, context):
    """🗑️ /reset command - Delete all data"""
    save_data([])
    await update.message.reply_text("🗑️ All data deleted!")

async def button_callback(update, context):
    """🔄 Button callbacks handle karein"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "pattern":
        await query.edit_message_text("📊 Detecting pattern...")
        data = load_data()
        if len(data) < 5:
            await query.edit_message_text("⚠️ Need 5+ records. Use /fetch first.")
            return
        pattern = detect_pattern(data)
        if pattern:
            colors = [item['color'].upper() for item in pattern['last_20']]
            pattern_sequence = " → ".join(colors)
            await query.edit_message_text(
                f"🎯 **Pattern Type:** {pattern['pattern_type']}\n\n"
                f"📊 **Last 20:** {pattern_sequence}\n"
                f"📈 **Streak:** {pattern['streak_count']}x {pattern['streak_color'].upper()}\n"
                f"🔥 **Hot Color:** {pattern['best_color'].upper()} ({pattern['best_probability']}%)"
            )
    
    elif query.data == "predict":
        await query.edit_message_text("📡 Fetching live prediction...")
        result = await scrape_bdg_live()
        if not result:
            await query.edit_message_text("❌ Failed to fetch live data.")
            return
        current_period = result['current_period']
        data = load_data()
        if len(data) < 5:
            await query.edit_message_text("⚠️ Need 5+ records. Use /fetch first.")
            return
        pattern = detect_pattern(data)
        if pattern:
            await query.edit_message_text(
                f"🔮 **LIVE PREDICTION**\n"
                f"📌 Period: {current_period}\n"
                f"🎯 Best Bet: {pattern['best_color'].upper()} ({pattern['best_probability']}%)\n"
                f"🔢 Expected Number: {pattern['expected_number']}\n"
                f"📈 Streak: {pattern['streak_count']}x {pattern['streak_color'].upper()}"
            )

# ============================================
# ⏰ AUTO FETCH SCHEDULE - Har 30 Seconds Mein Fetch Karega
# ============================================

async def auto_fetch():
    """⏰ Auto fetch data every 30 seconds"""
    while True:
        result = await scrape_bdg_live()
        if result and result['history']:
            existing = load_data()
            existing_periods = {item.get('period') for item in existing}
            new_count = 0
            for item in result['history']:
                if item['period'] not in existing_periods:
                    existing.append(item)
                    new_count += 1
            if new_count > 0:
                save_data(existing)
                print(f"✅ Auto-fetched {new_count} new records")
        await asyncio.sleep(30)  # ⏰ Har 30 seconds

# ============================================
# 🚀 MAIN - Bot Start Hoga Yahan Se
# ============================================

def main():
    """🚀 Bot start karne ka main function"""
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(token).build()
    
    # 📌 Commands register karein
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fetch", fetch_data))
    app.add_handler(CommandHandler("pattern", show_pattern))
    app.add_handler(CommandHandler("predict", predict_live))
    app.add_handler(CommandHandler("round", current_round))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("reset", reset_data))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ BDG Smart Bot is running...")
    
    # ⏰ Auto-fetch background task start
    loop = asyncio.get_event_loop()
    loop.create_task(auto_fetch())
    
    app.run_polling()

if __name__ == "__main__":
    main() 
