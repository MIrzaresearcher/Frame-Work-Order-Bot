import requests
from bs4 import BeautifulSoup
import os
import re

# Configuration
LOGIN_URL = "https://marketplace.nupco.com/market/marketplace/en/login"
ORDERS_URL = "https://marketplace.nupco.com/market/marketplace/en/vendor/framework/orders"
USERNAME = os.getenv("NUPCO_USER")
PASSWORD = os.getenv("NUPCO_PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FILE_NAME = "last_orders.txt"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def scrape_with_login():
    # Use a session to keep cookies active between login and scraping
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    })

    try:
        # 1. Get the login page first to handle any CSRF tokens if they exist
        login_page = session.get(LOGIN_URL)
        
        # 2. Perform the Login
        # Note: 'j_username' and 'j_password' are standard for many enterprise portals,
        # but these field names might need adjustment based on NUPCO's specific form tags.
        payload = {
            'j_username': USERNAME,
            'j_password': PASSWORD,
            '_spring_security_remember
