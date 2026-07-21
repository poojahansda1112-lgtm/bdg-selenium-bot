import requests
import time
import datetime
import os
import sys

# 🔑 YOUR BOT TOKEN
BOT_TOKEN = "8706798782:AAEUti6Qh6MApG2GrHXX8GaXbGqRuj7Nz_M"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"✅ Sent: {r.status_code}")
        return r
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_updates(offset=None):
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json()
    except Exception as e:
        print(f"❌ Get updates error: {e}")
        return {"result": []}

def process_message(chat_id, text):
    if text == "/start":
        return """🎯 Bot is working! ✅

📌 Commands:
/ping - Check bot
/time - Current time
/help - Help menu
/about - About bot

🤖 24/7 Running!"""
    elif text == "/ping":
        return "🏓 Pong! Bot is alive! ✅"
    elif text == "/time":
        return f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elif text == "/help":
        return """📚 Help Menu

/ping - Check bot
/time - Current time
/start - Welcome
/about - About bot
/help - This menu"""
    elif text == "/about":
        return """🤖 About Bot

📌 Name: JA CLUB KING BOT
🔑 Version: 1.0.0
✅ Status: Active
🔄 Mode: Polling (No Webhook)
💻 24/7 Running"""
    else:
        return f"📨 You said: {text}\n\nType /help"

def main():
    print("🤖 Bot is running (Polling mode)...")
    print("✅ No webhook required!")
    print("✅ 24/7 mode enabled!")
    print(f"🔑 Token: {BOT_TOKEN[:10]}...")
    
    offset = None
    last_error = 0
    
    while True:
        try:
            updates = get_updates(offset)
            
            if "result" in updates:
                for update in updates["result"]:
                    if "message" in update:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"].get("text", "")
                        
                        print(f"📨 Received: {text} from {chat_id}")
                        
                        reply = process_message(chat_id, text)
                        send_message(chat_id, reply)
                        
                        offset = update["update_id"] + 1
            
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Auto-restart on crash
    while True:
        try:
            main()
        except Exception as e:
            print(f"❌ Bot crashed: {e}")
            print("🔄 Restarting in 10 seconds...")
            time.sleep(10) 
