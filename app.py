from playwright.sync_api import sync_playwright
import requests
import time
import re

# 🔑 NEW BOT TOKEN
BOT_TOKEN = "8938863154:AAGByeSmRCAPg35if4hwFdhRis-55nibq5I"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def scrape_bdgdu():
    """Scrape data from bdgdu.com"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            
            page.goto("http://bdgdu.com/#/", timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            title = page.title()
            links = page.eval_on_selector_all('a', 'els => els.map(el => el.href)')
            
            game_data = []
            try:
                elements = page.query_selector_all('[class*="game"], [class*="result"], [class*="color"], [class*="number"]')
                for el in elements[:20]:
                    text = el.inner_text()
                    if text.strip():
                        game_data.append(text)
            except:
                pass
            
            body_text = page.inner_text('body')
            browser.close()
            
            return {
                "success": True,
                "title": title,
                "links_count": len(links),
                "links": links[:10],
                "game_data": game_data[:10],
                "body_preview": body_text[:500]
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_message(chat_id, text):
    """Send message to Telegram"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

def handle_message(update):
    """Handle incoming messages"""
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")
        
        if text == "/start":
            msg = """🤖 <b>BDGDU Scraper Bot</b>
            
📌 <b>Commands:</b>
/scrape - Get latest data
/links - Get all links
/game - Get game data
/help - Show this message

🔹 Made with ❤️"""
            send_message(chat_id, msg)
            
        elif text == "/scrape":
            send_message(chat_id, "⏳ Scraping in progress...")
            data = scrape_bdgdu()
            
            if data["success"]:
                msg = f"""✅ <b>Scraping Complete!</b>
                
📌 <b>Title:</b> {data['title']}
🔗 <b>Links Found:</b> {data['links_count']}
📝 <b>Preview:</b> {data['body_preview'][:200]}...

<a href="https://bdgdu.com">Visit Website</a>"""
            else:
                msg = f"❌ Error: {data['error']}"
            
            send_message(chat_id, msg)
            
        elif text == "/links":
            send_message(chat_id, "⏳ Fetching links...")
            data = scrape_bdgdu()
            
            if data["success"] and data["links"]:
                links_text = "\n".join([f"🔗 {link}" for link in data["links"][:10]])
                msg = f"<b>Links:</b>\n{links_text}"
            else:
                msg = "❌ No links found or error occurred"
            
            send_message(chat_id, msg)
            
        elif text == "/game":
            send_message(chat_id, "⏳ Fetching game data...")
            data = scrape_bdgdu()
            
            if data["success"] and data["game_data"]:
                game_text = "\n".join([f"🎯 {item}" for item in data["game_data"]])
                msg = f"<b>Game Data:</b>\n{game_text}"
            else:
                msg = "❌ No game data found"
            
            send_message(chat_id, msg)
            
        elif text == "/help":
            msg = """📚 <b>Help Menu</b>

/scrape - Get complete scraped data
/links - Get all links from page
/game - Get game related data
/start - Show welcome message
/help - Show this menu

<b>Developer:</b> @YourUsername"""
            send_message(chat_id, msg)
            
        else:
            send_message(chat_id, "❌ Unknown command. Type /help for available commands.")

def get_updates(offset=None):
    """Get new messages from Telegram"""
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    
    response = requests.get(url, params=params)
    return response.json()

def main():
    """Main bot loop"""
    print("🤖 Bot is running...")
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
