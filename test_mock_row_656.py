#!/usr/bin/env python3
"""
Test script to test campaign creation with mock data in row 656
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_mock_data_row_656():
    """Test campaign creation with mock data in row 656"""
    print("🧪 Testing campaign creation with mock data in row 656...")
    
    try:
        # Import required modules
        from utils import get_sheet_cached, get_sheet_data
        from a import run
        
        # Get the sheet
        sheet = get_sheet_cached()
        if not sheet:
            print("❌ Could not connect to Google Sheet")
            return
        
        print("✅ Connected to Google Sheet")
        
        # Get current data
        headers, data_rows = get_sheet_data(sheet)
        print(f"📊 Found {len(data_rows)} rows in sheet")
        
        # Check if row 656 exists (row index 655 since 0-based)
        if len(data_rows) < 656:
            print(f"⚠️ Sheet only has {len(data_rows)} rows, need at least 656")
            return
        
        # Get row 656 data
        row_656_data = data_rows[655]  # 0-based index
        print(f"📋 Current row 656 data: {row_656_data}")
        
        # Create mock data for row 656 with a Pin ID
        mock_pin_id = "TEST_PIN_656_12345"
        
        # Update row 656 with mock data
        print(f"🔧 Setting up mock data in row 656...")
        
        # Update the Pin ID column (column N, index 13)
        pin_id_col = 13  # Pin ID is column N (14th column, 0-based index 13)
        sheet.update_cell(657, pin_id_col + 1, mock_pin_id)  # Row 657 in sheet (1-based)
        
        # Update other required columns for testing
        sheet.update_cell(657, 2, "https://example.com/product")  # Product URL
        sheet.update_cell(657, 1, "Test Product 656")  # Product Name
        
        print(f"✅ Set mock Pin ID '{mock_pin_id}' in row 656")
        
        # Now test the campaign creation
        print("📊 Running campaign creation...")
        result = run(
            campaign_mode="single_product",
            products_per_campaign=1,
            daily_budget=1000,  # 10 euro in cents
            campaign_type="WEB_CONVERSION",
            target_language="de",
            enable_second_sheet=False,
            second_sheet_id="",
            campaign_start_date="next_tuesday",
            custom_start_date=""
        )
        
        print(f"📊 Campaign creation result: {result}")
        
        # Check the updated row 656
        print("🔍 Checking updated row 656...")
        updated_row = sheet.row_values(657)
        print(f"📋 Updated row 656: {updated_row}")
        
        # Check specific columns
        print(f"📊 Column O (Ad Campaign Status): {updated_row[15] if len(updated_row) > 15 else 'Not set'}")
        print(f"📊 Column P (Ad Campaign ID): {updated_row[16] if len(updated_row) > 16 else 'Not set'}")
        print(f"📊 Column Q (Advertised At): {updated_row[17] if len(updated_row) > 17 else 'Not set'}")
        
        # Clean up - remove the mock Pin ID
        print("🧹 Cleaning up mock data...")
        sheet.update_cell(657, pin_id_col + 1, "")
        
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mock_data_row_656()
