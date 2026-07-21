import requests
import time
import datetime
import os
import sys
import threading
import json
from flask import Flask

app = Flask(__name__)

# 🔑 BOT TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8706798782:AAEUti6Qh6MApG2GrHXX8GaXbGqRuj7Nz_M")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 📁 Data files
WINGO_DATA_FILE = "wingo_data.json"
WINGO_HISTORY_FILE = "wingo_history.json"

# ==================== SCRAPE WINGO 1MIN ====================

def scrape_wingo_1min():
    """Scrape Wingo 1Min game history from bdgdu.com"""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            page.goto("http://bdgdu.com/#/", timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # Click on "Win Go 1Min" tab
            try:
                # Find and click the element with text "Win Go 1Min"
                wingo_tab = page.locator("text=Win Go 1Min").first
                wingo_tab.click()
                time.sleep(2)
                print("✅ Clicked on Win Go 1Min")
            except Exception as e:
                print(f"⚠️ Could not click Win Go 1Min: {e}")
                # Try alternative selector
                try:
                    wingo_tab = page.locator("a:has-text('Win Go 1Min')").first
                    wingo_tab.click()
                    time.sleep(2)
                except:
                    pass
            
            # Wait for table to load
            page.wait_for_selector("table tbody tr", timeout=10000)
            time.sleep(2)
            
            # Extract table data
            rows = page.query_selector_all("table tbody tr")
            table_data = []
            
            for row in rows:
                cells = row.query_selector_all("td")
                if len(cells) >= 4:
                    period = cells[0].inner_text().strip()
                    number = cells[1].inner_text().strip()
                    big_small = cells[2].inner_text().strip()
                    color = cells[3].inner_text().strip()
                    
                    table_data.append({
                        "period": period,
                        "number": int(number) if number.isdigit() else 0,
                        "big_small": big_small,
                        "color": color
                    })
            
            browser.close()
            
            # Prepare data structure
            data = {
                "success": True,
                "game": "Wingo 1Min",
                "entries": table_data,
                "count": len(table_data),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Save current data
            with open(WINGO_DATA_FILE, "w") as f:
                json.dump(data, f, indent=2)
            
            # Save history
            save_wingo_history(table_data)
            
            return data
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def save_wingo_history(entries):
    """Save Wingo history with timestamp"""
    history = []
    if os.path.exists(WINGO_HISTORY_FILE):
        with open(WINGO_HISTORY_FILE, "r") as f:
            history = json.load(f)
    
    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "count": len(entries),
        "first_entry": entries[0] if entries else None,
        "last_entry": entries[-1] if entries else None
    })
    
    if len(history) > 50:
        history = history[-50:]
    
    with open(WINGO_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def load_wingo_data():
    if os.path.exists(WINGO_DATA_FILE):
        with open(WINGO_DATA_FILE, "r") as f:
            return json.load(f)
    return None

# ==================== TELEGRAM FUNCTIONS ====================

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
        return """🎯 JA CLUB KING BOT ✅

📌 Commands:
/ping - Check bot
/time - Current time
/wingo - Scrape Wingo 1Min data
/show - Show last Wingo data
/wingohistory - Show Wingo scrape history
/help - Help menu
/about - About bot

🤖 24/7 Running!"""
    
    elif text == "/ping":
        return "🏓 Pong! Bot is alive! ✅"
    
    elif text == "/time":
        return f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    elif text == "/wingo":
        send_message(chat_id, "⏳ Scraping Wingo 1Min data...")
        data = scrape_wingo_1min()
        if data["success"]:
            entries = data.get("entries", [])
            # Show first 5 entries as preview
            preview = "\n".join([f"  {e['period']} | {e['number']} | {e['big_small']} | {e['color']}" for e in entries[:5]])
            return f"""✅ Wingo 1Min Scraped!

📊 Total Entries: {len(entries)}
🕐 Time: {data['timestamp']}

📋 Last 5 Entries:
{preview}

💾 Data stored!
📁 Type /show to view all"""
        else:
            return f"❌ Error: {data['error']}"
    
    elif text == "/show":
        data = load_wingo_data()
        if data and data.get("success"):
            entries = data.get("entries", [])
            if not entries:
                return "❌ No entries found."
            preview = "\n".join([f"  {e['period']} | {e['number']} | {e['big_small']} | {e['color']}" for e in entries[:10]])
            return f"""📊 Wingo 1Min Data

📌 Total Entries: {len(entries)}
🕐 Scraped: {data.get('timestamp', 'N/A')}

📋 First 10 Entries:
{preview}"""
        else:
            return "❌ No Wingo data! Type /wingo first."
    
    elif text == "/wingohistory":
        if os.path.exists(WINGO_HISTORY_FILE):
            with open(WINGO_HISTORY_FILE, "r") as f:
                history = json.load(f)
            if not history:
                return "❌ No history! Type /wingo first."
            msg = f"📚 Wingo Scrape History (Last 10)\n📊 Total: {len(history)}\n"
            for i, entry in enumerate(history[-10:], 1):
                msg += f"\n{i}. 🕐 {entry.get('timestamp', 'N/A')[:16]}\n   📊 Entries: {entry.get('count', 0)}"
            return msg
        else:
            return "❌ No history! Type /wingo first."
    
    elif text == "/help":
        return """📚 Help Menu

/wingo - Scrape Wingo 1Min data
/show - Show last Wingo data
/wingohistory - Show Wingo scrape history
/ping - Check bot
/time - Current time
/start - Welcome
/about - About bot
/help - This menu"""
    
    elif text == "/about":
        return """🤖 About Bot

📌 Name: JA CLUB KING BOT
🔑 Version: 3.0.0
✅ Status: Active
🔄 Mode: Polling (No Webhook)
💻 24/7 Running
🕷️ Scraping: Wingo 1Min"""
    
    else:
        return f"📨 You said: {text}\n\nType /help"

# ==================== POLLING LOOP ====================

def polling_loop():
    print("🤖 Polling thread started...")
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
            print(f"❌ Polling error: {e}")
            time.sleep(5)

# ==================== FLASK SERVER ====================

@app.route('/')
def home():
    return "JA CLUB KING BOT is running! ✅"

if __name__ == "__main__":
    print("🤖 JA CLUB KING BOT starting...")
    print("✅ Polling + Flask server + Wingo Scrape mode")
    
    # Start polling thread
    thread = threading.Thread(target=polling_loop, daemon=True)
    thread.start()
    
    # Run Flask server
    port = int(os.environ.get("PORT", 8080))
    print(f"✅ Flask server running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False) 
