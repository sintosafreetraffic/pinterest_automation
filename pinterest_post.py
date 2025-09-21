
import os
import json
import requests
import time
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
all_boards_cache = None

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

def get_all_boards(access_token):
    """Get all boards once and cache them"""
    global all_boards_cache
    
    if all_boards_cache is not None:
        return all_boards_cache
    
    print(f"[DEBUG] Fetching all boards (one-time operation)...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    all_boards = []
    page_size = 2000  # Maximum boards per page to get all boards in one request
    page = 1
    max_pages = 5  # Reduced max pages since we're getting many more per page
    
    while page <= max_pages:
        boards_url = f"{BASE_URL}/boards?page_size={page_size}&page={page}"
        boards_response = requests.get(boards_url, headers=headers)
        
        print(f"[DEBUG] Boards API page {page} response: {boards_response.status_code}")
        
        if boards_response.status_code == 200:
            response_data = boards_response.json()
            page_boards = response_data.get("items", [])
            
            # Debug: Check the actual response structure
            print(f"[DEBUG] Page {page} response structure: {list(response_data.keys())}")
            if "bookmark" in response_data:
                print(f"[DEBUG] Page {page} has bookmark: {response_data['bookmark']}")
            if "has_next" in response_data:
                print(f"[DEBUG] Page {page} has_next: {response_data['has_next']}")
            
            # Check for duplicates before adding
            new_boards = []
            for board in page_boards:
                board_id = board.get("id")
                if not any(existing.get("id") == board_id for existing in all_boards):
                    new_boards.append(board)
                else:
                    print(f"[DEBUG] Skipping duplicate board: {board.get('name', 'No name')} (ID: {board_id})")
            
            all_boards.extend(new_boards)
            
            print(f"[DEBUG] Page {page}: Found {len(page_boards)} boards, {len(new_boards)} new (total so far: {len(all_boards)})")
            
            # Check if we have more pages using Pinterest's pagination indicators
            has_more_pages = True
            
            # Check Pinterest's pagination indicators
            if "has_next" in response_data and not response_data["has_next"]:
                print(f"[DEBUG] Pinterest API indicates no more pages (has_next: false)")
                has_more_pages = False
            elif len(page_boards) < page_size:
                print(f"[DEBUG] Reached last page (got {len(page_boards)} boards, expected {page_size})")
                has_more_pages = False
            elif len(page_boards) == 0:
                print(f"[DEBUG] No boards returned on page {page} - reached end")
                has_more_pages = False
            
            if not has_more_pages:
                break
            else:
                page += 1
                # Add delay between pages to respect rate limits
                time.sleep(0.5)
        else:
            print(f"[DEBUG] Boards API failed on page {page}: {boards_response.status_code} - {boards_response.text}")
            break
    
    print(f"[DEBUG] Total boards fetched: {len(all_boards)}")
    
    # Log all board names for debugging
    print(f"[DEBUG] All board names found:")
    for i, board in enumerate(all_boards, 1):
        board_name = board.get("name", "No name")
        print(f"[DEBUG] {i:3d}. '{board_name}' (length: {len(board_name)})")
        
        # Check if this board name contains "Outfit" or "Inspirationen"
        if "Outfit" in board_name or "Inspirationen" in board_name:
            print(f"[DEBUG] *** POTENTIAL MATCH: '{board_name}' ***")
            print(f"[DEBUG] *** Contains 'Outfit': {'Outfit' in board_name}")
            print(f"[DEBUG] *** Contains 'Inspirationen': {'Inspirationen' in board_name}")
            print(f"[DEBUG] *** Exact match: {board_name == 'Outfit Inspirationen'}")
            print(f"[DEBUG] *** Stripped match: {board_name.strip() == 'Outfit Inspirationen'}")
            print(f"[DEBUG] *** Repr: {repr(board_name)}")
    
    all_boards_cache = all_boards
    return all_boards

def search_board_by_name(access_token, board_name):
    """Search for a board by name using Pinterest's search API"""
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Use Pinterest's search API to find boards by name
        search_url = f"{BASE_URL}/search/boards"
        params = {
            "query": board_name,
            "page_size": 25
        }
        
        print(f"[DEBUG] Searching for board by name: '{board_name}'")
        response = requests.get(search_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            boards = data.get("items", [])
            print(f"[DEBUG] Search found {len(boards)} boards matching '{board_name}'")
            
            for board in boards:
                found_name = board.get("name", "")
                if found_name == board_name:
                    board_id = board["id"]
                    print(f"📌 Found board via search: {board_name} (ID: {board_id})")
                    return board_id
                else:
                    print(f"[DEBUG] Search result: '{found_name}' (not exact match)")
            
            print(f"[DEBUG] No exact match found in search results")
            return None
        else:
            print(f"[DEBUG] Board search failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"[DEBUG] Error searching for board: {e}")
        return None

def get_or_create_board(access_token, board_name):
    if board_name in board_cache:
        return board_cache[board_name]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Search through cached boards (board search requires additional permissions)
    try:
        print(f"[DEBUG] Falling back to cached boards for: {board_name}")
        
        # Get all boards (cached)
        all_boards = get_all_boards(access_token)
        
        # Search through cached boards
        print(f"[DEBUG] Searching for board: '{board_name}' (length: {len(board_name)})")
        print(f"[DEBUG] Target board repr: {repr(board_name)}")
        for board in all_boards:
            board_name_found = board.get("name", "")
            print(f"[DEBUG] Checking: '{board_name_found}' vs '{board_name}'")
            print(f"[DEBUG] Found board repr: {repr(board_name_found)}")
            if board_name_found == board_name:
                board_id = board["id"]
                board_cache[board_name] = board_id
                print(f"📌 Found existing board: {board_name} (ID: {board_id})")
                return board_id
        
        print(f"[DEBUG] Board '{board_name}' not found in {len(all_boards)} existing boards, will create new one")
        
    except Exception as e:
        print(f"⚠️ Could not check existing boards: {e}")
        print(f"[DEBUG] Will attempt to create board anyway")

    # Board doesn't exist, create it
    print(f"[DEBUG] Creating new board: {board_name}")
    
    # Add rate limiting delay
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
                print(f"⚠️ Board '{board_name}' already exists (creation failed). Finding it in cached boards...")
                # Try to find the existing board in cached boards
                all_boards = get_all_boards(access_token)
                
                print(f"[DEBUG] Searching through {len(all_boards)} cached boards for '{board_name}'")
                for board in all_boards:
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

def post_pin(access_token, board_id, image_url, title, description, destination_url=None):
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
    
    # Add destination URL (link) if provided
    if destination_url:
        payload["link"] = destination_url
        print(f"[DEBUG] Adding destination URL to pin: {destination_url}")
    else:
        print(f"[DEBUG] No destination URL provided for pin")

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
    
    # Fetch all boards once at the start (this will cache them)
    print("🔄 Fetching all Pinterest boards (one-time operation)...")
    get_all_boards(access_token)
    print("✅ All boards cached successfully")
    
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
        product_url = row_data.get("Product URL", "")  # Get product URL if available

        if not (image_url and pin_title and pin_description and board_name):
            print(f"⚠️ Skipping row {i + 1} due to missing fields.")
            continue

        board_id = row_data["Board ID"] or get_or_create_board(access_token, board_name)
        if board_id and post_pin(access_token, board_id, image_url, pin_title, pin_description, product_url):
            update_sheet(sheet_service, i + 1, board_id)

if __name__ == "__main__":
    main()
