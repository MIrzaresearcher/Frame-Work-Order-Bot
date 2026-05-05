import requests
from bs4 import BeautifulSoup
import os
import time
import re  # This was likely missing and caused the error

# Configuration
URL = "https://marketplace.nupco.com/market/marketplace/en/vendor/framework/orders"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NUPCO_COOKIE = os.getenv("NUPCO_COOKIE")
FILE_NAME = "last_orders.txt"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def scrape_orders():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Cookie': NUPCO_COOKIE,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://marketplace.nupco.com/',
    }
    
    for attempt in range(3):
        try:
            print(f"Attempt {attempt + 1}: Connecting...")
            response = requests.get(URL, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Using Regex to find any 10-digit number starting with 32
                # This works even if the table is formatted strangely
                raw_text = response.text
                found_ids = re.findall(r'32\d{8}', raw_text)
                
                # If we found something, return it
                if found_ids:
                    return list(set(found_ids))
                
                # If page loaded but no IDs found, might be a login redirect
                if "login" in raw_text.lower() or "sign in" in raw_text.lower():
                    print("Session expired. Bot sees login page.")
                    return []
                    
            print(f"Status {response.status_code} on attempt {attempt+1}")
        except Exception as e:
            print(f"Error on attempt {attempt+1}: {e}")
            time.sleep(5)
                
    return []

# --- MAIN EXECUTION ---

# 1. Get current IDs
current_orders = scrape_orders()

# 2. Debug Alert: If absolutely nothing was found
if not current_orders:
    send_telegram_message("⚠️ *Scraper Alert:* No orders found. Please check if your `NUPCO_COOKIE` secret is updated or if the Marketplace is down.")
    print("Sent debug alert.")

# 3. Normal Comparison Logic
if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "r") as f:
        seen_orders = set(line.strip() for line in f if line.strip() != '0')
else:
    seen_orders = set()

# Find IDs that are in current_orders but NOT in seen_orders
new_entries = [oid for oid in current_orders if oid not in seen_orders]

if new_entries:
    message = "📦 *New NUPCO Orders Found!* 📦\n\n" + "\n".join([f"- `{oid}`" for oid in sorted(new_entries)])
    send_telegram_message(message)
    
    # Save ALL current IDs to the file for next time
    with open(FILE_NAME, "w") as f:
        f.write("\n".join(current_orders))
    print(f"Sent {len(new_entries)} new orders to Telegram.")
else:
    print("No new orders to report.")
