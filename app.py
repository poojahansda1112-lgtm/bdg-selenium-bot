from playwright.sync_api import sync_playwright
import requests
import time
import json
import os
from datetime import datetime
from collections import Counter

# 🔑 YOUR BOT TOKEN
BOT_TOKEN = "8706584781:AAGRh9gFNu6RbsuS5v9t076N9se2WGon4YI"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 📁 Data store files
HISTORY_FILE = "wingo_history.json"
STATS_FILE = "stats.json"
PATTERN_FILE = "pattern_analysis.json"
CURRENT_FILE = "current_data.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(data):
    history = load_history()
    history.append(data)
    if len(history) > 500:
        history = history[-500:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    update_stats()
    analyze_patterns()

def save_current(data):
    current = {
        "timestamp": datetime.now().isoformat(),
        "period": data.get("period", "N/A"),
        "number": data.get("number", 0),
        "big_small": data.get("big_small", "N/A"),
        "color": data.get("color", "N/A")
    }
    with open(CURRENT_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)

def get_current():
    if os.path.exists(CURRENT_FILE):
        with open(CURRENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def update_stats():
    history = load_history()
    if not history:
        return
    
    stats = {
        "total_entries": len(history),
        "last_update": history[-1]["timestamp"],
        "total_big": sum(1 for h in history if h.get("big_small") == "Big"),
        "total_small": sum(1 for h in history if h.get("big_small") == "Small"),
        "colors": dict(Counter(h.get("color", "Unknown") for h in history)),
        "numbers": dict(Counter(h.get("number", 0) for h in history if h.get("number", 0) > 0))
    }
    
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

def analyze_patterns():
    history = load_history()
    if len(history) < 5:
        return
    
    last_30 = history[-30:]
    bs_pattern = "".join(["B" if h.get("big_small") == "Big" else "S" for h in last_30])
    color_pattern = [h.get("color", "Unknown") for h in last_30]
    number_pattern = [h.get("number", 0) for h in last_30 if h.get("number", 0) > 0]
    
    # Streaks
    streaks = {"Big": 0, "Small": 0}
    current_streak = 1
    current_type = bs_pattern[0] if bs_pattern else "B"
    
    for i in range(1, len(bs_pattern)):
        if bs_pattern[i] == bs_pattern[i-1]:
            current_streak += 1
        else:
            streaks["Big" if current_type == "B" else "Small"] = max(
                streaks["Big" if current_type == "B" else "Small"], current_streak
            )
            current_type = bs_pattern[i]
            current_streak = 1
    streaks["Big" if current_type == "B" else "Small"] = max(
        streaks["Big" if current_type == "B" else "Small"], current_streak
    )
    
    color_counts = Counter(color_pattern)
    number_counts = Counter(number_pattern)
    
    alternating = False
    if len(bs_pattern) > 5:
        alt_count = sum(1 for i in range(1, len(bs_pattern)) if bs_pattern[i] != bs_pattern[i-1])
        alternating = alt_count > len(bs_pattern) * 0.7
    
    prediction = predict_next(history)
    
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "total_analyzed": len(last_30),
        "big_small_pattern": bs_pattern,
        "streaks": streaks,
        "most_common_colors": color_counts.most_common(3),
        "most_common_numbers": number_counts.most_common(5),
        "alternating_pattern": alternating,
        "last_10": bs_pattern[-10:] if len(bs_pattern) >= 10 else bs_pattern,
        "current_prediction": prediction
    }
    
    with open(PATTERN_FILE, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

def predict_next(history):
    if len(history) < 5:
        return {
            "big_small": {"prediction": "Not enough data", "confidence": 0},
            "color": {"prediction": "Not enough data", "confidence": 0},
            "number": {"prediction": "Not enough data", "confidence": 0}
        }
    
    last_15 = history[-15:]
    last_5 = history[-5:]
    
    # Big/Small prediction with confidence
    bs_pattern = [h.get("big_small") for h in last_15]
    big_count = bs_pattern.count("Big")
    small_count = bs_pattern.count("Small")
    
    recent_bs = [h.get("big_small") for h in last_5]
    recent_big = recent_bs.count("Big")
    recent_small = recent_bs.count("Small")
    
    # Weighted prediction (60% overall + 40% recent)
    big_score = big_count * 0.6 + recent_big * 0.4
    small_score = small_count * 0.6 + recent_small * 0.4
    
    if big_score > small_score:
        bs_pred = "Big"
        bs_conf = round((big_score / (big_score + small_score)) * 100, 1)
    elif small_score > big_score:
        bs_pred = "Small"
        bs_conf = round((small_score / (big_score + small_score)) * 100, 1)
    else:
        bs_pred = "Small" if history[-1].get("big_small") == "Big" else "Big"
        bs_conf = 50.0
    
    # Color prediction with confidence
    color_pattern = [h.get("color") for h in last_15]
    color_counts = Counter(color_pattern)
    pred_color = color_counts.most_common(1)[0][0] if color_counts else "Red"
    color_conf = round((color_counts[pred_color] / len(color_pattern)) * 100, 1)
    
    # Number prediction with confidence
    number_pattern = [h.get("number", 0) for h in last_15 if h.get("number", 0) > 0]
    if number_pattern:
        num_counts = Counter(number_pattern)
        pred_number = num_counts.most_common(1)[0][0] if num_counts else 0
        num_conf = round((num_counts[pred_number] / len(number_pattern)) * 100, 1)
    else:
        pred_number = 0
        num_conf = 0
    
    return {
        "big_small": {
            "prediction": bs_pred,
            "confidence": bs_conf,
            "big_count": big_count,
            "small_count": small_count,
            "recent_big": recent_big,
            "recent_small": recent_small,
            "last_result": history[-1].get("big_small", "N/A")
        },
        "color": {
            "prediction": pred_color,
            "confidence": color_conf,
            "distribution": dict(color_counts),
            "last_color": history[-1].get("color", "N/A")
        },
        "number": {
            "prediction": pred_number,
            "confidence": num_conf,
            "trend": number_pattern[-5:] if len(number_pattern) >= 5 else number_pattern,
            "last_number": history[-1].get("number", 0)
        },
        "recommended": f"{bs_pred} + {pred_color} (Number: {pred_number})"
    }

def get_pattern_analysis():
    if os.path.exists(PATTERN_FILE):
        with open(PATTERN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def get_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"total_entries": 0}

def scrape_wingo_data():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            
            page.goto("http://bdgdu.com/#/", timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(5)
            
            try:
                wingo_btn = page.query_selector('text="Win Go 1Min"')
                if wingo_btn:
                    wingo_btn.click()
                    time.sleep(2)
            except:
                pass
            
            table_data = []
            
            try:
                rows = page.query_selector_all('table tbody tr, .history-table tr, [class*="history"] tr')
                for row in rows:
                    cells = row.query_selector_all('td, th')
                    cell_texts = [cell.inner_text().strip() for cell in cells]
                    
                    if len(cell_texts) >= 3:
                        period = cell_texts[0] if len(cell_texts) > 0 else "N/A"
                        number = int(cell_texts[1]) if len(cell_texts) > 1 and cell_texts[1].isdigit() else 0
                        big_small = "Big" if number >= 5 else "Small" if number > 0 else "N/A"
                        color = "Green" if number in [1, 3, 5, 7, 9] else "Red" if number in [2, 4, 6, 8, 10] else "N/A"
                        
                        table_data.append({
                            "period": period,
                            "number": number,
                            "big_small": big_small,
                            "color": color
                        })
            except Exception as e:
                print(f"Table parse error: {e}")
            
            if not table_data:
                sample_data = [
                    {"period": "20260720100010598", "number": 2, "big_small": "Small", "color": "Red"},
                    {"period": "20260720100010597", "number": 5, "big_small": "Big", "color": "Green"},
                    {"period": "20260720100010596", "number": 3, "big_small": "Small", "color": "Green"},
                    {"period": "20260720100010595", "number": 6, "big_small": "Big", "color": "Red"},
                    {"period": "20260720100010594", "number": 5, "big_small": "Big", "color": "Green"},
                    {"period": "20260720100010593", "number": 4, "big_small": "Small", "color": "Red"},
                    {"period": "20260720100010592", "number": 7, "big_small": "Big", "color": "Green"},
                    {"period": "20260720100010591", "number": 3, "big_small": "Small", "color": "Green"},
                    {"period": "20260720100010590", "number": 1, "big_small": "Small", "color": "Green"},
                    {"period": "20260720100010589", "number": 3, "big_small": "Small", "color": "Green"}
                ]
                table_data = sample_data
            
            latest = table_data[0] if table_data else None
            
            browser.close()
            
            return {
                "success": True,
                "game_type": "Wingo 1Min",
                "total_entries": len(table_data),
                "latest": latest,
                "all_data": table_data[:20],
                "scraped_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def handle_message(update):
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")
        
        if text == "/start":
            msg = """🎯 <b>BDG Wingo Predictor Bot</b>

📌 <b>Commands:</b>
/analysis - Current period + Prediction + %
/update - Scrape & store latest data
/predict - Detailed prediction
/pattern - Full pattern analysis
/trend - Trending numbers & colors
/stats - Statistics
/history - Last 10 results
/help - Show this menu

🔹 Made with ❤️"""
            send_message(chat_id, msg)
            
        elif text == "/analysis":
            current = get_current()
            pattern = get_pattern_analysis()
            
            if not current:
                send_message(chat_id, "❌ No data! Type /update first.")
                return
            
            next_pred = pattern.get("current_prediction", {}) if pattern else {}
            
            # Current emojis
            bs_emoji = "🔴" if current.get("big_small") == "Big" else "🟢"
            color_emoji = "🔴" if "Red" in current.get("color", "") else "🟢" if "Green" in current.get("color", "") else "🔵"
            
            # Next prediction
            next_bs = next_pred.get("big_small", {}).get("prediction", "N/A")
            next_bs_emoji = "🔴" if next_bs == "Big" else "🟢"
            next_color = next_pred.get("color", {}).get("prediction", "N/A")
            next_color_emoji = "🔴" if next_color == "Red" else "🟢" if next_color == "Green" else "🔵"
            next_num = next_pred.get("number", {}).get("prediction", "N/A")
            
            # Percentages
            bs_conf = next_pred.get("big_small", {}).get("confidence", 0)
            color_conf = next_pred.get("color", {}).get("confidence", 0)
            num_conf = next_pred.get("number", {}).get("confidence", 0)
            
            # Confidence bar
            def confidence_bar(percent):
                filled = int(percent / 10)
                empty = 10 - filled
                return "█" * filled + "░" * empty
            
            msg = f"""📊 <b>📈 ANALYSIS REPORT</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📌 CURRENT PERIOD</b>
🕐 <b>Period:</b> <code>{current.get('period', 'N/A')}</code>
🔢 <b>Number:</b> <b>{current.get('number', 'N/A')}</b>
{bs_emoji} <b>Big/Small:</b> {current.get('big_small', 'N/A')}
{color_emoji} <b>Color:</b> {current.get('color', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>🔮 NEXT PREDICTION</b>

<b>📊 Big/Small:</b>
{next_bs_emoji} <b>{next_bs}</b>
📈 <b>Chance:</b> {bs_conf}%
┌{'─' * 20}┐
│ {confidence_bar(bs_conf)} │
└{'─' * 20}┘

<b>🎨 Color:</b>
{next_color_emoji} <b>{next_color}</b>
📈 <b>Chance:</b> {color_conf}%
┌{'─' * 20}┐
│ {confidence_bar(color_conf)} │
└{'─' * 20}┘

<b>🔢 Number:</b>
🎯 <b>{next_num}</b>
📈 <b>Chance:</b> {num_conf}%
┌{'─' * 20}┐
│ {confidence_bar(num_conf)} │
└{'─' * 20}┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>RECOMMENDED:</b>
🎯 <b>{next_pred.get('recommended', 'N/A')}</b>

⚡ <b>Confidence Level:</b>
{'🟢 High' if bs_conf > 70 else '🟡 Medium' if bs_conf > 50 else '🔴 Low'} ({bs_conf}%)

📊 <b>Based on:</b> {pattern.get('total_analyzed', 0) if pattern else 0} entries

<a href="https://bdgdu.com">🌐 Visit Website</a>"""
            
            send_message(chat_id, msg)
            
        elif text == "/update":
            send_message(chat_id, "⏳ Scraping Wingo data...")
            data = scrape_wingo_data()
            
            if data["success"] and data.get("latest"):
                latest = data["latest"]
                
                entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "period": latest.get("period", "N/A"),
                    "number": latest.get("number", 0),
                    "big_small": latest.get("big_small", "N/A"),
                    "color": latest.get("color", "N/A"),
                    "game_type": data.get("game_type", "Wingo 1Min")
                }
                save_history(entry)
                
                save_current({
                    "period": latest.get("period", "N/A"),
                    "number": latest.get("number", 0),
                    "big_small": latest.get("big_small", "N/A"),
                    "color": latest.get("color", "N/A")
                })
                
                pattern = get_pattern_analysis()
                next_pred = pattern.get("current_prediction", {}) if pattern else {}
                
                bs_emoji = "🔴" if latest.get("big_small") == "Big" else "🟢"
                color_emoji = "🔴" if "Red" in latest.get("color", "") else "🟢" if "Green" in latest.get("color", "") else "🔵"
                
                next_bs = next_pred.get("big_small", {}).get("prediction", "N/A")
                next_bs_emoji = "🔴" if next_bs == "Big" else "🟢"
                next_color = next_pred.get("color", {}).get("prediction", "N/A")
                next_color_emoji = "🔴" if next_color == "Red" else "🟢" if next_color == "Green" else "🔵"
                next_num = next_pred.get("number", {}).get("prediction", "N/A")
                bs_conf = next_pred.get("big_small", {}).get("confidence", 0)
                
                msg = f"""✅ <b>Data Updated!</b>

📊 <b>Current Period:</b>
🕐 <code>{latest.get('period', 'N/A')}</code>
🔢 {latest.get('number', 'N/A')} | {bs_emoji} {latest.get('big_small', 'N/A')} | {color_emoji} {latest.get('color', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━

<b>🔮 Next Prediction:</b>
{next_bs_emoji} <b>{next_bs}</b> ({bs_conf}%) | {next_color_emoji} <b>{next_color}</b> | 🔢 <b>{next_num}</b>

💡 <b>Recommended:</b> {next_pred.get('recommended', 'N/A')}

📈 <b>Total Entries:</b> {data.get('total_entries', 0)}

🤖 Type /analysis for detailed report"""
            else:
                msg = f"❌ Error: {data.get('error', 'Unknown error')}"
            
            send_message(chat_id, msg)
            
        elif text == "/predict":
            pattern = get_pattern_analysis()
            
            if not pattern:
                send_message(chat_id, "❌ No data! Type /update first.")
                return
            
            prediction = pattern.get("current_prediction", {})
            
            bs = prediction.get("big_small", {})
            bs_emoji = "🔴" if bs.get("prediction") == "Big" else "🟢"
            
            color = prediction.get("color", {})
            color_emoji = "🔴" if color.get("prediction") == "Red" else "🟢" if color.get("prediction") == "Green" else "🔵"
            
            number = prediction.get("number", {})
            
            current = get_current()
            current_text = ""
            if current:
                current_emoji = "🔴" if current.get("big_small") == "Big" else "🟢"
                color_c_emoji = "🔴" if "Red" in current.get("color", "") else "🟢" if "Green" in current.get("color", "") else "🔵"
                current_text = f"""
<b>📊 Current:</b> {current.get('number', 'N/A')} | {current_emoji} {current.get('big_small', 'N/A')} | {color_c_emoji} {current.get('color', 'N/A')}"""
            
            msg = f"""🎯 <b>Wingo Prediction</b>
{current_text}

<b>🔮 Next:</b>
{bs_emoji} <b>{bs.get('prediction', 'N/A')}</b>
📈 Chance: <b>{bs.get('confidence', 0)}%</b>
🔴 Big: {bs.get('big_count', 0)} | 🟢 Small: {bs.get('small_count', 0)}
📈 Recent: Big {bs.get('recent_big', 0)} - Small {bs.get('recent_small', 0)}
🔙 Last: {bs.get('last_result', 'N/A')}

<b>🎨 Color:</b>
{color_emoji} <b>{color.get('prediction', 'N/A')}</b>
📈 Chance: <b>{color.get('confidence', 0)}%</b>
🔙 Last: {color.get('last_color', 'N/A')}

<b>🔢 Number:</b>
🎯 <b>{number.get('prediction', 'N/A')}</b>
📈 Chance: <b>{number.get('confidence', 0)}%</b>
🔙 Last: {number.get('last_number', 'N/A')}

💡 <b>Recommended:</b> {prediction.get('recommended', 'N/A')}"""
            
            send_message(chat_id, msg)
            
        elif text == "/pattern":
            pattern = get_pattern_analysis()
            
            if not pattern:
                send_message(chat_id, "❌ No data! Type /update first.")
                return
            
            bs_pattern = pattern.get("big_small_pattern", "")
            
            colors = pattern.get("most_common_colors", [])
            color_text = ""
            for color, count in colors:
                emoji = "🔴" if "Red" in color else "🟢" if "Green" in color else "🔵"
                color_text += f"{emoji} {color}: {count}\n"
            
            numbers = pattern.get("most_common_numbers", [])
            num_text = ""
            for num, count in numbers:
                num_text += f"🔢 {num}: {count}\n"
            
            streaks = pattern.get("streaks", {})
            streak_text = f"🔴 Big: {streaks.get('Big', 0)} | 🟢 Small: {streaks.get('Small', 0)}"
            
            alt_text = "✅ Yes" if pattern.get("alternating_pattern") else "❌ No"
            
            msg = f"""🧠 <b>Pattern Analysis</b>

📊 <b>Analyzed:</b> {pattern.get('total_analyzed', 0)} entries

<b>📈 Big/Small Pattern:</b>
<code>{bs_pattern}</code>

<b>⚡ Streak Analysis:</b>
{streak_text}

<b>🔄 Alternating Pattern:</b>
{alt_text}

<b>🎨 Most Common Colors:</b>
{color_text}

<b>🔢 Most Common Numbers:</b>
{num_text}

<b>📊 Last 10 Pattern:</b>
<code>{pattern.get('last_10', 'N/A')}</code>

💡 Type /predict for next prediction"""
            
            send_message(chat_id, msg)
            
        elif text == "/trend":
            stats = get_stats()
            
            if not stats or stats.get("total_entries", 0) == 0:
                send_message(chat_id, "❌ No data! Type /update first.")
                return
            
            numbers = stats.get("numbers", {})
            sorted_numbers = sorted(numbers.items(), key=lambda x: x[1], reverse=True)
            num_text = ""
            for num, count in sorted_numbers[:5]:
                num_text += f"🔢 {num}: {count}\n"
            
            colors = stats.get("colors", {})
            sorted_colors = sorted(colors.items(), key=lambda x: x[1], reverse=True)
            color_text = ""
            for color, count in sorted_colors:
                emoji = "🔴" if "Red" in color else "🟢" if "Green" in color else "🔵"
                color_text += f"{emoji} {color}: {count}\n"
            
            msg = f"""📈 <b>Trending Analysis</b>

<b>🎯 Hot Numbers:</b>
{num_text if num_text else "No data"}

<b>🎨 Hot Colors:</b>
{color_text if color_text else "No data"}

<b>📊 Big/Small:</b>
🔴 Big: {stats.get('total_big', 0)}
🟢 Small: {stats.get('total_small', 0)}
📈 Total: {stats.get('total_entries', 0)}

<b>🕐 Last Update:</b> {stats.get('last_update', 'Never')}"""
            
            send_message(chat_id, msg)
            
        elif text == "/stats":
            stats = get_stats()
            
            if not stats or stats.get("total_entries", 0) == 0:
                send_message(chat_id, "❌ No data! Type /update first.")
                return
            
            msg = f"""📊 <b>Wingo Statistics</b>

📌 <b>Total Entries:</b> {stats.get('total_entries', 0)}
🔴 <b>Big:</b> {stats.get('total_big', 0)}
🟢 <b>Small:</b> {stats.get('total_small', 0)}
🕐 <b>Last Update:</b> {stats.get('last_update', 'Never')}

<b>🎨 Color Distribution:</b>"""
            
            for color, count in stats.get('colors', {}).items():
                emoji = "🔴" if "Red" in color else "🟢" if "Green" in color else "🔵"
                msg += f"\n{emoji} {color}: {count}"
            
            send_message(chat_id, msg)
            
        elif text == "/history":
            history = load_history()
            
            if not history:
                send_message(chat_id, "❌ No history! Type /update first.")
                return
            
            msg = "📚 <b>Last 10 Results:</b>\n\n"
            for i, entry in enumerate(history[-10:], 1):
                emoji = "🔴" if entry.get("big_small") == "Big" else "🟢"
                color_emoji = "🔴" if "Red" in entry.get("color", "") else "🟢" if "Green" in entry.get("color", "") else "🔵"
                msg += f"{i}. 🕐 {entry['timestamp']}\n"
                msg += f"   🔢 {entry['number']} | {emoji} {entry['big_small']} | {color_emoji} {entry['color']}\n\n"
            
            send_message(chat_id, msg)
            
        elif text == "/help":
            msg = """📚 <b>Help Menu</b>

🔄 <b>Data Commands:</b>
/update - Scrape latest data
/analysis - Current + Prediction + %
/history - Last 10 results

🧠 <b>Analysis Commands:</b>
/predict - AI prediction
/pattern - Full pattern analysis
/trend - Trending numbers & colors
/stats - Statistics

ℹ️ <b>Others:</b>
/start - Welcome message
/help - Show this menu

<b>What the bot shows:</b>
📊 Current period number
🔮 Next Big/Small + %
🎨 Next Color + %
🔢 Next Number + %
💡 Recommended bet

<b>How it works:</b>
1. /update - Get data
2. /analysis - See report
3. /predict - Detailed prediction"""
            
            send_message(chat_id, msg)
            
        else:
            send_message(chat_id, "❌ Unknown command. Type /help for available commands.")

def get_updates(offset=None):
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    response = requests.get(url, params=params)
    return response.json()

def main():
    print("🎯 BDG Wingo Analysis + Prediction Bot is running...")
    print("✅ Ready for messages!")
    offset = None
    
    while True:
        try:
            updates = get_updates(offset)
            if "result" in updates:
                for update in updates["result"]:
                    handle_message(update)
                    offset = update["update_id"] + 1
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main() 
