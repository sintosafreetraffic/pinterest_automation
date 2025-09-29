import os
import shutil
import string
import threading
import requests
import queue
import gspread
import re
import time
import sys
# Use only load_dotenv and os.getenv for consistency
from dotenv import load_dotenv
from pathlib import Path
import zipfile
import datetime
import random
import concurrent.futures
from collections import defaultdict
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
# Import Pinterest posting functionality
from pinterest_post import post_pin, get_or_create_board, get_access_token

# --- Simplified Key Loading ---
BASEDIR = Path(__file__).resolve().parent
DOTENV_PATH = BASEDIR / ".env"

print(f"--- DEBUG: Attempting to load .env from: {DOTENV_PATH} ---")
# Load into environment variables ONCE
# verbose=True shows which keys are loaded from the file
load_dotenv(dotenv_path=DOTENV_PATH, verbose=True, override=True)

# Get keys from environment variables
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
DEEPSEEK_API_KEY=os.getenv("DEEPSEEK_API_KEY")
# Consider loading these from .env too if they might change
SHOPIFY_STORE_URL = "92c6ce-58.myshopify.com"
CREDENTIALS_FILE = "credentials.json"

# --- ADD Key Verification ---
# Critical checks - stop if essential keys are missing
if not SHOPIFY_API_KEY:
    print("❌ CRITICAL ERROR: SHOPIFY_API_KEY not found in .env file or environment!")
    # sys.exit("Exiting: Shopify API Key is missing.")
if not DEEPSEEK_API_KEY:
    print("❌ CRITICAL ERROR: DEEPSEEK API KEY not found in .env file or environment!")
    # Decide how to handle: exit, raise error, or proceed with limited functionality
    # sys.exit("Exiting:  API Key is missing.")

def call_deepseek_api(prompt, api_key, model="deepseek-chat", max_tokens=100, temperature=0.7):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"❌ DeepSeek API error: {resp.status_code}, {resp.text}")
            return ""
    except Exception as e:
        print(f"❌ DeepSeek API error: {e}")
        return ""

print(f"--- DEBUG: Keys Status ---")
# More informative status, avoid printing keys directly even if masked
print(f"Shopify Key Status: {'Loaded' if SHOPIFY_API_KEY else 'MISSING!'}")
print(f"DeepSeek Key Status: {'Loaded' if DEEPSEEK_API_KEY else 'MISSING!'}")
print(f"--- END DEBUG ---")



# ✅ Authenticate Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
# Ensure credentials file exists
if not os.path.exists(CREDENTIALS_FILE):
    print(f"❌ CRITICAL ERROR: Google Credentials file '{CREDENTIALS_FILE}' not found!")
    sys.exit(f"Exiting: Missing Google Credentials file '{CREDENTIALS_FILE}'.")

try:
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    google_sheets_client = gspread.authorize(creds) # Renamed client to avoid conflict
    print("✅ Google credentials authorized.")
except Exception as e:
    print(f"❌ Google Credentials Error: {e}")
    sys.exit(f"Exiting: Failed to authorize Google credentials - {e}")


# ✅ Connect to Google Sheets
SHEET_ID = "1SutOYJ0UA-DDy1d4Xf86jf4wh8-ImNG5Tq0lcvMlqmE"
try:
    # Use the authorized client
    sheet = google_sheets_client.open_by_key(SHEET_ID).sheet1
    print(f"✅ Connected to Google Sheet ID: {SHEET_ID} successfully!")
except gspread.exceptions.APIError as e:
     print(f"❌ Google Sheets API Error connecting to sheet: {e}")
     # Provide more specific advice based on common errors
     if 'PERMISSION_DENIED' in str(e):
         print("   Ensure the service account email has edit access to the Google Sheet.")
     elif 'invalid_grant' in str(e):
          print("   Check if the service account key (credentials.json) is valid or has expired.")
     sys.exit(f"Exiting: Failed to connect to Google Sheet - {e}")
except Exception as e:
    print(f"❌ Google Sheets Generic Error connecting to sheet: {e}")
    sys.exit(f"Exiting: Failed to connect to Google Sheet - {e}")

# 🔥 Flask Setup
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.urandom(24) # Good for session security
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["TEMPLATES_AUTO_RELOAD"] = True # Useful for development
app.jinja_env.auto_reload = True

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Global progress tracking
automation_progress = {
    'status': 'idle',  # idle, running, completed, error
    'current_step': '',
    'progress_percent': 0,
    'total_items': 0,
    'processed_items': 0,
    'collection_id': '',
    'collection_name': '',
    'start_time': None,
    'end_time': None,
    'error_message': '',
    'logs': []
}
progress_lock = threading.Lock()

# ✅ Upload Logo Route
@app.route("/upload_logo", methods=["POST"])
def upload_logo():
    # ... (keep existing logo upload logic) ...
    if "file" not in request.files:
        flash("⚠️ No file selected!", "error")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("⚠️ No selected file!", "error")
        return redirect(url_for("index"))

    # Basic check for allowed extensions (optional but recommended)
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        flash("⚠️ Invalid file type. Please upload PNG, JPG, JPEG, or GIF.", "error")
        return redirect(url_for("index"))

    # Ensure filename is safe (though we are overwriting with logo.png)
    # from werkzeug.utils import secure_filename
    # filename = secure_filename(file.filename) # Not strictly needed if always saving as logo.png

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], "logo.png")
    try:
        file.save(file_path)
        flash("✅ Logo successfully uploaded!", "success")
    except Exception as e:
        flash(f"❌ Error saving logo: {e}", "error")

    return redirect(url_for("index"))


# ✅ Fetch Shopify Collections
def fetch_collections():
    # Ensure SHOPIFY_API_KEY is available
    if not SHOPIFY_API_KEY:
        print("❌ Cannot fetch collections: Shopify API Key is missing.")
        return {}

    headers = {"X-Shopify-Access-Token": SHOPIFY_API_KEY}
    collections = {}
    api_version = "2024-04" # Use a recent, stable API version

    # Define URLs using f-string and api_version variable
    urls = {
        "smart": f"https://{SHOPIFY_STORE_URL}/admin/api/{api_version}/smart_collections.json",
        "custom": f"https://{SHOPIFY_STORE_URL}/admin/api/{api_version}/custom_collections.json"
    }

    print("🔄 Fetching Shopify collections...")
    for key, url in urls.items():
        try:
            response = requests.get(url, headers=headers, timeout=10) # Add timeout
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            data = response.json()
            collection_key = key + "_collections" # e.g., "smart_collections"

            if collection_key in data:
                for col in data[collection_key]:
                     # Ensure id and title exist before adding
                     if "id" in col and "title" in col:
                        collections[str(col["id"])] = col["title"]
                print(f"   Fetched {len(data[collection_key])} {key} collections.")
            else:
                 print(f"   No '{collection_key}' key found in response for {key} collections.")

        except requests.exceptions.Timeout:
            print(f"❌ Timeout error fetching {key} collections from {url}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching {key} collections: {e}")
            # If auth error (401/403), suggest checking key
            if e.response is not None and e.response.status_code in [401, 403]:
                 print("   -> Check if your Shopify API Key is correct and has permissions.")

    if not collections:
         print("⚠️ No collections were fetched. Check Shopify API key/permissions or store status.")

    return collections

def get_seasonal_context_germany():
    """Get current seasonal context for Germany with 6-week lookahead intelligence"""
    now = datetime.datetime.now()
    month = now.month
    day = now.day
    
    # Define seasonal transitions with 6-week lookahead
    # Winter: Dec 1 - Feb 28/29
    # Spring: Mar 1 - May 31  
    # Summer: Jun 1 - Aug 31
    # Autumn: Sep 1 - Nov 30
    
    # Check if we're in the last 6 weeks of a season (42 days)
    if month == 2 and day >= 15:  # Mid-February - transition to Spring
        return "transition_to_spring", "Frühling"
    elif month == 5 and day >= 15:  # Mid-May - transition to Summer  
        return "transition_to_summer", "Sommer"
    elif month == 8 and day >= 15:  # Mid-August - transition to Autumn
        return "transition_to_autumn", "Herbst"
    elif month == 11 and day >= 15:  # Mid-November - transition to Winter
        return "transition_to_winter", "Winter"
    
    # Standard seasonal assignment
    if month in [12, 1, 2]:
        return "winter", "Winter"
    elif month in [3, 4, 5]:
        return "spring", "Frühling"
    elif month in [6, 7, 8]:
        return "summer", "Sommer"
    else:
        return "autumn", "Herbst"

def remove_old_years_and_fix_season(text, season_override=None):
    """Ensures no old years (2024, etc) appear in output, and normalizes season/year with German seasonal intelligence."""
    # 1. Replace all year-like patterns with current year if they're older
    current_year = datetime.datetime.now().year
    # Only match years from 2021 to current_year-1 to avoid mistakes
    text = re.sub(r"(20[1-9][0-9])", lambda m: str(current_year) if int(m.group(1)) < current_year else m.group(1), text)

    # 2. Apply German seasonal intelligence with 6-week lookahead
    if season_override:
        current_season = season_override
        seasonal_context = "override"
    else:
        seasonal_context, current_season = get_seasonal_context_germany()
    
    # 3. Replace seasonal references with current context
    text = re.sub(r"\b(Winter|Frühling|Sommer|Herbst|Spring|Summer|Autumn|Fall) 20[1-9][0-9]\b",
                  f"{current_season} {current_year}", text)
    
    # 4. Add seasonal intelligence to content
    if seasonal_context == "transition_to_spring":
        text = text.replace("Sommer", "Frühling").replace("Summer", "Spring")
        # Avoid summer content when transitioning to spring
        if any(word in text.lower() for word in ["sommer", "summer", "badeanzug", "bikini", "sonnencreme"]):
            text = text.replace("Sommer", "Frühling").replace("Summer", "Spring")
    elif seasonal_context == "transition_to_summer":
        # Avoid winter content when transitioning to summer
        if any(word in text.lower() for word in ["winter", "warm", "gefuttert", "mantel", "jacke"]):
            text = text.replace("Winter", "Sommer").replace("warm", "leicht")
    elif seasonal_context == "transition_to_autumn":
        # Avoid summer content when transitioning to autumn
        if any(word in text.lower() for word in ["sommer", "summer", "badeanzug", "bikini"]):
            text = text.replace("Sommer", "Herbst").replace("Summer", "Autumn")
    elif seasonal_context == "transition_to_winter":
        # Avoid spring content when transitioning to winter
        if any(word in text.lower() for word in ["frühling", "spring", "blüte", "blume"]):
            text = text.replace("Frühling", "Winter").replace("Spring", "Winter")
    
    return text

# ✅ Fetch Shopify Products (Simplified Error Handling)
def fetch_product_data(collection_id, image_limit=3):
    if not SHOPIFY_API_KEY:
        print("❌ Cannot fetch products: Shopify API Key is missing.")
        return []
    if not collection_id:
         print("❌ Cannot fetch products: No collection ID provided.")
         return []

    print(f"🔄 Fetching products for collection {collection_id} (limit: {image_limit} images/product)...")
    api_version = "2024-04" # Use consistent API version
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/{api_version}/collections/{collection_id}/products.json"
    headers = {"X-Shopify-Access-Token": SHOPIFY_API_KEY}
    image_data = []
    # Fetch collection name once if needed, handle potential errors
    try:
        # This might be slow if called repeatedly, consider caching if performance is an issue
        all_collections = fetch_collections()
        collection_name = all_collections.get(str(collection_id), "Unknown Collection")
    except Exception as e:
         print(f"⚠️ Error fetching collection name, using fallback: {e}")
         collection_name = "General Fashion" # Fallback

    params = {"limit": 250} # Max limit per page
    try:
        response = requests.get(url, headers=headers, params=params, timeout=20) # Increased timeout for products
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print(f"❌ Timeout error fetching products for collection {collection_id}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching products for collection {collection_id}: {e}")
        if e.response is not None:
             print(f"   Status Code: {e.response.status_code}")
             if e.response.status_code == 404:
                  print(f"   -> Collection ID {collection_id} might not exist or be accessible.")
             elif e.response.status_code in [401, 403]:
                  print(f"   -> Check Shopify API Key permissions.")
        return [] # Return empty list on error

    products = response.json().get("products", [])
    print(f"   Found {len(products)} products in collection {collection_id} ('{collection_name}'). Processing...")

    # Process products (simplified - consider if threading is still needed for your volume)
    for product in products:
        try:
            if product.get("status") != "active":
                continue # Skip non-active products

            product_id = product.get("id")
            product_name = product.get("title", "Unknown Product").replace("_", " ")
            product_url = f"https://{SHOPIFY_STORE_URL}/products/{product.get('handle', 'unknown')}"
            # Safely get price from the first variant, provide default
            variants = product.get("variants", [])
            product_price = variants[0].get("price", "N/A") if variants else "N/A"
            product_type = product.get("product_type", "N/A") or "N/A" # Ensure not empty

            # Safely handle tags
            tags_list = product.get("tags", [])
            tags = ", ".join(tags_list) if isinstance(tags_list, list) else str(tags_list or "").strip()

            # Get product description for better Pin descriptions
            product_description = product.get("body_html", "")
            # Clean HTML tags from description
            import re
            if product_description:
                product_description = re.sub(r'<[^>]+>', '', product_description)  # Remove HTML tags
                product_description = re.sub(r'\s+', ' ', product_description).strip()  # Clean whitespace
                # Truncate if too long (keep first 200 chars for context)
                if len(product_description) > 200:
                    product_description = product_description[:200] + "..."
            else:
                product_description = ""

            # Placeholder for review summary - fetching reviews per product can be slow
            # Consider if the placeholder is sufficient or if real reviews are needed
            review_summary = "🔥 Bestseller – Trendet auf TikTok!"
            # If real reviews are needed, uncomment and potentially optimize fetch_product_reviews
            # review_summary = fetch_product_reviews(product_id)

            images = product.get("images", [])
            # Ensure image limit is applied correctly, handle case where images are fewer than limit
            for i, image in enumerate(images):
                if i >= image_limit: # Stop if image limit is reached
                    break
                if "src" in image:
                    image_data.append((
    image["src"], product_name, product_url, product_price,
    product_type, collection_name, tags, review_summary, str(product_id), product_description
))

        except Exception as e:
             print(f"⚠️ Error processing product ID {product.get('id', 'N/A')}: {e}") # Log error but continue

    print(f"   Processed {len(image_data)} images from collection {collection_id}.")
    return image_data

# ❗ Fetch Product Reviews - CAUTION: This makes an extra API call PER product.
# This can be very slow and hit rate limits quickly. Consider if this is necessary.
def fetch_product_reviews(product_id):
    # Only attempt if key is available
    if not SHOPIFY_API_KEY or not product_id:
        return "🔥 Bestseller – Trendet auf TikTok!" # Default fallback

    reviews_url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-04/products/{product_id}.json" # Use consistent API version
    headers = {"X-Shopify-Access-Token": SHOPIFY_API_KEY}
    # Lower timeout for this specific, potentially non-critical call
    try:
        response = requests.get(reviews_url, headers=headers, timeout=5)
        response.raise_for_status()

        product_data = response.json().get("product", {})

        # Example: Accessing metafields IF they exist and are configured
        # This depends heavily on how reviews are stored (e.g., Shopify Reviews app, other apps)
        # The following is a GUESS based on common patterns - ADJUST AS NEEDED
        review_count = 0
        avg_rating = "N/A"
        metafields = product_data.get("metafields", []) # Metafields are usually a list
        for mf in metafields:
             # Example using Shopify's standard Product Reviews app metafields
             if mf.get('namespace') == 'spr' and mf.get('key') == 'reviews_count':
                  review_count = int(mf.get('value', 0))
             if mf.get('namespace') == 'spr' and mf.get('key') == 'reviews_average':
                  avg_rating = float(mf.get('value', 0.0))

        if review_count > 0 and avg_rating != "N/A":
            return f"⭐ {avg_rating:.1f}/5 Sterne von {review_count}+ Kunden!"

    except requests.exceptions.RequestException as e:
        # Don't stop everything for review errors, just log and return default
        # Avoid logging excessively for rate limits (429) as it can clutter logs
        status_code = e.response.status_code if e.response is not None else None
        if status_code != 429: # Log errors other than rate limits
             print(f"⚠️ Error fetching reviews for product {product_id}: {e} (Status: {status_code})")

    # Default fallback if reviews aren't found or error occurs
    return "🔥 Bestseller – Trendet auf TikTok!"


import requests

def retry_on_rate_limit(func):
    def wrapper(*args, **kwargs):
        retries = 5
        wait_time = 3
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                # Rate limit or server errors
                status = e.response.status_code if e.response else None
                if status == 429:
                    print(f"\nDeepSeek Rate Limit (429) (Retry {attempt+1}/{retries} after {wait_time}s): {e}")
                    time.sleep(wait_time)
                    wait_time *= 2
                elif status and status >= 500:
                    print(f"\nDeepSeek Server Error ({status}) (Retry {attempt+1}/{retries}): {e}")
                    time.sleep(wait_time)
                    wait_time *= 2
                else:
                    print(f"\nDeepSeek API HTTP Error ({status}) (Attempt {attempt+1}/{retries}): {e}")
                    if attempt == retries - 1:
                        raise
                    time.sleep(wait_time / 2)
            except requests.exceptions.RequestException as e:
                print(f"\nDeepSeek Request Error (Attempt {attempt+1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(wait_time)
                wait_time *= 2
            except Exception as e:
                print(f"\nUnexpected Error in {func.__name__} (Attempt {attempt+1}/{retries}): {e}")
                if attempt == retries - 1:
                    print(f"Giving up after {retries} attempts.")
                    # Don't raise, will fallback below
                else:
                    time.sleep(wait_time)
                    wait_time *= 2

        # Fallback if all retries fail
        print(f"\n❌ {func.__name__} failed after {retries} retries.")
        # Return a sensible default based on the function's purpose
        if "title" in func.__name__:
            data = args[0] if args else None
            name = data[1] if data and len(data) > 1 else "Produkt"
            return f"{name.replace('_', ' ')} – Jetzt entdecken!"
        elif "description" in func.__name__:
            return "Ein Must-Have für 2025! #Trend #Fashion"
        elif "board" in func.__name__:
            return "Trend-Produkte"
        else:
            return None

    return wrapper

@retry_on_rate_limit
def generate_single_pin_title(data):
    """
    Generate a Pinterest Pin Title using DeepSeek.
    Output is always short, catchy, and optimized for clicks (German).
    """
    try:
        # Adjust these indices to your columns!
        # data = [
        #   0: Image URL, 1: Product Name, 2: Product URL, 3: Product Price,
        #   4: Product Type, 5: Collection Name, 6: Tags, 7: Review Summary,
        #   8: Product ID, 9: Product Description, 10: Generated Pin Title, etc.
        # ]
        product_name  = data[1]
        product_price = data[3]
        product_type  = data[4]
        tags          = data[6]
        product_description = data[9] if len(data) > 9 else ""  # Product description
        clean_product_name = str(product_name).replace("_", " ")
        price = str(product_price)
        category = str(product_type)
        tags_str = str(tags)
        description_text = str(product_description)
    except (IndexError, TypeError) as e:
        print(f"⚠️ Error unpacking data for title generation: {e}. Data: {data}")
        return "Tolles Produkt – Jetzt entdecken!"
    
    # Extract meaningful product terms for SEO (focus on product features, not brand/prepositions)
    import re
    # Remove brand prefix and focus on product description
    product_terms = re.sub(r'^[^|]*\|?\s*', '', clean_product_name).strip()  # Remove brand prefix
    product_terms = re.sub(r'[^\w\s]', ' ', product_terms).strip()  # Clean special chars
    
    # Filter out meaningless words and keep only substantial product terms
    meaningful_words = []
    skip_words = {'à', 'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'avec', 'pour', 'sur', 'dans', 'par', 'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car', 'que', 'qui', 'quoi', 'dont', 'où', 'température', 'temperature', 'réglable', 'reglable'}
    
    for word in product_terms.split():
        word_lower = word.lower()
        if len(word) > 3 and word_lower not in skip_words and word.isalpha():
            meaningful_words.append(word)
    
    key_terms = ' '.join(meaningful_words)
    
    print(f"   DEBUG: Product name: '{clean_product_name}' -> Key terms: '{key_terms}'")
    
    # Get seasonal context for Germany
    seasonal_context, current_season = get_seasonal_context_germany()
    
    prompt = (
        "Du bist ein erfahrener, deutschsprachiger Pinterest-Copywriter für virale E-Commerce-Produkte.\n"
        "Schreibe einen einzigartigen, extrem klickstarken Pin-Titel für Pinterest, max. 60 Zeichen (keine Zeichen-Anzahl im Text!).\n"
        "WICHTIG: Verwende die Produktbegriffe aus dem Produktnamen für bessere SEO (z.B. bei 'Linen Sweater' verwende 'Linen' und 'Sweater').\n"
        "Der Titel MUSS mindestens einen der Produktbegriffe enthalten!\n"
        "Der Titel soll sofort Aufmerksamkeit erregen, neugierig machen oder einen Nutzen/Lifestyle vermitteln. "
        "Verwende maximal EIN passendes Emoji (am besten am Anfang oder Ende, kein Zwang). "
        "Keine Anführungszeichen, keine Listen, keine Nummerierungen, keine Meta-Angaben (z.B. 'Pin-Titel:').\n"
        "Text soll modern, emotional, anregend, kreativ und auf die Zielgruppe zugeschnitten sein. Keine offensichtlichen 'Werbetexte', sondern echte Value-Kommunikation.\n"
        "Gib ausschließlich den fertigen Pin-Titel zurück, keine Kommentare, kein Zusatztext.\n\n"
        f"Produkt: {clean_product_name}\n"
        f"Produktbegriffe (für SEO verwenden): {key_terms}\n"
        f"Preis: {price} €\n"
        f"Kategorie: {category}\n"
        f"Tags: {tags_str}\n"
        f"Produktbeschreibung: {description_text}\n"
        f"AKTUELLE SAISON (Deutschland): {current_season} {datetime.datetime.now().year}\n"
        f"SAISONALER KONTEXT: {seasonal_context}\n"
        "WICHTIG: Berücksichtige die aktuelle Saison in Deutschland! "
        "Vermeide saisonal unpassende Begriffe (z.B. keine Sommer-Begriffe im Spätsommer/Herbst, "
        "keine Winter-Begriffe im Spätwinter/Frühling).\n\n"
        "Gib nur den Pin-Titel zurück. Keine weiteren Erklärungen oder Begrenzungen."
    )

    pin_title = call_deepseek_api(
        prompt,
        DEEPSEEK_API_KEY,
        model="deepseek-chat",
        max_tokens=30,
        temperature=0.7
    )

    # Clean: Remove numbering, stray markdown, quotes, trim whitespace
    pin_title = re.sub(r"^[\d\*\-\.]+\s*", "", str(pin_title)).replace('"', '').strip()

    # Ensure product terms are included (force inclusion if missing)
    print(f"   DEBUG: Checking title '{pin_title}' for key terms: {key_terms}")
    if key_terms and not any(term.lower() in pin_title.lower() for term in key_terms.split()):
        # Add the first key term to the title
        first_term = key_terms.split()[0]
        pin_title = f"{first_term} {pin_title}"
        print(f"   ✅ FORCED: Added missing product term '{first_term}' to title")
        
        # If still no product terms, add a second one
        if len(key_terms.split()) > 1 and not any(term.lower() in pin_title.lower() for term in key_terms.split()[1:]):
            second_term = key_terms.split()[1]
            pin_title = f"{second_term} {pin_title}"
            print(f"   ✅ FORCED: Added second product term '{second_term}' to title")
    else:
        print(f"   ✅ Title already contains product terms")
    
    # ALWAYS ensure at least one product term is in the title (aggressive approach)
    if key_terms and not any(term.lower() in pin_title.lower() for term in key_terms.split()):
        first_term = key_terms.split()[0]
        pin_title = f"{first_term} {pin_title}"
        print(f"   🔥 AGGRESSIVE: Forced '{first_term}' into title")

    # If output is too long for Pinterest titles, hard-truncate and append ellipsis
    if len(pin_title) > 60:
        pin_title = pin_title[:57].rstrip() + "..."

    # Optionally, add an emoji if none present (to boost CTR)
    # if not re.search(r'[😀-🙏🦄✨❤️⭐🌟🔥💡🛒🎁]', pin_title):
    #     pin_title += " ⭐"

    # If still empty, fallback
    if not pin_title:
        pin_title = f"{clean_product_name} – Jetzt entdecken!"

    return pin_title
@retry_on_rate_limit
def generate_single_pin_description(data):
    """
    Generate a world-class Pinterest Pin Description with Hashtags using DeepSeek.
    Description is always emotionally engaging, SEO-strong, emoji-rich, and ends with trendy hashtags.
    """
    try:
        # Adjust to your columns!
        product_name  = data[1]
        product_price = data[3]
        product_type  = data[4]
        tags          = data[6]
        product_description = data[9] if len(data) > 9 else ""  # Product description
        clean_product_name = str(product_name).replace("_", " ")
        price = str(product_price)
        category = str(product_type)
        tags_str = str(tags)
        description_text = str(product_description)
    except (IndexError, TypeError) as e:
        print(f"⚠️ Error unpacking data for description generation: {e}. Data: {data}")
        return "Entdecke dieses tolle Produkt! Perfekt für dich. #Angebot #Neu"


    # Extract meaningful product terms for SEO (same as title generation)
    import re
    # Remove brand prefix and focus on product description
    product_terms = re.sub(r'^[^|]*\|?\s*', '', clean_product_name).strip()  # Remove brand prefix
    product_terms = re.sub(r'[^\w\s]', ' ', product_terms).strip()  # Clean special chars
    
    # Filter out meaningless words and keep only substantial product terms
    meaningful_words = []
    skip_words = {'à', 'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'avec', 'pour', 'sur', 'dans', 'par', 'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car', 'que', 'qui', 'quoi', 'dont', 'où', 'température', 'temperature', 'réglable', 'reglable'}
    
    for word in product_terms.split():
        word_lower = word.lower()
        if len(word) > 3 and word_lower not in skip_words and word.isalpha():
            meaningful_words.append(word)
    
    key_terms = ' '.join(meaningful_words)
    
    print(f"   DEBUG: Description - Product name: '{clean_product_name}' -> Key terms: '{key_terms}'")

    # Get seasonal context for Germany
    seasonal_context, current_season = get_seasonal_context_germany()
    
    # Short & powerful DeepSeek prompt with seasonal intelligence
    prompt = (
        "Du bist ein erfahrener Pinterest-Texter und kennst alle Best Practices für Conversion und Klicks. "
        "Schreibe eine unwiderstehliche, trendige Pinterest-Pin-Beschreibung auf Deutsch für das untenstehende Produkt. "
        "WICHTIG: Maximal 200 Zeichen! Verwende die Produktbegriffe aus dem Produktnamen für bessere SEO. "
        "Die Beschreibung MUSS mindestens einen der Produktbegriffe enthalten! "
        "Beginne sofort mit einem emotionalen Aufhänger, gefolgt vom stärksten Vorteil oder Trend-Faktor. "
        "Nutze bildhafte, lebendige Sprache, 1-2 Emojis und die Produktbegriffe für Keywords. "
        "Beende den Text mit nur 2 kurzen Hashtags. "
        "Beispiel: 'Perfekter Styling-Helfer! ✨ Schützt dein Haar und zaubert Volume. #Haarstyling #Beauty'"
        "Schreibe **nur** den eigentlichen Pin-Text – keine Meta-Informationen, keine Hinweise, "
        "keine Erklärungen, keine Einleitungen oder Abschlusssätze. "
        "Antwort darf **ausschließlich** den Pin-Text enthalten, ohne weitere Hinweise oder Formatierungen."
        "\n\n"
        f"Produkt: {clean_product_name}\n"
        f"Produktbegriffe (für SEO verwenden): {key_terms}\n"
        f"Preis: {price} €\n"
        f"Kategorie: {category}\n"
        f"Tags: {tags_str}\n"
        f"Produktbeschreibung: {description_text}\n"
        f"AKTUELLE SAISON (Deutschland): {current_season} {datetime.datetime.now().year}\n"
        f"SAISONALER KONTEXT: {seasonal_context}\n"
        "WICHTIG: Berücksichtige die aktuelle Saison in Deutschland! "
        "Vermeide saisonal unpassende Begriffe (z.B. keine Sommer-Begriffe im Spätsommer/Herbst, "
        "keine Winter-Begriffe im Spätwinter/Frühling). "
        "Achtung: Maximal 200 Zeichen! Entferne in deiner Antwort ausnahmslos alle Zeichenhinweise oder Meta-Kommentare."
    )


    pin_description = call_deepseek_api(
        prompt,
        DEEPSEEK_API_KEY,
        model="deepseek-chat",
        max_tokens=120,     # Increased for longer desc + hashtags
        temperature=0.85
    )

    # Ensure it's a string and clean up formatting
    if not isinstance(pin_description, str):
        pin_description = str(pin_description)

    # Remove leading markdown, numbers, or list symbols
    pin_description = re.sub(r"^[\d\*\-\.]+\s*", "", pin_description).strip()

    # Insert clean_product_name, category, and tags_str manually if not already done by DeepSeek
    pin_description = pin_description.replace("{clean_product_name}", clean_product_name)
    pin_description = pin_description.replace("{category}", category)
    pin_description = pin_description.replace("{tags_str}", tags_str)
    
    # Ensure description is not too long (max 200 characters)
    if len(pin_description) > 200:
        # Try to cut at a natural break point (space, punctuation)
        truncated = pin_description[:197]
        last_space = truncated.rfind(' ')
        last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        cut_point = max(last_space, last_punct)
        
        if cut_point > 150:  # Only cut if we can keep most of the content
            pin_description = pin_description[:cut_point] + "..."
        else:
            pin_description = pin_description[:197] + "..."

    # Ensure product terms are included (force inclusion if missing)
    print(f"   DEBUG: Checking description for key terms: {key_terms}")
    if key_terms and not any(term.lower() in pin_description.lower() for term in key_terms.split()):
        # Add the first key term to the description
        first_term = key_terms.split()[0]
        pin_description = f"{first_term} {pin_description}"
        print(f"   ✅ FORCED: Added missing product term '{first_term}' to description")
        
        # If still no product terms, add a second one
        if len(key_terms.split()) > 1 and not any(term.lower() in pin_description.lower() for term in key_terms.split()[1:]):
            second_term = key_terms.split()[1]
            pin_description = f"{second_term} {pin_description}"
            print(f"   ✅ FORCED: Added second product term '{second_term}' to description")
    else:
        print(f"   ✅ Description already contains product terms")
    
    # ALWAYS ensure at least one product term is in the description (aggressive approach)
    if key_terms and not any(term.lower() in pin_description.lower() for term in key_terms.split()):
        first_term = key_terms.split()[0]
        pin_description = f"{first_term} {pin_description}"
        print(f"   🔥 AGGRESSIVE: Forced '{first_term}' into description")

    # Ensure hashtags at end, add default if missing
    if "#" not in pin_description:
        pin_description += " #ModeMustHave #StylishAndPractical #Trend"

    # Ensure description fits Pinterest (250 chars)
    if len(pin_description) > 250:
        # Try to keep hashtags visible
        hashtags = " ".join([w for w in pin_description.split() if w.startswith("#")])
        text = pin_description.replace(hashtags, "").strip()
        pin_description = (text[:240] + "… ") + hashtags
        # Trim again if still too long
        pin_description = pin_description[:250]

    # Ensure not empty
    if not pin_description.strip():
        pin_description = f"Jetzt entdecken: {clean_product_name} – das Trendprodukt! #Trend #Fashion #MustHave"

    # <<< REMOVE ALL LEADING/TRAILING QUOTES >>>
    pin_description = remove_old_years_and_fix_season(pin_description)
    pin_description = pin_description.strip(' "\'')

    return pin_description

# Top SEO/Trend-Optimized Board Titles
BOARD_TITLES = [
    "Sommer Outfit Inspirationen",
    "Streetstyle für jeden Tag",
    "Trendige Kleider & Röcke",
    "Schicke Büro-Looks",
    "Minimalistische Garderobe",
    "Festival- & Party-Outfits",
    "Boho Style Vibes",
    "Athleisure & Sportliche Looks",
    "Date Night Fashion",
    "Urlaubs- & Reiseoutfits",
    "Layering & Herbstmode",
    "Winter Style Edit",
    "Denim-Trends & Jeans-Looks",
    "Beste Accessoires & Taschen",
    "Schuhtrends zum Verlieben",
    "Promi-Style Inspiration",
    "Fashion Hauls & Try-Ons",
    "Farbige Outfit-Ideen",
    "Plus Size Fashion",
    "Vintage & Retro Styles"
]

PRODUCT_TO_BOARD_KEYWORDS = {
    "kleid": "Bestseller Kleider",
    "dress": "Bestseller Kleider",
    "abend": "Elegante Abendmode",
    "casual": "Alltag & Casual Looks",
    "anzug": "Business Looks",
    "business": "Business Looks",
    "boho": "Boho Chic Styles",
    "schmuck": "Edle Schmuckstücke",
    "jewelry": "Edle Schmuckstücke",
    "accessoire": "Trendige Accessoires",
    "tiktok": "TikTok Favorites",
    "neu": "New In: Neuheiten",
    "lounge": "Loungewear & Cozy",
    "outdoor": "Outdoor Essentials",
    "vintage": "Vintage Vibes",
    "winter": "Winter Essentials",
    "sommer": "Sommer Must-Haves",
    "spring": "Frühlingsgefühle",
    "herbst": "Herbsttrends",
    "boots": "Schuhe & Boots Trends",
    "shoes": "Schuhe & Boots Trends",
    "sport": "Sportliche Outfits",
    "minimal": "Minimalistische Styles",
    "urban": "Urban Fashion",
    "luxus": "Luxury Finds",
    "luxury": "Luxury Finds",
    "nachhaltig": "Sustainable Fashion",
}

def deepseek_best_board_title(product_name_or_type, board_titles, api_key):
    """
    Nutze DeepSeek, um aus einer festen Liste von Pinterest Board-Titeln exakt den besten (auf Deutsch!) für das Produkt/den Typ zu wählen.
    """
    prompt = (
        "Wähle aus der folgenden Liste den EINEN Pinterest Board-Titel, der am besten zum Produktnamen oder Produkttyp passt. "
        "Antworte nur mit dem Titel, keine Kommentare, keine weiteren Worte.\n\n"
        f"Produktname oder Produkttyp: '{product_name_or_type}'\n\n"
        "Board-Titel:\n" + "\n".join(f"- {t}" for t in board_titles)
    )
    result = call_deepseek_api(
        prompt,
        api_key,
        model="deepseek-chat",
        max_tokens=20,
        temperature=0.0
    )
    result_clean = result.strip().strip('"\'')
    for t in board_titles:
        if result_clean.lower() == t.lower():
            return t
    return board_titles[0]  # Fallback: always first board, never random

def generate_board_title_for_collection(product_name_or_type, board_titles_cache, api_key=None):
    """
    Liefert immer exakt einen Pinterest Board-Titel aus der BOARD_TITLES-Liste:
      1. Keyword-Mapping (German first).
      2. DeepSeek-LLM-Fallback auf bestes Board aus der Liste.
      3. Nie random, nie .title(), nie generisch außer Board #1 als letzter Ausweg.
    """
    name = (product_name_or_type or "").lower().strip()
    if not name:
        return BOARD_TITLES[0]  # fallback zu erstem Board-Titel

    if name in board_titles_cache:
        return board_titles_cache[name]

    for keyword, mapped_title in PRODUCT_TO_BOARD_KEYWORDS.items():
        if keyword in name:
            board_titles_cache[name] = mapped_title
            return mapped_title

    if api_key:
        board_title = deepseek_best_board_title(name, BOARD_TITLES, api_key)
    else:
        board_title = BOARD_TITLES[0]  # fallback: deterministic

    board_titles_cache[name] = board_title
    return board_title


# ✅ Update Progress (Enhanced with web tracking)
def update_progress(completed, total, stage=""):
    """Live progress update in the console and web interface."""
    percent = (completed / total) * 100 if total > 0 else 0
    sys.stdout.write(f"\r🔄 {stage}: {completed}/{total} ({percent:.1f}%) completed...")
    sys.stdout.flush()
    
    # Update web progress tracking
    with progress_lock:
        automation_progress['current_step'] = stage
        automation_progress['progress_percent'] = percent
        automation_progress['processed_items'] = completed
        automation_progress['total_items'] = total
        automation_progress['logs'].append(f"{stage}: {completed}/{total} ({percent:.1f}%)")

def update_automation_status(status, step="", error_msg=""):
    """Update the global automation status for web interface."""
    with progress_lock:
        automation_progress['status'] = status
        automation_progress['current_step'] = step
        if error_msg:
            automation_progress['error_message'] = error_msg
        if status == 'running' and not automation_progress['start_time']:
            automation_progress['start_time'] = datetime.datetime.now().isoformat()
        elif status in ['completed', 'error']:
            automation_progress['end_time'] = datetime.datetime.now().isoformat()

def generate_ai_pin_text_batch(image_data):
    """
    GOD MODE: Parallel, reliable, and progress-tracked AI Pin title/desc/board generation for massive scale.
    Each Pin is generated in its own thread, and results are returned in the correct order.
    Board title cache is thread-safe and minimizes duplicate AI calls.
    """
    if not DEEPSEEK_API_KEY or not image_data:
        print("⚠️ No AI key or no data.")
        return [("AI Key fehlt", "AI Key fehlt", "AI Key fehlt") for _ in image_data]

    total_pins = len(image_data)
    print(f"\n🚀 Generating AI text for {total_pins} Pins using up to 18 workers...")

    board_titles_cache = {}
    cache_lock = threading.Lock()
    results = [None] * total_pins

    def generate_for_pin(idx, data):
        try:
            pin_title = generate_single_pin_title(data)
            pin_desc  = generate_single_pin_description(data)
            product_name = data[1] if len(data) > 1 else ""
            product_type = data[4] if len(data) > 4 else ""
            # Priority: product_name first, fallback product_type
            board_key = product_name if product_name else product_type
            with cache_lock:
                board_title = generate_board_title_for_collection(board_key, board_titles_cache)
            return (idx, pin_title, pin_desc, board_title)
        except Exception as e:
            name = data[1].replace('_', ' ') if len(data) > 1 else "Produkt"
            print(f"❌ AI ERROR (idx={idx}): {e}")
            return (idx, f"{name} – Jetzt entdecken!", "Ein Must-Have für 2025! #Trend #Fashion", "Trend-Produkte")


    with concurrent.futures.ThreadPoolExecutor(max_workers=18) as executor:
        # Start all jobs
        futures = {executor.submit(generate_for_pin, i, d): i for i, d in enumerate(image_data)}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            idx, pin_title, pin_desc, board_title = future.result()
            results[idx] = (pin_title, pin_desc, board_title)
            completed += 1
            if completed % max(1, total_pins // 20) == 0 or completed == total_pins:
                update_progress(completed, total_pins, stage="AI Generation")
    print(f"\n✅ Completed AI Generation. Processed {total_pins} items.")
    return results

import re

def clean_pin_description(description):
    # Remove everything after "(250 Zeichen)" if it appears
    description = re.split(r"\(250 Zeichen\)", description)[0]

    # Remove all markdown bullets/stars/ellipsis at line start or end
    description = re.sub(r"(^[\*\.\-]+|[\*\.\-]+$)", "", description)

    # Collapse multiple linebreaks/spaces to one
    description = re.sub(r"\n+", " ", description)
    description = re.sub(r"\s{2,}", " ", description)

    # Remove trailing junk like "*…", "...", etc at the end
    description = re.sub(r"(\*…|\.{2,}|…|…|\*)+$", "", description).strip()

    # Now force to 250 chars, keep hashtags at the end if possible
    if len(description) > 250:
        # Try to keep hashtags at the end
        hashtags = " ".join([w for w in description.split() if w.startswith("#")])
        text = description.replace(hashtags, "").strip()
        description = (text[:240].rstrip() + "… " + hashtags).strip()
        # Ensure max 250 chars
        description = description[:250].strip()

    # Final super-clean
    return description.strip(' "\'')

def update_pin_id_in_sheet(row_idx, pin_id):
    # 'row_idx' is 1-based (header = 1, first data row = 2)
    pin_id_col = 15   # O column (15th col)
    sheet.update_cell(row_idx, pin_id_col, pin_id)

def ensure_sheet_headers(sheet, headers):
    existing_headers = sheet.row_values(1)
    if existing_headers != headers:
        print("⚠️ Headers missing/wrong, updating.")
        sheet.update([headers], f'A1:{gspread.utils.rowcol_to_a1(1, len(headers))}')
# OR using named arguments:
# sheet.update(values=[headers], range_name=f'A1:{gspread.utils.rowcol_to_a1(1, len(headers))}')



# ✅ Save to Google Sheets (Aligned with AI Output)
def save_to_google_sheets(image_data):
    if not image_data:
        print("⚠️ No image data to save to Google Sheets.")
        return

    headers = [
        "Image URL", "Product Name", "Product URL", "Product Price", "Product Type", "Collection Name",
        "Tags", "Review Summary", "Generated Pin Title", "Generated Pin Description", "Board Title",
        "Status", "Board ID", "Order", "Pin ID", "Ad Campaign Status", "Advertised At"
    ]

    # -- Always check and fix headers! --
    try:
        existing_headers = sheet.row_values(1)
        if existing_headers != headers:
            print("⚠️ Headers missing/incorrect. Updating headers in the first row...")
            sheet.update(f'A1:{gspread.utils.rowcol_to_a1(1, len(headers))}', [headers])
    except Exception as e:
        print(f"❌ Error checking/updating Google Sheet headers: {e}")
        return

    print(f"📤 Generating AI text before saving to Google Sheets...")
    ai_results = generate_ai_pin_text_batch(image_data)
    if len(ai_results) != len(image_data):
        print(f"❌ Mismatch between image data ({len(image_data)}) and AI results ({len(ai_results)}). Cannot save.")
        return

    rows_to_add = []
    print(f"   Preparing {len(image_data)} rows for Google Sheets...")
    for i, data in enumerate(image_data):
        pin_title, pin_description, board_title = ai_results[i]
        pin_description = clean_pin_description(pin_description)
        status, board_id = "", ""
        order = i + 1
        # Fallback for missing product id (should be always present at data[8])
        product_uid = str(data[8]) if len(data) > 8 else f"{data[1]}_{data[2].split('/')[-1]}"
        if len(data) >= 8:
            row = list(data[:8]) + [
                pin_title, pin_description, board_title, status, board_id, order, "", "", ""
            ]
            # Fill missing cols just in case
            row = (row + [""] * 17)[:17]
            rows_to_add.append(row)
        else:
            print(f"⚠️ Skipping row {i+1}: unexpected data structure {data}")

    # -- Optimized batch append with progress tracking --
    if rows_to_add:
        print(f"   📤 Uploading {len(rows_to_add)} rows to Google Sheets...")
        BATCH_SIZE = 100  # Smaller batches for faster processing
        total = len(rows_to_add)
        uploaded_count = 0
        
        # Get the next available row number (after existing data) - calculate once only
        existing_data = sheet.get_all_values()
        next_row = len(existing_data) + 1
        
        for start in range(0, total, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total)
            batch = rows_to_add[start:end]
            try:
                # Calculate the range for this batch
                start_row = next_row + start
                end_row = start_row + len(batch) - 1
                range_name = f'A{start_row}:Q{end_row}'  # Use columns A-Q (first 17 columns)
                
                print(f"   📤 Uploading batch to range {range_name}...")
                
                # Use batch update with specific range to ensure data goes to correct columns
                try:
                    sheet.update(values=batch, range_name=range_name, value_input_option='USER_ENTERED')
                    uploaded_count += len(batch)
                    progress_percent = (uploaded_count / total) * 100
                    print(f"   📊 Uploaded {uploaded_count}/{total} rows ({progress_percent:.1f}%)")
                except Exception as e:
                    if "exceeds grid limits" in str(e):
                        print(f"   🔧 Expanding Google Sheet to accommodate data...")
                        try:
                            # Add more rows to the sheet
                            sheet.add_rows(len(batch) + 50)  # Add extra rows for safety
                            print(f"   ✅ Added {len(batch) + 50} rows to sheet")
                            # Try batch upload again
                            sheet.update(values=batch, range_name=range_name, value_input_option='USER_ENTERED')
                            uploaded_count += len(batch)
                            progress_percent = (uploaded_count / total) * 100
                            print(f"   📊 Uploaded {uploaded_count}/{total} rows ({progress_percent:.1f}%)")
                        except Exception as expand_error:
                            print(f"❌ Failed to expand sheet: {expand_error}")
                            # Skip this batch
                            continue
                    else:
                        print(f"❌ Google Sheets error: {e}")
                        # Skip this batch and continue
                        continue
                
                # Update progress tracking
                    update_progress(uploaded_count, total, "Uploading to Google Sheets")
                
            except Exception as e:
                print(f"❌ Error uploading rows {start + 1}-{end}: {e}")
                # Try individual row upload as fallback
                for i, row in enumerate(batch):
                    try:
                        row_num = next_row + start + i
                        range_name = f'A{row_num}:Q{row_num}'
                        sheet.update(values=[row], range_name=range_name, value_input_option='USER_ENTERED')
                        uploaded_count += 1
                        if uploaded_count % 10 == 0:  # Update every 10 rows
                            progress_percent = (uploaded_count / total) * 100
                            print(f"   📊 Fallback upload: {uploaded_count}/{total} rows ({progress_percent:.1f}%)")
                            update_progress(uploaded_count, total, "Uploading to Google Sheets (fallback)")
                    except Exception as row_error:
                        print(f"❌ Failed to upload individual row {start + i + 1}: {row_error}")
        
        print(f"   ✅ Google Sheets upload completed: {uploaded_count} rows uploaded")
    else:
        print("⚠️ No valid rows were prepared to add to Google Sheets.")

def save_to_google_sheets_with_ai(image_data, ai_results):
    """Save data to Google Sheets with pre-generated AI results"""
    if not image_data or not ai_results:
        print("⚠️ No image data or AI results to save to Google Sheets.")
        return

    headers = [
        "Image URL", "Product Name", "Product URL", "Product Price", "Product Type", "Collection Name",
        "Tags", "Review Summary", "Generated Pin Title", "Generated Pin Description", "Board Title",
        "Status", "Board ID", "Order", "Pin ID", "Ad Campaign Status", "Advertised At"
    ]

    # -- Always check and fix headers! --
    try:
        existing_headers = sheet.row_values(1)
        if existing_headers != headers:
            print("⚠️ Headers missing/incorrect. Updating headers in the first row...")
            sheet.update([headers], f'A1:{gspread.utils.rowcol_to_a1(1, len(headers))}')
    except Exception as e:
        print(f"❌ Error checking/updating Google Sheet headers: {e}")
        return

    rows_to_add = []
    print(f"   Preparing {len(image_data)} rows for Google Sheets...")
    print(f"   DEBUG: AI results length: {len(ai_results)}")
    for i, data in enumerate(image_data):
        print(f"   DEBUG: Processing item {i+1}, data length: {len(data)}")
        print(f"   DEBUG: Data sample: {data[:3] if len(data) >= 3 else data}")
        
        if i < len(ai_results):
            pin_title, pin_description, board_title = ai_results[i]
            print(f"   DEBUG: AI result {i+1}: title='{pin_title[:50]}...', desc='{pin_description[:50]}...', board='{board_title}'")
        else:
            print(f"   ⚠️ No AI result for item {i+1}")
            pin_title, pin_description, board_title = "No AI Result", "No AI Result", "No AI Result"
            
        pin_description = clean_pin_description(pin_description)
        status, board_id = "", ""  # Empty status until actually posted to Pinterest
        order = i + 1
        # Fallback for missing product id (should be always present at data[8])
        product_uid = str(data[8]) if len(data) > 8 else f"{data[1]}_{data[2].split('/')[-1]}"
        if len(data) >= 8:
            row = list(data[:8]) + [
                pin_title, pin_description, board_title, status, board_id, order, "", "", ""
            ]
            # Fill missing cols just in case
            row = (row + [""] * 17)[:17]
            print(f"   DEBUG: Final row {i+1}: {row[:5]}...")
            rows_to_add.append(row)
        else:
            print(f"⚠️ Skipping row {i+1}: unexpected data structure {data}")

    # -- Optimized batch append with progress tracking --
    if rows_to_add:
        print(f"   📤 Uploading {len(rows_to_add)} rows to Google Sheets...")
        BATCH_SIZE = 100  # Smaller batches for faster processing
        total = len(rows_to_add)
        uploaded_count = 0
        
        # Get the next available row number (after existing data) - calculate once only
        existing_data = sheet.get_all_values()
        next_row = len(existing_data) + 1
        
        for start in range(0, total, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total)
            batch = rows_to_add[start:end]
            try:
                # Calculate the range for this batch
                start_row = next_row + start
                end_row = start_row + len(batch) - 1
                range_name = f'A{start_row}:Q{end_row}'  # Use columns A-Q (first 17 columns)
                
                print(f"   📤 Uploading batch to range {range_name}...")
                
                # Use batch update with specific range to ensure data goes to correct columns
                try:
                    sheet.update(values=batch, range_name=range_name, value_input_option='USER_ENTERED')
                    uploaded_count += len(batch)
                    progress_percent = (uploaded_count / total) * 100
                    print(f"   📊 Uploaded {uploaded_count}/{total} rows ({progress_percent:.1f}%)")
                except Exception as e:
                    if "exceeds grid limits" in str(e):
                        print(f"   🔧 Expanding Google Sheet to accommodate data...")
                        try:
                            # Add more rows to the sheet
                            sheet.add_rows(len(batch) + 50)  # Add extra rows for safety
                            print(f"   ✅ Added {len(batch) + 50} rows to sheet")
                            # Try batch upload again
                            sheet.update(values=batch, range_name=range_name, value_input_option='USER_ENTERED')
                            uploaded_count += len(batch)
                            progress_percent = (uploaded_count / total) * 100
                            print(f"   📊 Uploaded {uploaded_count}/{total} rows ({progress_percent:.1f}%)")
                        except Exception as expand_error:
                            print(f"❌ Failed to expand sheet: {expand_error}")
                            # Skip this batch
                            continue
                    elif "Quota exceeded" in str(e):
                        print(f"⏳ Rate limit hit, waiting 60 seconds...")
                        import time
                        time.sleep(60)  # Wait 1 minute for quota reset
                        # Retry the batch
                        try:
                            sheet.update(values=batch, range_name=range_name, value_input_option='USER_ENTERED')
                            uploaded_count += len(batch)
                            progress_percent = (uploaded_count / total) * 100
                            print(f"   📊 Uploaded {uploaded_count}/{total} rows ({progress_percent:.1f}%)")
                        except Exception as retry_error:
                            print(f"❌ Failed to upload batch after retry: {retry_error}")
                            continue
                    else:
                        print(f"❌ Error uploading batch: {e}")
                        continue
                
                # Update progress tracking
                update_progress(uploaded_count, total, "Uploading to Google Sheets")
                
            except Exception as e:
                print(f"❌ Error uploading rows {start + 1}-{end}: {e}")
                # Try individual row upload as fallback
                for i, row in enumerate(batch):
                    try:
                        row_num = next_row + start + i
                        range_name = f'A{row_num}:Q{row_num}'
                        sheet.update(values=[row], range_name=range_name, value_input_option='USER_ENTERED')
                        uploaded_count += 1
                        if uploaded_count % 10 == 0:  # Update every 10 rows
                            progress_percent = (uploaded_count / total) * 100
                            print(f"   📊 Fallback upload: {uploaded_count}/{total} rows ({progress_percent:.1f}%)")
                            update_progress(uploaded_count, total, "Uploading to Google Sheets (fallback)")
                    except Exception as row_error:
                        print(f"❌ Failed to upload individual row {start + i + 1}: {row_error}")
        
            print(f"   ✅ Google Sheets upload completed: {uploaded_count} rows uploaded")
    else:
        print("⚠️ No valid rows were prepared to add to Google Sheets.")

def post_pins_to_pinterest(image_data, ai_results):
    """Post generated pins to Pinterest with progress tracking"""
    if not image_data or not ai_results:
        print("⚠️ No data to post to Pinterest")
        return
    
    try:
        # Get Pinterest access token
        access_token = get_access_token()
        if not access_token:
            print("❌ No Pinterest access token available. Skipping Pinterest posting.")
            return
        
        print(f"📌 Starting Pinterest posting for {len(image_data)} pins...")
        posted_count = 0
        failed_count = 0
        
        for i, (data, ai_result) in enumerate(zip(image_data, ai_results)):
            try:
                pin_title, pin_description, board_title = ai_result
                image_url = data[0]
                product_url = data[2]
                
                # Get or create board
                board_id = get_or_create_board(access_token, board_title)
                if not board_id:
                    print(f"⚠️ Could not create/find board '{board_title}', skipping pin {i+1}")
                    failed_count += 1
                    continue
                
                # Post the pin
                pin_id = post_pin(access_token, board_id, image_url, pin_title, pin_description, product_url)
                if pin_id:
                    posted_count += 1
                    print(f"✅ Posted pin {i+1}/{len(image_data)}: {pin_title[:30]}...")
                else:
                    failed_count += 1
                    print(f"❌ Failed to post pin {i+1}/{len(image_data)}")
                
                # Update progress
                update_progress(i + 1, len(image_data), "Posting pins to Pinterest")
                
            except Exception as e:
                print(f"❌ Error posting pin {i+1}: {e}")
                failed_count += 1
        
        print(f"📌 Pinterest posting completed: {posted_count} posted, {failed_count} failed")
        
    except Exception as e:
        print(f"❌ Pinterest posting failed: {e}")

# ✅ Shopify Collection Cleanup Functions

def get_collection_products(collection_id):
    """Get all products from a specific collection"""
    if not SHOPIFY_API_KEY:
        print("❌ Cannot fetch collection products: Shopify API Key is missing.")
        return []
    
    all_products = []
    page_info = None
    
    while True:
        try:
            api_version = "2024-04"  # Use consistent API version
            url = f"https://{SHOPIFY_STORE_URL}/admin/api/{api_version}/collections/{collection_id}/products.json"
            params = {"limit": 250}
            if page_info:
                params["page_info"] = page_info
            
            headers = {
                "X-Shopify-Access-Token": SHOPIFY_API_KEY,
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            products = data.get("products", [])
            all_products.extend(products)
            
            # Check for pagination
            link_header = response.headers.get("Link", "")
            if "rel=\"next\"" in link_header:
                # Extract page_info from the Link header
                import re
                next_match = re.search(r'page_info=([^&>]+)', link_header)
                if next_match:
                    page_info = next_match.group(1)
                else:
                    break
            else:
                break
                
        except Exception as e:
            print(f"❌ Error fetching products from collection {collection_id}: {e}")
            break
    
    print(f"📦 Found {len(all_products)} products in collection {collection_id}")
    return all_products

def remove_product_from_collection(collection_id, product_id):
    """Remove a specific product from a collection using the correct Shopify API"""
    if not SHOPIFY_API_KEY:
        print("❌ Cannot remove product: Shopify API Key is missing.")
        return False
    
    try:
        api_version = "2024-04"  # Use consistent API version
        
        # Step 1: Get the collect ID that links the product to the collection
        collect_url = f"https://{SHOPIFY_STORE_URL}/admin/api/{api_version}/collects.json"
        params = {
            "product_id": product_id,
            "collection_id": collection_id
        }
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_API_KEY,
            "Content-Type": "application/json"
        }
        
        collect_response = requests.get(collect_url, headers=headers, params=params)
        collect_response.raise_for_status()
        
        collect_data = collect_response.json()
        collects = collect_data.get("collects", [])
        
        if not collects:
            print(f"⚠️ No collect found for product {product_id} in collection {collection_id}")
            return False
        
        # Step 2: Delete each collect entry (there might be multiple)
        removed_count = 0
        for collect in collects:
            collect_id = collect.get("id")
            if collect_id:
                delete_url = f"https://{SHOPIFY_STORE_URL}/admin/api/{api_version}/collects/{collect_id}.json"
                delete_response = requests.delete(delete_url, headers=headers)
                delete_response.raise_for_status()
                removed_count += 1
        
        print(f"✅ Removed product {product_id} from collection {collection_id} ({removed_count} collect(s) deleted)")
        return True
        
    except Exception as e:
        print(f"❌ Error removing product {product_id} from collection {collection_id}: {e}")
        return False

def cleanup_collections():
    """Remove products from 'NEEDS TO BE DONE' collection that are already in 'READY FOR PINTEREST' collection"""
    if not SHOPIFY_API_KEY:
        print("❌ Cannot cleanup collections: Shopify API Key is missing.")
        return False
    
    needs_done_collection_id = "644626448708"  # NEEDS TO BE DONE
    ready_collection_id = "644749033796"       # READY FOR PINTEREST
    
    print(f"🧹 Starting collection cleanup...")
    print(f"   📋 Checking 'NEEDS TO BE DONE' collection (ID: {needs_done_collection_id})")
    print(f"   📋 Checking 'READY FOR PINTEREST' collection (ID: {ready_collection_id})")
    
    try:
        # Keep trying until no more duplicates are found
        total_removed = 0
        iteration = 1
        
        while True:
            print(f"\n🔄 Cleanup iteration {iteration}...")
            
            # Get products from both collections
            needs_done_products = get_collection_products(needs_done_collection_id)
            ready_products = get_collection_products(ready_collection_id)
            
            if not needs_done_products:
                print("✅ No products in 'NEEDS TO BE DONE' collection to clean up")
                break
            
            if not ready_products:
                print("⚠️ No products in 'READY FOR PINTEREST' collection for comparison")
                break
            
            # Create sets of product IDs for comparison
            needs_done_ids = {str(product["id"]) for product in needs_done_products}
            ready_ids = {str(product["id"]) for product in ready_products}
            
            # Find duplicates
            duplicates = needs_done_ids.intersection(ready_ids)
            
            if not duplicates:
                print("✅ No duplicate products found between collections")
                break
            
            print(f"🔄 Found {len(duplicates)} duplicate products to remove from 'NEEDS TO BE DONE' collection")
            
            # Remove duplicates from 'NEEDS TO BE DONE' collection
            removed_count = 0
            rate_limited = False
            
            for product_id in duplicates:
                try:
                    if remove_product_from_collection(needs_done_collection_id, product_id):
                        removed_count += 1
                except Exception as e:
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        print(f"⏳ Rate limit hit, will retry after delay...")
                        rate_limited = True
                        break
                    else:
                        print(f"❌ Error removing product {product_id}: {e}")
            
            total_removed += removed_count
            print(f"✅ Iteration {iteration} completed: {removed_count} products removed (total: {total_removed})")
            
            # If we hit rate limits or still have duplicates, wait and try again
            if rate_limited or removed_count > 0:
                print("⏳ Waiting 30 seconds before next iteration...")
                import time
                time.sleep(30)
                iteration += 1
            else:
                break
        
        print(f"✅ Collection cleanup completed: {total_removed} products removed in {iteration} iteration(s)")
        return True
        
    except Exception as e:
        print(f"❌ Collection cleanup failed: {e}")
        return False

# ✅ Step Functions for 3-Step Workflow

def run_step1_content_generation(collection_id, image_limit=10):
    """Step 1: Content Generation - Fetch products, generate AI content, save to Google Sheets"""
    try:
        # Get collection name for display
        collections_dict = fetch_collections()
        collection_name = collections_dict.get(str(collection_id), f"Collection {collection_id}")
        
        print(f"\n--- Starting Step 1: Content Generation for Collection: {collection_name} ---")
        update_automation_status('running', 'Step 1: Fetching Shopify Product Data...')

        # Step 0: Clean up collections before processing
        print("\n[Step 0/3] Cleaning up collections...")
        cleanup_success = cleanup_collections()
        if not cleanup_success:
            print("⚠️ Collection cleanup failed, but continuing with content generation...")
        
        # Step 0.5: Move processed products to GENERATED collection
        print("\n[Step 0.5/3] Moving processed products to GENERATED collection...")
        try:
            from a import move_processed_products_to_generated_collection
            move_success = move_processed_products_to_generated_collection()
            if move_success:
                print("✅ Successfully moved processed products to GENERATED collection")
            else:
                print("ℹ️ No processed products found to move")
        except Exception as e:
            print(f"⚠️ Error moving processed products: {e}")
            print("Continuing with content generation...")

        # Step 1: Fetch data from Shopify
        print("\n[Step 1/3] Fetching Shopify Product Data...")
        image_data = fetch_product_data(collection_id, image_limit)
        if not image_data:
            error_msg = f"No product data fetched for collection {collection_id}"
            print(f"❌ Step 1 stopped: {error_msg}")
            update_automation_status('error', 'Failed to fetch products', error_msg)
            return

        # Update progress with total items found
        with progress_lock:
            automation_progress['total_items'] = len(image_data)
        
        print(f"✅ Found {len(image_data)} products to process")

        # Step 2: Generate AI content
        print("\n[Step 2/3] Generating AI Text...")
        update_automation_status('running', 'Step 1: Generating AI content...')
        ai_results = generate_ai_pin_text_batch(image_data)
        
        # Step 3: Save data to Google Sheets
        print("\n[Step 3/3] Saving to Google Sheets...")
        update_automation_status('running', 'Step 1: Saving to Google Sheets...')
        save_to_google_sheets_with_ai(image_data, ai_results)

        print(f"\n--- Step 1 Completed for Collection: {collection_name} ---")
        update_automation_status('completed', 'Step 1: Content generation completed successfully!')
        
    except Exception as e:
        error_msg = f"Step 1 failed: {str(e)}"
        print(f"❌ {error_msg}")
        update_automation_status('error', 'Step 1 failed', error_msg)

def run_step1_content_generation_enhanced(collection_id, image_limit=10):
    """
    Enhanced Step 1: Content Generation with Pinterest Trends and Customer Persona Integration
    Fetch products, generate AI content with trending keywords and audience insights, save to Google Sheets
    """
    try:
        # Enhanced Pinterest integration imports
        import sys
        meta_change_path = '/Users/saschavanwell/Documents/meta-change'
        sys.path.append(meta_change_path)
        
        try:
            from pin_generation_enhancement import PinGenerationEnhancement
            print("✅ Enhanced Pinterest integration modules loaded")
            ENHANCED_FEATURES_AVAILABLE = True
        except ImportError as e:
            print(f"⚠️ Could not load enhanced integration modules: {e}")
            PinGenerationEnhancement = None
            ENHANCED_FEATURES_AVAILABLE = False
        
        # Enhanced features configuration
        ENHANCED_FEATURES_ENABLED = True
        TRENDING_KEYWORDS_ENABLED = True
        AUDIENCE_INSIGHTS_ENABLED = True
        DEFAULT_REGION = "DE"
        
        # Initialize enhanced integration
        enhanced_pin_generation = None
        if ENHANCED_FEATURES_AVAILABLE and PinGenerationEnhancement:
            try:
                enhanced_pin_generation = PinGenerationEnhancement()
                print("✅ Enhanced pin generation initialized")
            except Exception as e:
                print(f"⚠️ Error initializing enhanced pin generation: {e}")
                enhanced_pin_generation = None
        
        # Get collection name for display
        collections_dict = fetch_collections()
        collection_name = collections_dict.get(str(collection_id), f"Collection {collection_id}")
        
        print(f"\n--- Starting Enhanced Step 1: Content Generation for Collection: {collection_name} ---")
        update_automation_status('running', 'Enhanced Step 1: Fetching Shopify Product Data...')

        # Step 0: Clean up collections before processing
        print("\n[Step 0/3] Cleaning up collections...")
        cleanup_success = cleanup_collections()
        if not cleanup_success:
            print("⚠️ Collection cleanup failed, but continuing with content generation...")
        
        # Step 0.5: Move processed products to GENERATED collection
        print("\n[Step 0.5/3] Moving processed products to GENERATED collection...")
        try:
            from a import move_processed_products_to_generated_collection
            move_success = move_processed_products_to_generated_collection()
            if move_success:
                print("✅ Successfully moved processed products to GENERATED collection")
            else:
                print("ℹ️ No processed products found to move")
        except Exception as e:
            print(f"⚠️ Error moving processed products: {e}")
            print("Continuing with content generation...")

        # Step 1: Fetch data from Shopify
        print("\n[Step 1/3] Fetching Shopify Product Data...")
        image_data = fetch_product_data(collection_id, image_limit)
        if not image_data:
            error_msg = f"No product data fetched for collection {collection_id}"
            print(f"❌ Step 1 stopped: {error_msg}")
            update_automation_status('error', 'Failed to fetch products', error_msg)
            return

        # Update progress with total items found
        with progress_lock:
            automation_progress['total_items'] = len(image_data)
        
        print(f"✅ Found {len(image_data)} products to process")

        # Enhanced Step 2: Generate AI content with Pinterest trends and customer persona
        print("\n[Step 2/3] Generating Enhanced AI Text with Pinterest Trends and Customer Persona...")
        update_automation_status('running', 'Enhanced Step 1: Generating AI content with Pinterest trends...')
        
        if ENHANCED_FEATURES_ENABLED and enhanced_pin_generation:
            print("🎯 Using enhanced AI generation with Pinterest trends and audience insights...")
            try:
                # Get customer persona for better targeting
                print("👤 Fetching customer persona insights...")
                audience_insights = enhanced_pin_generation.get_audience_insights()
                if audience_insights:
                    persona = enhanced_pin_generation.generate_customer_persona(audience_insights)
                    print(f"✅ Customer persona generated: {persona.get('persona_name', 'Unknown')}")
                    print(f"   Demographics: {persona.get('demographics', {})}")
                    print(f"   Target Keywords: {persona.get('target_keywords', [])}")
                else:
                    print("⚠️ No audience insights available, using default targeting")
                    persona = None
                
                # Generate enhanced AI content
                ai_results = []
                for i, data in enumerate(image_data):
                    try:
                        print(f"   Processing pin {i+1}/{len(image_data)}: {data[1] if len(data) > 1 else 'Unknown'}")
                        
                        # Generate enhanced title and description
                        enhanced_title = enhanced_pin_generation.generate_enhanced_pin_title(
                            data, use_trending_keywords=True, region=DEFAULT_REGION
                        )
                        enhanced_description = enhanced_pin_generation.generate_enhanced_pin_description(
                            data, use_trending_keywords=True, region=DEFAULT_REGION
                        )
                        
                        # Use existing board title logic
                        product_name = data[1] if len(data) > 1 else ""
                        product_type = data[4] if len(data) > 4 else ""
                        board_key = product_name if product_name else product_type
                        
                        # Enhanced board title mapping with trending keywords
                        board_title = "Trend-Produkte"  # Default
                        if "dress" in board_key.lower() or "kleid" in board_key.lower():
                            board_title = "Bestseller Kleider"
                        elif "shoes" in board_key.lower() or "schuhe" in board_key.lower():
                            board_title = "Schuhe & Boots Trends"
                        elif "bag" in board_key.lower() or "tasche" in board_key.lower():
                            board_title = "Trendige Accessoires"
                        
                        ai_results.append((enhanced_title, enhanced_description, board_title))
                        
                    except Exception as e:
                        print(f"❌ Error processing pin {i+1}: {e}")
                        # Fallback to original format
                        name = data[1].replace('_', ' ') if len(data) > 1 else "Produkt"
                        ai_results.append((f"{name} – Jetzt entdecken!", "Ein Must-Have für 2025! #Trend #Fashion", "Trend-Produkte"))
                
                print(f"✅ Enhanced AI generation completed: {len(ai_results)} results")
                
            except Exception as e:
                print(f"⚠️ Enhanced AI generation failed, using fallback: {e}")
                # Fallback to original function
                ai_results = generate_ai_pin_text_batch(image_data)
        else:
            print("⚠️ Enhanced features not available, using original AI generation...")
            ai_results = generate_ai_pin_text_batch(image_data)

        # Step 3: Save data to Google Sheets
        print("\n[Step 3/3] Saving to Google Sheets...")
        update_automation_status('running', 'Enhanced Step 1: Saving to Google Sheets...')
        
        # Combine image data with AI results
        combined_data = []
        for i, (image_info, ai_info) in enumerate(zip(image_data, ai_results)):
            title, description, board_title = ai_info
            combined_data.append(image_info + [title, description, board_title])
        
        # Save to Google Sheets
        save_success = save_to_google_sheets(combined_data)
        if not save_success:
            error_msg = "Failed to save data to Google Sheets"
            print(f"❌ Step 1 stopped: {error_msg}")
            update_automation_status('error', 'Failed to save to Google Sheets', error_msg)
            return

        print(f"\n--- Enhanced Step 1 Completed for Collection: {collection_name} ---")
        print(f"✅ Enhanced content generation completed with Pinterest trends and customer persona integration!")
        update_automation_status('completed', 'Enhanced Step 1: Content generation completed successfully!')
        
    except Exception as e:
        error_msg = f"Enhanced Step 1 failed: {str(e)}"
        print(f"❌ {error_msg}")
        update_automation_status('error', 'Enhanced Step 1 failed', error_msg)

def run_step2_pinterest_posting(delay_between_posts=45, max_posts=0):
    """Step 2: Pinterest Posting - Post pins to Pinterest with rate limiting"""
    try:
        if delay_between_posts == 0:
            print(f"\n--- Starting Step 2: Pinterest Posting (NO DELAY - fastest mode, max: {max_posts}) ---")
        else:
            print(f"\n--- Starting Step 2: Pinterest Posting (delay: {delay_between_posts}s, max: {max_posts}) ---")
        update_automation_status('running', 'Step 2: Starting Pinterest posting...')
        
        # Step 0: Clean up collections before posting (additional safety check)
        print("\n[Step 0/2] Cleaning up collections before posting...")
        cleanup_success = cleanup_collections()
        if not cleanup_success:
            print("⚠️ Collection cleanup failed, but continuing with Pinterest posting...")
        
        # Import and run Pinterest posting with custom delay
        import pinterest_post
        
        # Update the delay in the pinterest_post module
        pinterest_post.DELAY_BETWEEN_POSTS = delay_between_posts
        
        # Run the posting
        pinterest_post.main()
        
        print(f"\n--- Step 2 Completed: Pinterest Posting ---")
        update_automation_status('completed', 'Step 2: Pinterest posting completed successfully!')
        
    except Exception as e:
        error_msg = f"Step 2 failed: {str(e)}"
        print(f"❌ {error_msg}")
        update_automation_status('error', 'Step 2 failed', error_msg)

def run_step3_campaign_creation(campaign_mode="single_product", products_per_campaign=1, daily_budget=100, campaign_type="WEB_CONVERSION", target_language="de", enable_second_sheet=False, second_sheet_id="", campaign_start_date="next_tuesday", custom_start_date=""):
    """Step 3: Campaign Creation - Create Pinterest ad campaigns"""
    try:
        print(f"\n--- Starting Step 3: Campaign Creation (mode: {campaign_mode}, products per campaign: {products_per_campaign}, second sheet: {enable_second_sheet}) ---")
        update_automation_status('running', f'Step 3: Creating Pinterest campaigns in {campaign_mode} mode...')
        
        # Add current directory to Python path to ensure utils module can be found
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Import and run the campaign creation
        import a
        result = a.run(campaign_mode=campaign_mode, products_per_campaign=products_per_campaign, daily_budget=daily_budget, campaign_type=campaign_type, target_language=target_language, enable_second_sheet=enable_second_sheet, second_sheet_id=second_sheet_id, campaign_start_date=campaign_start_date, custom_start_date=custom_start_date)
        
        if result == "NO_ELIGIBLE_PINS":
            print(f"\n--- Step 3 Completed: No eligible pins found - automation run complete ---")
            update_automation_status('completed', 'Step 3: No eligible pins found - automation run complete!')
            return "NO_ELIGIBLE_PINS"
        else:
            print(f"\n--- Step 3 Completed: Campaign Creation ---")
            update_automation_status('completed', 'Step 3: Campaign creation completed successfully!')
            return True
        
    except Exception as e:
        error_msg = f"Step 3 failed: {str(e)}"
        print(f"❌ {error_msg}")
        update_automation_status('error', 'Step 3 failed', error_msg)

# ✅ Original Combined Process (Enhanced with Progress Tracking)
def run_automation_flow(collection_id, image_limit=10, campaign_mode="single_product", products_per_campaign=1):
    try:
        # Get collection name for display
        collections_dict = fetch_collections()
        collection_name = collections_dict.get(str(collection_id), f"Collection {collection_id}")
        
        # Initialize progress tracking
        with progress_lock:
            automation_progress.update({
                'status': 'running',
                'collection_id': str(collection_id),
                'collection_name': collection_name,
                'start_time': datetime.datetime.now().isoformat(),
                'current_step': 'Initializing...',
                'progress_percent': 0,
                'total_items': 0,
                'processed_items': 0,
                'error_message': '',
                'logs': []
            })
        
        print(f"\n--- Starting Automation for Collection: {collection_name} (ID: {collection_id}) ---")
        update_automation_status('running', 'Fetching Shopify Product Data...')

        # Step 0: Clean up collections before processing
        print("\n[Step 0/3] Cleaning up collections...")
        cleanup_success = cleanup_collections()
        if not cleanup_success:
            print("⚠️ Collection cleanup failed, but continuing with automation...")

        # Step 1: Fetch data from Shopify
        print("\n[Step 1/3] Fetching Shopify Product Data...")
        image_data = fetch_product_data(collection_id, image_limit)
        if not image_data:
            error_msg = f"No product data fetched for collection {collection_id}"
            print(f"❌ Automation stopped: {error_msg}")
            update_automation_status('error', 'Failed to fetch products', error_msg)
            return

        # Update progress with total items found
        with progress_lock:
            automation_progress['total_items'] = len(image_data)
        
        print(f"✅ Found {len(image_data)} products to process")

        # Step 2: Generate AI content
        print("\n[Step 2/3] Generating AI Text...")
        update_automation_status('running', 'Generating AI content...')
        ai_results = generate_ai_pin_text_batch(image_data)
        
        # Step 3: Save data to Google Sheets
        print("\n[Step 3/3] Saving to Google Sheets...")
        update_automation_status('running', 'Saving to Google Sheets...')
        save_to_google_sheets_with_ai(image_data, ai_results)

        print(f"\n--- Step 1-3 Completed for Collection: {collection_name} ---")
        print("✅ Content generation completed! You can now run Step 2 (Pinterest posting) or Step 3 (Campaign creation) separately.")
        update_automation_status('completed', 'Content generation completed! Ready for Pinterest posting or campaign creation.')
        
    except Exception as e:
        error_msg = f"Automation failed: {str(e)}"
        print(f"❌ {error_msg}")
        update_automation_status('error', 'Automation failed', error_msg)


# ✅ Flask Routes
@app.route("/process", methods=["POST"])
def process_collection():
    collection_id = request.form.get("collection_id")
    image_limit = request.form.get("image_limit", 3)
    campaign_mode = request.form.get("campaign_mode", "single_product")
    products_per_campaign = request.form.get("products_per_campaign", 1)
    
    if not collection_id:
         flash("⚠️ Please select a collection.", "error")
         return redirect(url_for("index"))

    # Check if Shopify key is loaded before starting thread
    if not SHOPIFY_API_KEY:
         flash("❌ Cannot start process: Shopify API Key is missing.", "error")
         return redirect(url_for("index"))

    # Convert image_limit to int and validate
    try:
        image_limit = int(image_limit)
        if image_limit < 1 or image_limit > 10:
            image_limit = 3
    except (ValueError, TypeError):
        image_limit = 3
    
    # Validate campaign mode
    if campaign_mode not in ["single_product", "multi_product"]:
        campaign_mode = "single_product"
    
    # Convert products_per_campaign to int and validate
    try:
        products_per_campaign = int(products_per_campaign)
        if products_per_campaign < 2 or products_per_campaign > 50:
            products_per_campaign = 10
    except (ValueError, TypeError):
        products_per_campaign = 10
    
    # For single_product mode, force products_per_campaign to 1
    if campaign_mode == "single_product":
        products_per_campaign = 1

    # Run the automation flow in a background thread
    # Consider using Flask-Executor or Celery for more robust background tasks
    print(f"🚀 Starting background processing for collection: {collection_id} (images per product: {image_limit}, campaign mode: {campaign_mode}, products per campaign: {products_per_campaign})")
    thread = threading.Thread(target=run_automation_flow, args=(collection_id, image_limit, campaign_mode, products_per_campaign))
    thread.start()

    flash(f"✅ Background processing started for collection ID: {collection_id} with {image_limit} images per product, campaign mode: {campaign_mode}. Check status page for progress.", "success")
    return redirect(url_for("status_page"))

@app.route("/dashboard")
def dashboard():
    """Dashboard route to display system statistics and status"""
    # Get basic system stats
    stats = {
        'total_users': 'N/A',
        'active_oauth_accounts': 'N/A', 
        'system_configs': 'N/A',
        'health_metrics': 'N/A'
    }
    
    # Check if API keys are loaded
    if SHOPIFY_API_KEY:
        stats['shopify_status'] = 'Connected'
    else:
        stats['shopify_status'] = 'Not Connected'
        
    if DEEPSEEK_API_KEY:
        stats['ai_status'] = 'Connected'
    else:
        stats['ai_status'] = 'Not Connected'
        
    # Check Google Sheets connection
    try:
        sheet_info = sheet.get_all_records()
        stats['google_sheets_status'] = f'Connected ({len(sheet_info)} records)'
    except Exception as e:
        stats['google_sheets_status'] = f'Error: {str(e)[:50]}...'
    
    return render_template("dashboard.html", stats=stats)

@app.route("/")
def index():
    # Fetch collections for the dropdown
    collections_dict = fetch_collections()
    # Convert to list of tuples for the template
    collections_list = list(collections_dict.items())

    # Optional: Sort collections alphabetically by name for better UI
    collections_list.sort(key=lambda item: item[1])

    print("\n🔍 DEBUG: Rendering index page with collections:")
    # Print only first few for brevity in logs
    print(collections_list[:5])
    if not collections_list:
         flash("⚠️ Could not fetch Shopify collections. Check API key and store connection.", "warning")

    return render_template("index.html", collections=collections_list)

@app.route("/progress")
def get_progress():
    """API endpoint to get current automation progress"""
    with progress_lock:
        return automation_progress

@app.route("/status")
def status_page():
    """Status page showing current automation progress"""
    with progress_lock:
        progress_data = automation_progress.copy()
    
    return render_template("status.html", progress=progress_data)

# ✅ Step 1: Content Generation Routes
@app.route("/step1")
def step1_page():
    """Step 1: Content Generation page"""
    collections = fetch_collections()
    return render_template("step1.html", collections=collections)

@app.route("/step1/process", methods=["POST"])
def step1_process():
    """Process Step 1: Content Generation"""
    collection_id = request.form.get("collection_id")
    image_limit = request.form.get("image_limit", 3)
    
    if not collection_id:
        flash("⚠️ Please select a collection.", "error")
        return redirect(url_for("step1_page"))

    if not SHOPIFY_API_KEY:
        flash("❌ Cannot start process: Shopify API Key is missing.", "error")
        return redirect(url_for("step1_page"))

    try:
        image_limit = int(image_limit)
        if image_limit < 1 or image_limit > 10:
            image_limit = 3
    except (ValueError, TypeError):
        image_limit = 3

    print(f"🚀 Starting Step 1: Content Generation for collection: {collection_id} (images per product: {image_limit})")
    thread = threading.Thread(target=run_step1_content_generation, args=(collection_id, image_limit))
    thread.start()

    flash(f"✅ Step 1 started: Content generation for collection ID: {collection_id} with {image_limit} images per product. Check status page for progress.", "success")
    return redirect(url_for("status_page"))

# ✅ Step 2: Pinterest Posting Routes
@app.route("/step2")
def step2_page():
    """Step 2: Pinterest Posting page"""
    return render_template("step2.html")

@app.route("/step2/process", methods=["POST"])
def step2_process():
    """Process Step 2: Pinterest Posting"""
    delay_between_posts = request.form.get("delay_between_posts", 45)
    max_posts = request.form.get("max_posts", 0)
    
    try:
        delay_between_posts = int(delay_between_posts)
        max_posts = int(max_posts)
    except (ValueError, TypeError):
        delay_between_posts = 45
        max_posts = 0

    print(f"🚀 Starting Step 2: Pinterest Posting (delay: {delay_between_posts}s, max posts: {max_posts})")
    thread = threading.Thread(target=run_step2_pinterest_posting, args=(delay_between_posts, max_posts))
    thread.start()

    if delay_between_posts == 0:
        flash(f"✅ Step 2 started: Pinterest posting with NO DELAY (fastest mode). Check status page for progress.", "success")
    else:
        flash(f"✅ Step 2 started: Pinterest posting with {delay_between_posts}s delay. Check status page for progress.", "success")
    return redirect(url_for("status_page"))

# ✅ Step 3: Campaign Creation Routes
@app.route("/step3")
def step3_page():
    """Step 3: Campaign Creation page"""
    return render_template("step3.html")

@app.route("/step3/process", methods=["POST"])
def step3_process():
    """Process Step 3: Campaign Creation"""
    campaign_type = request.form.get("campaign_type", "WEB_CONVERSION")
    campaign_mode = request.form.get("campaign_mode", "single_product")
    products_per_campaign = request.form.get("products_per_campaign", 1)
    daily_budget = request.form.get("daily_budget", 100)
    print(f"[DEBUG] Frontend daily_budget input: '{daily_budget}' (type: {type(daily_budget)})")
    target_language = request.form.get("target_language", "de")
    enable_second_sheet = request.form.get("enable_second_sheet") == "true"
    second_sheet_id = request.form.get("second_sheet_id", "").strip()
    campaign_start_date = request.form.get("campaign_start_date", "next_tuesday")
    custom_start_date = request.form.get("custom_start_date", "")
    
    # Validate campaign type
    if campaign_type not in ["WEB_CONVERSION", "CONSIDERATION", "CATALOG_SALES"]:
        campaign_type = "WEB_CONVERSION"
    
    # Validate campaign mode
    if campaign_mode not in ["single_product", "multi_product"]:
        campaign_mode = "single_product"
    
    # Validate target language
    if target_language not in ["en", "de", "fr", "es", "it", "nl", "pt"]:
        target_language = "de"
    
    # Validate second sheet
    if enable_second_sheet and not second_sheet_id:
        flash("❌ Second sheet ID is required when enabling second sheet.", "error")
        return redirect(url_for("step3_page"))
    
    # Validate start date
    if campaign_start_date not in ["immediate", "next_tuesday", "custom"]:
        campaign_start_date = "next_tuesday"
    
    # Validate custom date if provided
    if campaign_start_date == "custom":
        if not custom_start_date:
            flash("❌ Custom start date is required when 'Custom Date' is selected.", "error")
            return redirect(url_for("step3_page"))
        # Validate date format and ensure it's not in the past
        try:
            import datetime
            custom_date = datetime.datetime.strptime(custom_start_date, "%Y-%m-%d").date()
            today = datetime.date.today()
            if custom_date < today:
                flash("❌ Custom start date cannot be in the past.", "error")
                return redirect(url_for("step3_page"))
        except ValueError:
            flash("❌ Invalid custom start date format.", "error")
            return redirect(url_for("step3_page"))
    
    try:
        products_per_campaign = int(products_per_campaign)
        daily_budget = int(daily_budget)
        print(f"[DEBUG] After parsing: daily_budget = {daily_budget} (type: {type(daily_budget)})")
        if products_per_campaign < 2 or products_per_campaign > 50:
            products_per_campaign = 10
        if daily_budget < 1:  # Minimum 1 cent
            daily_budget = 1
            print(f"[DEBUG] Daily budget was < 1, set to minimum: {daily_budget}")
    except (ValueError, TypeError) as e:
        print(f"[DEBUG] Error parsing daily_budget: {e}, using default 100")
        products_per_campaign = 10
        daily_budget = 100  # Default to 1 euro
    
    if campaign_mode == "single_product":
        products_per_campaign = 1

    print(f"🚀 Starting Step 3: Campaign Creation (type: {campaign_type}, mode: {campaign_mode}, products per campaign: {products_per_campaign}, budget: {daily_budget}, language: {target_language}, second sheet: {enable_second_sheet}, start date: {campaign_start_date})")
    thread = threading.Thread(target=run_step3_campaign_creation, args=(campaign_mode, products_per_campaign, daily_budget, campaign_type, target_language, enable_second_sheet, second_sheet_id, campaign_start_date, custom_start_date))
    thread.start()

    start_date_msg = "immediately" if campaign_start_date == "immediate" else f"on {custom_start_date}" if campaign_start_date == "custom" else "next Tuesday"
    flash(f"✅ Step 3 started: Campaign creation ({campaign_type}) in {campaign_mode} mode, starting {start_date_msg}. Check status page for progress.", "success")
    return redirect(url_for("status_page"))


if __name__ == "__main__":
    print("--- Initializing Application ---")
    # Add final checks before running
    if not DEEPSEEK_API_KEY:
        print("CRITICAL WARNING: DEEPSEEK client not initialized. AI features will be disabled or fail.")
    if not SHOPIFY_API_KEY:
         print("CRITICAL WARNING: Shopify API Key not loaded. Shopify interactions will fail.")
    # Add check for Google Sheets client?
    # if not sheet: print("CRITICAL WARNING: Google Sheet connection failed.")

    # Start Flask development server
    print("Starting Flask server on http://0.0.0.0:5002 (Press CTRL+C to quit)")
    # debug=True enables auto-reloading AND the interactive debugger (requires PIN)
    # Use debug=False in production
    app.run(host="0.0.0.0", port=5002, debug=False)