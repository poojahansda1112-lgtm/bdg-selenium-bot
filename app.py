from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 🔑 Your Bot Token
BOT_TOKEN = "8938863154:AAGByeSmRCAPg35if4hwFdhRis-55nibq5I"

def send_message(chat_id, text):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, json=payload)
        print(f"✅ Sent: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"📨 Received: {data}")
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            
            # Reply with same text
            reply = f"✅ Bot is working! You said: {text}"
            send_message(chat_id, reply)
            
            return jsonify({"status": "ok"})
        
        return jsonify({"status": "no message"})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error"})

if __name__ == "__main__":
    print("🤖 Bot is starting...")
    app.run(host="0.0.0.0", port=8080) 
