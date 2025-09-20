import os
import json
import base64
import requests
import logging


# Config
TOKEN_FILE = "pinterest_token.json"
BASE_URL = "https://api.pinterest.com/v5"
TOKEN_REFRESH_URL = f"{BASE_URL}/oauth/token"

PINTEREST_APP_ID = os.getenv("PINTEREST_APP_ID")
PINTEREST_APP_SECRET = os.getenv("PINTEREST_APP_SECRET")

# Logging
logger = logging.getLogger("pinterest_auth")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        logger.error("❌ pinterest_token.json not found.")
        raise FileNotFoundError("pinterest_token.json not found.")
    with open(TOKEN_FILE) as f:
        return json.load(f)
    
def get_ad_account_id(access_token):
    """Fetches the user's first ad account ID"""
    url = f"{BASE_URL}/ad_accounts"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        logger.error(f"Failed to create campaign: {resp.status_code} {resp.text}")
        return None
    else:
        logger.info(f"✅ Campaign created successfully: {resp.json()}")

    accounts = resp.json().get("items", [])
    if not accounts:
        logger.error("❌ No ad accounts found for this Pinterest user.")
        raise ValueError("No ad accounts found")

    ad_account_id = accounts[0]["id"]
    logger.info(f"✅ Using Ad Account ID: {ad_account_id}")
    return ad_account_id

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def refresh_access_token():
    tokens = load_tokens()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        logger.error("❌ No refresh_token found in pinterest_token.json")
        raise ValueError("Missing refresh_token")

    creds = f"{PINTEREST_APP_ID}:{PINTEREST_APP_SECRET}"
    b64creds = base64.b64encode(creds.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64creds}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    logger.info("🔄 Refreshing Pinterest access token...")
    resp = requests.post(TOKEN_REFRESH_URL, headers=headers, data=data)

    if resp.ok:
        new_tokens = resp.json()
        tokens.update(new_tokens)
        save_tokens(tokens)
        logger.info("✅ Access token refreshed.")
        return tokens["access_token"]
    else:
        logger.error(f"❌ Failed to refresh access token: {resp.text}")
        raise RuntimeError(f"Failed to refresh access token: {resp.text}")


def get_access_token():
    tokens = load_tokens()
    access_token = tokens.get("access_token")
    if not access_token:
        raise ValueError("❌ No access_token in token file")

    headers = {"Authorization": f"Bearer {access_token}"}
    test_resp = requests.get(f"{BASE_URL}/user_account", headers=headers)

    if test_resp.status_code == 401:
        logger.warning("⚠️ Access token expired, refreshing...")
        return refresh_access_token()
    return access_token
