import requests
from bs4 import BeautifulSoup
import os

# Configuration
URL = "https://marketplace.nupco.com/market/marketplace/en/vendor/framework/orders"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FILE_NAME = "last_orders.txt"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def scrape_orders():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        found_orders = []
        # Based on your image, we are looking for links starting with '32'
        for link in soup.find_all('a'):
            order_text = link.text.strip()
            if order_text.startswith('32') and len(order_text) >= 8:
                found_orders.append(order_text)
        
        return list(set(found_orders))
    except Exception as e:
        print(f"Error scraping website: {e}")
        return []

# 1. Load previous Order Numbers
if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "r") as f:
        seen_orders = set(f.read().splitlines())
else:
    seen_orders = set()

# 2. Get current Order Numbers
current_orders = scrape_orders()

# 3. Identify new orders
new_entries = [oid for oid in current_orders if oid not in seen_orders]

if new_entries:
    message = "📦 *New NUPCO Framework Orders!* 📦\n\n" + "\n".join([f"- Order #: {oid}" for oid in new_entries])
    send_telegram_message(message)
    
    # Update the file with the latest list
    with open(FILE_NAME, "w") as f:
        f.write("\n".join(current_orders))
    print(f"Alerted for {len(new_entries)} new orders.")
else:
    print("No new framework orders found.")
