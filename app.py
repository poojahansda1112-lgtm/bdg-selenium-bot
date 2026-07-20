from playwright.sync_api import sync_playwright
from flask import Flask, jsonify
import time
import re

app = Flask(__name__)

def scrape_bdgdu():
    """Scrape all data from bdgdu.com"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            page = browser.new_page()
            
            print("🌐 Loading website...")
            page.goto("http://bdgdu.com/#/", timeout=60000)
            
            # Wait for JavaScript to fully load
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(5)
            
            print("✅ Page loaded, extracting data...")
            
            # 1. Page title
            title = page.title()
            
            # 2. All links
            links = page.eval_on_selector_all('a', 'els => els.map(el => el.href)')
            
            # 3. All images
            images = page.eval_on_selector_all('img', 'els => els.map(el => el.src)')
            
            # 4. All buttons
            buttons = page.eval_on_selector_all('button', 'els => els.map(el => el.innerText)')
            
            # 5. All divs with text
            all_divs = page.eval_on_selector_all('div', 'els => els.map(el => el.innerText)')
            
            # 6. All paragraphs
            paragraphs = page.eval_on_selector_all('p', 'els => els.map(el => el.innerText)')
            
            # 7. All headings
            headings = page.eval_on_selector_all('h1, h2, h3, h4, h5, h6', 'els => els.map(el => el.innerText)')
            
            # 8. All spans with text
            spans = page.eval_on_selector_all('span', 'els => els.map(el => el.innerText)')
            
            # 9. All classes containing "game", "result", "color", "number"
            game_data = []
            try:
                # Find elements with game-related classes
                elements = page.query_selector_all('[class*="game"], [class*="result"], [class*="color"], [class*="number"], [class*="score"]')
                for el in elements[:50]:
                    text = el.inner_text()
                    if text.strip():
                        game_data.append(text)
            except:
                pass
            
            # 10. Complete HTML
            full_html = page.content()
            
            browser.close()
            
            return {
                "success": True,
                "title": title,
                "total_links": len(links),
                "links": links[:50],
                "images": images[:20],
                "buttons": buttons[:20],
                "headings": headings[:20],
                "paragraphs": paragraphs[:20],
                "divs": all_divs[:30],
                "spans": spans[:30],
                "game_related_data": game_data[:30],
                "body_preview": " ".join(paragraphs)[:1000],
                "html_length": len(full_html)
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.route('/')
def home():
    return """
    <h1>🔄 BDGDU Scraper</h1>
    <ul>
        <li><a href="/scrape">/scrape</a> - Get all data in JSON</li>
        <li><a href="/html">/html</a> - Get full HTML</li>
        <li><a href="/links">/links</a> - Get only links</li>
        <li><a href="/game-data">/game-data</a> - Get game related data</li>
        <li><a href="/text">/text</a> - Get all text</li>
    </ul>
    """

@app.route('/scrape')
def get_data():
    return jsonify(scrape_bdgdu())

@app.route('/html')
def get_html():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page()
            page.goto("http://bdgdu.com/#/", timeout=60000)
            page.wait_for_load_state("networkidle")
            html = page.content()
            browser.close()
        return html
    except Exception as e:
        return f"Error: {e}"

@app.route('/links')
def get_links():
    data = scrape_bdgdu()
    return jsonify(data.get('links', []))

@app.route('/game-data')
def get_game_data():
    data = scrape_bdgdu()
    return jsonify(data.get('game_related_data', []))

@app.route('/text')
def get_text():
    data = scrape_bdgdu()
    return jsonify({
        'title': data.get('title'),
        'headings': data.get('headings'),
        'paragraphs': data.get('paragraphs')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
