import requests
from bs4 import BeautifulSoup
import os

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
    """Scrapes the NUPCO Marketplace using the session cookie."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Cookie': NUPCO_COOKIE,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://marketplace.nupco.com/'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        # Debugging: This helps you see if you are being redirected to login
        if "login" in response.url.lower():
            print("⚠️ Error: The cookie expired or is invalid. Redirected to login page.")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        found_orders = []
        # Finding all links. Per your screenshot, order numbers are 32000...
        for link in soup.find_all('a'):
            order_text = link.text.strip()
            # Logic: Must start with '32' and be at least 8 digits long
            if order_text.startswith('32') and len(order_text) >= 8:
                found_orders.append(order_text)
        
        return list(set(found_orders))
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

# --- MAIN EXECUTION ---

# 1. Load previous IDs to avoid duplicate alerts
if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "r") as f:
        # Filter out '0' which was our placeholder
        seen_orders = set(line.strip() for line in f if line.strip() != '0')
else:
    seen_orders = set()

# 2. Scrape the current marketplace
current_orders = scrape_orders()

# 3. Identify only the new orders
new_entries = [oid for oid in current_orders if oid not in seen_orders]

# 4. Handle results
if new_entries:
    # Build the Telegram alert
    message = "📦 *New NUPCO Framework Orders Found!* 📦\n\n"
    message += "\n".join([f"• `{oid}`" for oid in sorted(new_entries, reverse=True)])
    
    send_telegram_message(message)
    
    # Save the updated list back to the file for next time
    with open(FILE_NAME, "w") as f:
        f.write("\n".join(current_orders))
    print(f"Success! {len(new_entries)} new orders sent to Telegram.")
else:
    print("No new orders found at this time.")
