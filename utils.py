import os
import gspread
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Sheets configuration
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = os.getenv("SHEET_ID")

# Headers for the Google Sheet
HEADERS = [
    "Image URL", "Product Name", "Product URL", "Product Price", "Product Type", "Collection Name",
    "Tags", "Review Summary", "Generated Pin Title", "Generated Pin Description", "Board Title", 
    "Status", "Board ID", "Pin ID", "Status2", "Ad Campaign ID", "Advertised At"
]

# Cache for sheet data
_sheet_cache = None
_sheet_data_cache = None

def get_sheet_cached():
    """Get Google Sheet with caching"""
    global _sheet_cache
    if _sheet_cache is None:
        try:
            credentials = service_account.Credentials.from_service_account_file(
                CREDENTIALS_FILE,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            gc = gspread.authorize(credentials)
            _sheet_cache = gc.open_by_key(SPREADSHEET_ID).sheet1
            print(f"✅ Connected to Google Sheet ID: {SPREADSHEET_ID}")
        except Exception as e:
            print(f"❌ Error connecting to Google Sheet: {e}")
            return None
    return _sheet_cache

def get_sheet_data(sheet):
    """Get sheet data with headers and rows"""
    global _sheet_data_cache
    # Clear cache to force refresh with new headers
    _sheet_data_cache = None
    if _sheet_data_cache is None:
        try:
            all_data = sheet.get_all_values()
            if not all_data:
                return HEADERS, []
            
            # Check if first row matches headers
            if all_data[0] == HEADERS:
                headers = all_data[0]
                data_rows = all_data[1:]
            else:
                # Headers don't match, use our standard headers
                headers = HEADERS
                data_rows = all_data
            
            _sheet_data_cache = (headers, data_rows)
        except Exception as e:
            print(f"❌ Error getting sheet data: {e}")
            return HEADERS, []
    
    return _sheet_data_cache

def load_pins_from_sheet():
    """Load pins from Google Sheet, grouped by product name"""
    sheet = get_sheet_cached()
    if not sheet:
        return {}
    
    headers, data_rows = get_sheet_data(sheet)
    print(f"📊 DEBUG: Found {len(data_rows)} rows in Google Sheet")
    print(f"📊 DEBUG: Headers: {headers}")
    print(f"📊 DEBUG: First 3 data rows:")
    for i, row in enumerate(data_rows[:3]):
        print(f"   Row {i+2}: {row[:5]}...")  # Show first 5 columns
        print(f"   Row {i+2} full row length: {len(row)}")
        if len(row) > 13:
            print(f"   Row {i+2} Pin ID column (index 13): '{row[13]}'")
        else:
            print(f"   Row {i+2}: Row too short, only {len(row)} columns")
        # Show all columns for debugging
        print(f"   Row {i+2} all columns: {row}")
    
    pins_by_product = {}
    eligible_count = 0
    skipped_reasons = {}
    
    for row_idx, row in enumerate(data_rows):
        if len(row) < len(HEADERS):
            # Pad row with empty strings if it's too short
            row = row + [""] * (len(HEADERS) - len(row))
        
        row_data = dict(zip(HEADERS, row))
        
        # Debug first few rows to see what data we're getting
        if row_idx < 3:
            print(f"🔍 DEBUG Row {row_idx + 2}: Status='{row_data.get('Status', '')}', Pin ID='{row_data.get('Pin ID', '')}', Product Name='{row_data.get('Product Name', '')[:30]}...'")
            print(f"🔍 DEBUG Row {row_idx + 2} RAW: {row[13] if len(row) > 13 else 'N/A'}")  # Show raw Pin ID column
        
        # Check if this row has the required fields for pin posting
        required_fields = ["Image URL", "Generated Pin Title", "Generated Pin Description", "Board Title", "Product URL"]
        missing_fields = [field for field in required_fields if not row_data.get(field) or not row_data.get(field).strip()]
        if missing_fields:
            skipped_reasons["missing_fields"] = skipped_reasons.get("missing_fields", 0) + 1
            if row_idx < 5:  # Show details for first 5 rows
                print(f"⚠️ Row {row_idx + 2}: Missing fields: {missing_fields}")
            continue
        
        # Check if pin is already posted to Pinterest (Status = "POSTED" is required)
        status = row_data.get("Status", "").strip().upper()
        if status != "POSTED":
            skipped_reasons["not_posted"] = skipped_reasons.get("not_posted", 0) + 1
            if row_idx < 5:
                print(f"⚠️ Row {row_idx + 2}: Status is not POSTED (current: {status})")
            continue
        
        # Check if pin has a Pin ID (already posted to Pinterest)
        pin_id = row_data.get("Pin ID", "").strip()
        if not pin_id:
            skipped_reasons["no_pin_id"] = skipped_reasons.get("no_pin_id", 0) + 1
            if row_idx < 5:
                print(f"⚠️ Row {row_idx + 2}: No Pin ID")
            continue
        
        # Check if campaign is already created (Status2 should not be "ACTIVE")
        campaign_status = row_data.get("Status2", "").strip().upper()
        if campaign_status == "ACTIVE":
            skipped_reasons["campaign_already_created"] = skipped_reasons.get("campaign_already_created", 0) + 1
            if row_idx < 5:
                print(f"⚠️ Row {row_idx + 2}: Campaign already created (Status2: {campaign_status})")
            continue
        
        product_name = row_data.get("Product Name", "").strip()
        if not product_name:
            continue
        
        if product_name not in pins_by_product:
            pins_by_product[product_name] = []
        
        pins_by_product[product_name].append({
            'pin_id': row_data.get("Pin ID", "").strip(),
            'product_name': product_name,
            'pin_title': row_data.get("Generated Pin Title", "").strip(),
            'pin_description': row_data.get("Generated Pin Description", "").strip(),
            'board_title': row_data.get("Board Title", "").strip(),
            'product_url': row_data.get("Product URL", "").strip(),
            'row_number': len(pins_by_product[product_name]) + 2  # +2 because sheet starts at row 2
        })
        eligible_count += 1
    
    # Print summary
    print(f"📊 SUMMARY:")
    print(f"   Total rows processed: {len(data_rows)}")
    print(f"   Eligible pins found: {eligible_count}")
    print(f"   Products with pins: {len(pins_by_product)}")
    print(f"   Skip reasons: {skipped_reasons}")
    
    return pins_by_product

def plan_batch_updates(headers, data_rows, pin_updates):
    """Plan batch updates for Google Sheets"""
    batch_updates = []
    
    # Determine the starting row for data (header row + 1)
    data_start_row = 1  # Assuming headers are in row 1, data starts in row 2, but we want to go one higher
    
    for row_idx, row in enumerate(data_rows):
        if len(row) < len(HEADERS):
            row = row + [""] * (len(HEADERS) - len(row))
        
        row_data = dict(zip(HEADERS, row))
        pin_id = row_data.get("Pin ID", "").strip()
        
        if pin_id in pin_updates:
            updates = pin_updates[pin_id]
            print(f"[DEBUG] Found updates for pin {pin_id}: {updates}")
            for field, value in updates.items():
                if field in headers:
                    col_idx = headers.index(field)
                    # Calculate the actual row number in the sheet
                    sheet_row = row_idx + data_start_row
                    batch_updates.append({
                        'range': f'{chr(65 + col_idx)}{sheet_row}',
                        'values': [[value]]
                    })
                    print(f"[DEBUG] Planning update: {field} = {value} at {chr(65 + col_idx)}{sheet_row} (row_idx={row_idx}, data_start_row={data_start_row})")
                else:
                    print(f"[DEBUG] Field '{field}' not found in headers: {headers}")
    
    return batch_updates

def batch_write_to_sheet(sheet, batch_updates):
    """Write batch updates to Google Sheet"""
    if not batch_updates:
        print("No updates to write to sheet")
        return
    
    try:
        # Use the correct gspread batch_update format
        sheet.batch_update(batch_updates, value_input_option='USER_ENTERED')
        print(f"✅ Successfully updated {len(batch_updates)} cells in Google Sheet")
        
    except Exception as e:
        print(f"❌ Error updating Google Sheet: {e}")
        # Fallback to individual updates
        for update in batch_updates:
            try:
                sheet.update(update['range'], update['values'], value_input_option='USER_ENTERED')
            except Exception as e2:
                print(f"❌ Error updating {update['range']}: {e2}")
