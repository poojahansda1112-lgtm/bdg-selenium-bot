from flask import Flask, request, jsonify
import requests
import time
import os
import threading
from datetime import datetime

app = Flask(__name__)

# 🔑 YOUR BOT TOKEN
BOT_TOKEN = "8938863154:AAGByeSmRCAPg35if4hwFdhRis-55nibq5I"

# ==================== DATA STORAGE ====================

# In-memory storage (bot restart pe data reset ho jayega)
# For permanent storage, use JSON files or database
user_data = {}
message_count = 0
start_time = datetime.now()

# ==================== TELEGRAM FUNCTIONS ====================

def send_message(chat_id, text):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"✅ Sent to {chat_id}: {r.status_code}")
        return r
    except Exception as e:
        print(f"❌ Error sending: {e}")
        return None

def send_typing(chat_id):
    """Show typing indicator"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
    payload = {"chat_id": chat_id, "action": "typing"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

# ==================== COMMAND HANDLERS ====================

def handle_start(chat_id):
    msg = """🎯 <b>BDG Prediction Bot</b> ✅

📌 <b>Available Commands:</b>
/ping - Check bot status
/time - Current server time
/help - Help menu
/update - Update data
/stats - Bot statistics

✅ Bot is running 24/7!"""
    return msg

def handle_ping(chat_id):
    uptime = datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    return f"""🏓 <b>Pong!</b>

✅ Bot is alive!
🕐 Uptime: {hours}h {minutes}m
📊 Total messages: {message_count}"""

def handle_time(chat_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"🕐 <b>Server Time:</b> {now}"

def handle_help(chat_id):
    return """📚 <b>Help Menu</b>

/ping - Check bot status
/time - Current server time
/update - Update data
/stats - Bot statistics
/start - Welcome message
/help - This menu

🤖 Bot runs 24/7!"""

def handle_update(chat_id):
    return """✅ <b>Data Updated!</b>

📊 Sample data added:
🔢 2 | Small | Red
🔢 5 | Big | Green
🔢 3 | Small | Green

📈 Total: 10 entries
🕐 Updated at: """ + datetime.now().strftime("%H:%M:%S")

def handle_stats(chat_id):
    uptime = datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    return f"""📊 <b>Bot Statistics</b>

📌 Total Messages: {message_count}
🕐 Uptime: {hours}h {minutes}m
🤖 Status: Active
🚀 24/7 Running"""

# ==================== MAIN HANDLER ====================

def process_message(chat_id, text):
    """Process incoming messages"""
    global message_count
    message_count += 1
    
    # Send typing indicator
    send_typing(chat_id)
    
    # Small delay for natural feel
    time.sleep(0.5)
    
    # Handle commands
    if text == "/start":
        reply = handle_start(chat_id)
    elif text == "/ping":
        reply = handle_ping(chat_id)
    elif text == "/time":
        reply = handle_time(chat_id)
    elif text == "/help":
        reply = handle_help(chat_id)
    elif text == "/update":
        reply = handle_update(chat_id)
    elif text == "/stats":
        reply = handle_stats(chat_id)
    else:
        reply = f"📨 You said: <b>{text}</b>\n\nType /help for commands."
    
    return reply

# ==================== FLASK ROUTES ====================

@app.route('/')
def home():
    return "🤖 BDG Prediction Bot is running 24/7!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"📨 Received: {data}")
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            
            # Process message
            reply = process_message(chat_id, text)
            
            # Send reply
            send_message(chat_id, reply)
            
            return jsonify({"status": "ok"})
        
        return jsonify({"status": "no message"})
        
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return jsonify({"status": "error"}), 500

# ==================== KEEP-ALIVE FUNCTION ====================

def keep_alive():
    """Keep the bot alive by logging status"""
    while True:
        print(f"💚 Bot is alive! Messages: {message_count}")
        time.sleep(60)  # Every minute

# ==================== MAIN ====================

if __name__ == "__main__":
    print("🤖 BDG Prediction Bot is starting...")
    print(f"🔑 Token: {BOT_TOKEN[:10]}...")
    print("✅ 24/7 mode enabled!")
    
    # Start keep-alive thread
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    
    app.run(host="0.0.0.0", port=8080, debug=False) 
