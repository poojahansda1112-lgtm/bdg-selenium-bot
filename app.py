from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8706584781:AAGRh9gFNu6RbsuS5v9t076N9se2WGon4YI"

def send_message(chat_id, text):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload)
        print(f"✅ Sent: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

@app.route('/')
def home():
    return "🤖 BDG Wingo Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram messages"""
    try:
        data = request.json
        print(f"📨 Received: {data}")
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            
            if text == "/start":
                msg = """🎯 <b>BDG Wingo Bot</b> ✅

📌 <b>Commands:</b>
/ping - Check bot status
/help - Help menu
/time - Current time"""
                
            elif text == "/ping":
                msg = "🏓 Pong! Bot is alive! ✅"
                
            elif text == "/time":
                msg = f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
            elif text == "/help":
                msg = """📚 <b>Commands:</b>
/ping - Check bot status
/time - Current time
/start - Welcome message
/help - This menu"""
                
            else:
                msg = f"📨 You said: <b>{text}</b>\n\nType /help for commands."
            
            send_message(chat_id, msg)
            return jsonify({"status": "ok"})
        
        return jsonify({"status": "no message"})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
