from flask import Flask, request, jsonify
import requests
import json
import time
import os
from datetime import datetime
from collections import Counter
import random

app = Flask(__name__)

# 🔑 Bot Token
BOT_TOKEN = "8706584781:AAGRh9gFNu6RbsuS5v9t076N9se2WGon4YI"

# 📁 File paths
HISTORY_FILE = "wingo_history.json"
STATS_FILE = "stats.json"
PATTERN_FILE = "pattern_analysis.json"
CURRENT_FILE = "current_data.json"

# ==================== DATA FUNCTIONS ====================

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
    
    bs_pattern = [h.get("big_small") for h in last_15]
    big_count = bs_pattern.count("Big")
    small_count = bs_pattern.count("Small")
    
    recent_bs = [h.get("big_small") for h in last_5]
    recent_big = recent_bs.count("Big")
    recent_small = recent_bs.count("Small")
    
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
    
    color_pattern = [h.get("color") for h in last_15]
    color_counts = Counter(color_pattern)
    pred_color = color_counts.most_common(1)[0][0] if color_counts else "Red"
    color_conf = round((color_counts[pred_color] / len(color_pattern)) * 100, 1)
    
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

def add_sample_data():
    """Add sample data for testing"""
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
    
    history = load_history()
    if not history:
        for data in sample_data:
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "period": data["period"],
                "number": data["number"],
                "big_small": data["big_small"],
                "color": data["color"],
                "game_type": "Wingo 1Min"
            }
            save_history(entry)
            save_current({
                "period": data["period"],
                "number": data["number"],
                "big_small": data["big_small"],
                "color": data["color"]
            })

# ==================== TELEGRAM FUNCTIONS ====================

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload)
        print(f"✅ Sent: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def make_prediction(history):
    """Make prediction based on history"""
    if len(history) < 5:
        return {"big_small": "Not enough data", "color": "Not enough data", "number": "Not enough data"}
    
    last_15 = history[-15:]
    last_5 = history[-5:]
    
    # Big/Small
    bs_pattern = [h.get("big_small") for h in last_15]
    big_count = bs_pattern.count("Big")
    small_count = bs_pattern.count("Small")
    
    recent_bs = [h.get("big_small") for h in last_5]
    recent_big = recent_bs.count("Big")
    recent_small = recent_bs.count("Small")
    
    big_score = big_count * 0.6 + recent_big * 0.4
    small_score = small_count * 0.6 + recent_small * 0.4
    
    if big_score > small_score:
        bs_pred = "Big"
        bs_conf = round((big_score / (big_score + small_score)) * 100, 1)
    else:
        bs_pred = "Small"
        bs_conf = round((small_score / (big_score + small_score)) * 100, 1)
    
    # Color
    color_pattern = [h.get("color") for h in last_15]
    color_counts = Counter(color_pattern)
    pred_color = color_counts.most_common(1)[0][0] if color_counts else "Red"
    color_conf = round((color_counts[pred_color] / len(color_pattern)) * 100, 1)
    
    # Number
    number_pattern = [h.get("number", 0) for h in last_15 if h.get("number", 0) > 0]
    if number_pattern:
        num_counts = Counter(number_pattern)
        pred_number = num_counts.most_common(1)[0][0] if num_counts else 0
    else:
        pred_number = 0
    
    return {
        "big_small": {"prediction": bs_pred, "confidence": bs_conf},
        "color": {"prediction": pred_color, "confidence": color_conf},
        "number": {"prediction": pred_number}
    }

def confidence_bar(percent):
    filled = int(percent / 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty

# ==================== FLASK ROUTES ====================

@app.route('/')
def home():
    return "🤖 BDG Wingo Prediction Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"📨 Received: {data}")
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            
            # ========== /start ==========
            if text == "/start":
                msg = """🎯 <b>BDG Wingo Prediction Bot</b> ✅

📌 <b>All Commands:</b>

🔄 <b>Data Commands:</b>
/update - Scrape latest Wingo data
/analysis - Current period + Prediction + %
/history - Last 10 results

🧠 <b>Analysis Commands:</b>
/predict - AI prediction
/pattern - Full pattern analysis
/trend - Trending numbers & colors
/stats - Statistics

ℹ️ <b>Others:</b>
/start - Welcome message
/help - Show this menu

🔹 Made with ❤️"""
                send_message(chat_id, msg)
            
            # ========== /help ==========
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
💡 Recommended bet"""
                send_message(chat_id, msg)
            
            # ========== /ping ==========
            elif text == "/ping":
                msg = "🏓 Pong! Bot is alive! ✅"
                send_message(chat_id, msg)
            
            # ========== /time ==========
            elif text == "/time":
                msg = f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                send_message(chat_id, msg)
            
            # ========== /update ==========
            elif text == "/update":
                send_message(chat_id, "⏳ Adding sample data...")
                add_sample_data()
                current = get_current()
                pattern = get_pattern_analysis()
                next_pred = pattern.get("current_prediction", {}) if pattern else {}
                
                if current:
                    bs_emoji = "🔴" if current.get("big_small") == "Big" else "🟢"
                    color_emoji = "🔴" if "Red" in current.get("color", "") else "🟢" if "Green" in current.get("color", "") else "🔵"
                    next_bs = next_pred.get("big_small", {}).get("prediction", "N/A")
                    next_bs_emoji = "🔴" if next_bs == "Big" else "🟢"
                    next_color = next_pred.get("color", {}).get("prediction", "N/A")
                    next_color_emoji = "🔴" if next_color == "Red" else "🟢" if next_color == "Green" else "🔵"
                    next_num = next_pred.get("number", {}).get("prediction", "N/A")
                    bs_conf = next_pred.get("big_small", {}).get("confidence", 0)
                    
                    msg = f"""✅ <b>Data Updated!</b>

📊 <b>Current Period:</b>
🕐 <code>{current.get('period', 'N/A')}</code>
🔢 {current.get('number', 'N/A')} | {bs_emoji} {current.get('big_small', 'N/A')} | {color_emoji} {current.get('color', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━

<b>🔮 Next Prediction:</b>
{next_bs_emoji} <b>{next_bs}</b> ({bs_conf}%) | {next_color_emoji} <b>{next_color}</b> | 🔢 <b>{next_num}</b>

💡 <b>Recommended:</b> {next_pred.get('recommended', 'N/A')}

📈 <b>Total Entries:</b> {len(load_history())}

🤖 Type /analysis for detailed report"""
                else:
                    msg = "❌ Failed to add sample data"
                send_message(chat_id, msg)
            
            # ========== /analysis ==========
            elif text == "/analysis":
                current = get_current()
                pattern = get_pattern_analysis()
                
                if not current:
                    send_message(chat_id, "❌ No data! Type /update first.")
                    return
                
                next_pred = pattern.get("current_prediction", {}) if pattern else {}
                
                bs_emoji = "🔴" if current.get("big_small") == "Big" else "🟢"
                color_emoji = "🔴" if "Red" in current.get("color", "") else "🟢" if "Green" in current.get("color", "") else "🔵"
                
                next_bs = next_pred.get("big_small", {}).get("prediction", "N/A")
                next_bs_emoji = "🔴" if next_bs == "Big" else "🟢"
                next_color = next_pred.get("color", {}).get("prediction", "N/A")
                next_color_emoji = "🔴" if next_color == "Red" else "🟢" if next_color == "Green" else "🔵"
                next_num = next_pred.get("number", {}).get("prediction", "N/A")
                
                bs_conf = next_pred.get("big_small", {}).get("confidence", 0)
                color_conf = next_pred.get("color", {}).get("confidence", 0)
                num_conf = next_pred.get("number", {}).get("confidence", 0)
                
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

📊 <b>Based on:</b> {pattern.get('total_analyzed', 0) if pattern else 0} entries"""
                send_message(chat_id, msg)
            
            # ========== /predict ==========
            elif text == "/predict":
                pattern = get_pattern_analysis()
                if not pattern:
                    send_message(chat_id, "❌ No data! Type /update first.")
                    return
                
                prediction = pattern.get("current_prediction", {})
                bs = prediction.get("big_small", {})
                color = prediction.get("color", {})
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
🔴 <b>{bs.get('prediction', 'N/A')}</b>
📈 Chance: <b>{bs.get('confidence', 0)}%</b>

🎨 <b>Color:</b>
🔴 <b>{color.get('prediction', 'N/A')}</b>
📈 Chance: <b>{color.get('confidence', 0)}%</b>

🔢 <b>Number:</b>
🎯 <b>{number.get('prediction', 'N/A')}</b>

💡 <b>Recommended:</b> {prediction.get('recommended', 'N/A')}"""
                send_message(chat_id, msg)
            
            # ========== /pattern ==========
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
                
                msg = f"""🧠 <b>Pattern Analysis</b>

📊 <b>Analyzed:</b> {pattern.get('total_analyzed', 0)} entries

<b>📈 Pattern:</b>
<code>{bs_pattern}</code>

<b>⚡ Streaks:</b>
{streak_text}

<b>🎨 Common Colors:</b>
{color_text}

<b>🔢 Common Numbers:</b>
{num_text}

<b>📊 Last 10:</b>
<code>{pattern.get('last_10', 'N/A')}</code>"""
                send_message(chat_id, msg)
            
            # ========== /trend ==========
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
{num_text}

<b>🎨 Hot Colors:</b>
{color_text}

<b>📊 Big/Small:</b>
🔴 Big: {stats.get('total_big', 0)}
🟢 Small: {stats.get('total_small', 0)}
📈 Total: {stats.get('total_entries', 0)}"""
                send_message(chat_id, msg)
            
            # ========== /stats ==========
            elif text == "/stats":
                stats = get_stats()
                if not stats or stats.get("total_entries", 0) == 0:
                    send_message(chat_id, "❌ No data! Type /update first.")
                    return
                
                msg = f"""📊 <b>Statistics</b>

📌 <b>Total Entries:</b> {stats.get('total_entries', 0)}
🔴 <b>Big:</b> {stats.get('total_big', 0)}
🟢 <b>Small:</b> {stats.get('total_small', 0)}
🕐 <b>Last Update:</b> {stats.get('last_update', 'Never')}

<b>🎨 Color Distribution:</b>"""
                for color, count in stats.get('colors', {}).items():
                    emoji = "🔴" if "Red" in color else "🟢" if "Green" in color else "🔵"
                    msg += f"\n{emoji} {color}: {count}"
                send_message(chat_id, msg)
            
            # ========== /history ==========
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
            
            # ========== Unknown Command ==========
            else:
                msg = f"📨 You said: <b>{text}</b>\n\nType /help for commands."
                send_message(chat_id, msg)
            
            return jsonify({"status": "ok"})
        
        return jsonify({"status": "no message"})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "error": str(e)})

# ==================== MAIN ====================

if __name__ == "__main__":
    print("🎯 BDG Wingo Prediction Bot is running!")
    print("✅ Webhook ready!")
    add_sample_data()
    app.run(host="0.0.0.0", port=8080)
