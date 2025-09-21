import os
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

SPREADSHEET_ID = os.getenv("SHEET_ID")
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "pinterest_token.json"
PINTEREST_APP_ID = os.getenv("PINTEREST_APP_ID")
PINTEREST_APP_SECRET = os.getenv("PINTEREST_APP_SECRET")

USE_SANDBOX = False
BASE_URL = "https://api-sandbox.pinterest.com/v5" if USE_SANDBOX else "https://api.pinterest.com/v5"

PIN_CREATE_URL = f"{BASE_URL}/pins"
CREATE_BOARD_URL = f"{BASE_URL}/boards"
TOKEN_REFRESH_URL = f"{BASE_URL}/oauth/token"

HEADERS = [
    "Image URL", "Product Name", "Product URL", "Product Price", "Product Type", "Collection Name",
    "Tags", "Review Summary", "Generated Pin Title", "Generated Pin Description", "Board Title", "Status", "Board ID", "Order"
]

board_cache = {}

def load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

# Import the get_access_token function from pinterest_auth which has token refresh logic
from pinterest_auth import get_access_token


def get_sheet_service():
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
    return build("sheets", "v4", credentials=creds)

def get_data(sheet_service):
    sheet = sheet_service.spreadsheets().values()

    result = sheet.get(spreadsheetId=SPREADSHEET_ID, range="Sheet1").execute()
    values = result.get("values", [])

    if not values or values[0] != HEADERS:
        print("⚠️ Sheet headers are missing or incorrect. Resetting header row...")
        body = {
            "values": [HEADERS]
        }
        sheet.update(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body=body
        ).execute()
        values = sheet.get(spreadsheetId=SPREADSHEET_ID, range="Sheet1").execute().get("values", [])

    return values


def update_sheet(sheet_service, row_index, board_id):
    body = {
        "values": [["POSTED", board_id]]
    }
    range_ = f"Sheet1!L{row_index + 1}:M{row_index + 1}"  # Status = column L, Board ID = column M
    sheet_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_,
        valueInputOption="RAW",
        body=body
    ).execute()

def get_or_create_board(access_token, board_name):
    if board_name in board_cache:
        return board_cache[board_name]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # First, check if board already exists
    try:
        # Get user's boards to check for existing board
        boards_url = f"{BASE_URL}/boards"
        boards_response = requests.get(boards_url, headers=headers)
        
        print(f"[DEBUG] Checking for existing board: {board_name}")
        print(f"[DEBUG] Boards API response: {boards_response.status_code}")
        
        if boards_response.status_code == 200:
            existing_boards = boards_response.json().get("items", [])
            print(f"[DEBUG] Found {len(existing_boards)} existing boards")
            
            for board in existing_boards:
                board_name_found = board.get("name", "")
                print(f"[DEBUG] Checking board: '{board_name_found}' vs '{board_name}'")
                if board_name_found == board_name:
                    board_id = board["id"]
                    board_cache[board_name] = board_id
                    print(f"📌 Found existing board: {board_name} (ID: {board_id})")
                    return board_id
            
            print(f"[DEBUG] Board '{board_name}' not found in existing boards, will create new one")
        else:
            print(f"[DEBUG] Boards API failed: {boards_response.status_code} - {boards_response.text}")
            print(f"[DEBUG] Will attempt to create board anyway")
    except Exception as e:
        print(f"⚠️ Could not check existing boards: {e}")
        print(f"[DEBUG] Will attempt to create board anyway")

    # Board doesn't exist, create it
    print(f"[DEBUG] Creating new board: {board_name}")
    
    # Add rate limiting delay
    import time
    time.sleep(1)  # 1 second delay between Pinterest API calls

    payload = {
        "name": board_name[:50],
        "privacy": "PUBLIC"
    }

    r = requests.post(CREATE_BOARD_URL, headers=headers, json=payload)
    print(f"[DEBUG] Board creation response: {r.status_code} - {r.text}")
    
    if r.status_code == 201:
        board_id = r.json()["id"]
        board_cache[board_name] = board_id
        print(f"📌 Created new board: {board_name}")
        return board_id
    elif r.status_code == 429:  # Rate limit exceeded
        print(f"⚠️ Rate limit exceeded for board creation. Waiting 60 seconds...")
        time.sleep(60)
        # Retry once after waiting
        r = requests.post(CREATE_BOARD_URL, headers=headers, json=payload)
        if r.status_code == 201:
            board_id = r.json()["id"]
            board_cache[board_name] = board_id
            print(f"📌 Created board after retry: {board_name}")
            return board_id
    elif r.status_code == 400:  # Bad request - might be duplicate board
        try:
            error_data = r.json()
            if error_data.get("code") == 58 and "already have a board with this name" in error_data.get("message", ""):
                print(f"⚠️ Board '{board_name}' already exists (creation failed). Finding it...")
                # Try to find the existing board again
                boards_response = requests.get(f"{BASE_URL}/boards", headers=headers)
                if boards_response.status_code == 200:
                    existing_boards = boards_response.json().get("items", [])
                    for board in existing_boards:
                        if board.get("name") == board_name:
                            board_id = board["id"]
                            board_cache[board_name] = board_id
                            print(f"📌 Found existing board after creation failed: {board_name} (ID: {board_id})")
                            return board_id
        except Exception as e:
            print(f"⚠️ Could not parse error response: {e}")
    else:
        print(f"❌ Failed to create board '{board_name}': {r.text}")
        return None

def post_pin(access_token, board_id, image_url, title, description):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "board_id": board_id,
        "title": title[:100],
        "alt_text": description[:500],
        "description": description[:500],
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        }
    }

    # Add rate limiting delay
    import time
    time.sleep(2)  # 2 second delay between pin creation calls

    r = requests.post(PIN_CREATE_URL, headers=headers, json=payload)
    if r.status_code == 201:
        print(f"✅ Posted pin: {title}")
        return True
    elif r.status_code == 429:  # Rate limit exceeded
        print(f"⚠️ Rate limit exceeded for pin creation. Waiting 60 seconds...")
        time.sleep(60)
        # Retry once after waiting
        r = requests.post(PIN_CREATE_URL, headers=headers, json=payload)
        if r.status_code == 201:
            print(f"✅ Posted pin after retry: {title}")
            return True
    else:
        print(f"❌ Failed to post pin '{title}': {r.status_code} - {r.text}")
        return False

def main():
    access_token = get_access_token()
    sheet_service = get_sheet_service()
    data = get_data(sheet_service)

    for i, row in enumerate(data[1:], start=1):  # skip headers
        row_data = dict(zip(HEADERS, row + [""] * (len(HEADERS) - len(row))))

        if row_data["Status"].strip().upper() == "POSTED":
            continue

        image_url = row_data["Image URL"]
        pin_title = row_data["Generated Pin Title"]
        pin_description = row_data["Generated Pin Description"]
        board_name = row_data["Board Title"]

        if not (image_url and pin_title and pin_description and board_name):
            print(f"⚠️ Skipping row {i + 1} due to missing fields.")
            continue

        board_id = row_data["Board ID"] or get_or_create_board(access_token, board_name)
        if board_id and post_pin(access_token, board_id, image_url, pin_title, pin_description):
            update_sheet(sheet_service, i + 1, board_id)

if __name__ == "__main__":
    main()
