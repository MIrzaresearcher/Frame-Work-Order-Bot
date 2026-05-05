import requests
from bs4 import BeautifulSoup
import os
import time

# Configuration
URL = "https://marketplace.nupco.com/market/marketplace/en/vendor/framework/orders"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NUPCO_COOKIE = os.getenv("NUPCO_COOKIE")
FILE_NAME = "last_orders.txt"

def send_telegram_message(message):
    """Sends a notification to your Telegram Bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def scrape_orders():
    """Scrapes the NUPCO Marketplace using the session cookie with retries."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Cookie': NUPCO_COOKIE,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Try up to 3 times to overcome temporary connection timeouts
    for attempt in range(3):
        try:
            print(f"Attempt {attempt + 1}: Connecting to NUPCO...")
            response = requests.get(URL, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("Connection Successful!")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                found_orders = []
                # Finding all links starting with '32' (Order Number pattern)
                for link in soup.find_all('a'):
                    order_text = link.text.strip()
                    if order_text.startswith('32') and len(order_text) >= 8:
                        found_orders.append(order_text)
                return list(set(found_orders))
            else:
                print(f"Server returned status: {response.status_code}")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(5) # Wait before retrying
                
    return []

# --- MAIN EXECUTION ---

# 1. Get current IDs
current_orders = scrape_orders()

# 2. TEST: Force a message if current_orders is empty
if not current_orders:
    send_telegram_message("⚠️ *Debug Note:* The scraper connected to NUPCO but found 0 orders. This usually means the Session Cookie expired or the page structure changed.")
    print("Sent Debug message to Telegram.")

# 3. Normal Logic
if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "r") as f:
        # Filter out '0' which was our placeholder
        seen_orders = set(line.strip() for line in f if line.strip() != '0')
else:
    seen_orders = set()

# Identify only the new orders
new_entries = [oid for oid in current_orders if oid not in seen_orders]

if new_entries:
    message = "📦 *New NUPCO Orders Found!* 📦\n\n" + "\n".join([f"- `{oid}`" for oid in sorted(new_entries, reverse=True)])
    send_telegram_message(message)
    
    # Update the file with the latest list
    with open(FILE_NAME, "w") as f:
        f.write("\n".join(current_orders))
    print(f"Success! {len(new_entries)} new orders sent to Telegram.")
else:
    print("No new orders found at this time.")
