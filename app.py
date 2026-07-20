from playwright.sync_api import sync_playwright
from flask import Flask, jsonify
import time

app = Flask(__name__)

def scrape_bdgdu():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            
            print("🌐 Loading website...")
            page.goto("http://bdgdu.com/#/", timeout=60000)
            page.wait_for_timeout(8000)
            
            title = page.title()
            links = page.eval_on_selector_all('a', 'els => els.map(el => el.href)')
            body_text = page.inner_text('body')
            
            browser.close()
            
            return {
                "success": True,
                "title": title,
                "total_links": len(links),
                "links": links[:20],
                "body_preview": body_text[:500]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.route('/')
def home():
    return "<h1>🚀 BDGDU Scraper API</h1><p>/scrape pe data milega</p>"

@app.route('/scrape')
def get_data():
    return jsonify(scrape_bdgdu())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 
