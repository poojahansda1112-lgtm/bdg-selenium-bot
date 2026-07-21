import requests
import time
import datetime

# 🔑 YOUR BOT TOKEN
BOT_TOKEN = "8962862907:AAGn5lqXmh7Rcn9Kksz81oQyETnJDyF3d4w"
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
        return "🎯 Bot is working! ✅\n\nCommands:\n/ping - Check bot\n/time - Current time\n/help - Help menu"
    elif text == "/ping":
        return "🏓 Pong! Bot is alive! ✅"
    elif text == "/time":
        return f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elif text == "/help":
        return """📚 Help Menu

/ping - Check bot
/time - Current time
/start - Welcome
/help - This menu"""
    else:
        return f"📨 You said: {text}\n\nType /help"

def main():
    print("🤖 Bot is running (Polling mode)...")
    print("✅ No webhook required!")
    offset = None
    
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
    main() 
