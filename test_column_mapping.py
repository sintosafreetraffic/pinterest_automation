#!/usr/bin/env python3
"""
Test script to verify column mapping for campaign updates
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

def test_column_mapping():
    """Test column mapping by directly updating row 656 with mock campaign data"""
    print("🧪 Testing column mapping for campaign updates...")
    
    try:
        # Import required modules
        from utils import get_sheet_cached, get_sheet_data
        
        # Get the sheet
        sheet = get_sheet_cached()
        if not sheet:
            print("❌ Could not connect to Google Sheet")
            return
        
        print("✅ Connected to Google Sheet")
        
        # Get current data
        headers, data_rows = get_sheet_data(sheet)
        print(f"📊 Found {len(data_rows)} rows in sheet")
        print(f"📋 Headers: {headers}")
        
        # Check if row 656 exists (row index 655 since 0-based)
        if len(data_rows) < 656:
            print(f"⚠️ Sheet only has {len(data_rows)} rows, need at least 656")
            return
        
        # Get row 656 data before update
        row_656_before = sheet.row_values(657)  # Row 657 in sheet (1-based)
        print(f"📋 Row 656 BEFORE update: {row_656_before}")
        
        # Test the column mapping by directly updating the columns
        print("🔧 Testing column mapping...")
        
        # According to the headers, the columns should be:
        # Column O (15): "Ad Campaign Status" 
        # Column P (16): "Ad Campaign ID"
        # Column Q (17): "Advertised At"
        
        # Update row 656 with mock campaign data
        mock_campaign_id = "TEST_CAMPAIGN_12345"
        mock_date = "2025-01-23"
        
        print(f"📝 Updating row 656 with mock data:")
        print(f"   Column O (Ad Campaign Status): ACTIVE")
        print(f"   Column P (Ad Campaign ID): {mock_campaign_id}")
        print(f"   Column Q (Advertised At): {mock_date}")
        
        # Update the cells directly
        sheet.update_cell(657, 16, "ACTIVE")  # Column O (1-based index 16)
        sheet.update_cell(657, 17, mock_campaign_id)  # Column P (1-based index 17)
        sheet.update_cell(657, 18, mock_date)  # Column Q (1-based index 18)
        
        print("✅ Mock data placed in row 656")
        
        # Check the updated row
        print("🔍 Checking updated row 656...")
        row_656_after = sheet.row_values(657)
        print(f"📋 Row 656 AFTER update: {row_656_after}")
        
        # Check specific columns
        print(f"📊 Column O (Ad Campaign Status): '{row_656_after[15] if len(row_656_after) > 15 else 'Not set'}'")
        print(f"📊 Column P (Ad Campaign ID): '{row_656_after[16] if len(row_656_after) > 16 else 'Not set'}'")
        print(f"📊 Column Q (Advertised At): '{row_656_after[17] if len(row_656_after) > 17 else 'Not set'}'")
        
        # Verify the mapping is correct
        if len(row_656_after) > 17:
            if row_656_after[15] == "ACTIVE" and row_656_after[16] == mock_campaign_id and row_656_after[17] == mock_date:
                print("✅ SUCCESS: Column mapping is correct!")
                print("   - Column O (Ad Campaign Status): ACTIVE ✓")
                print("   - Column P (Ad Campaign ID): Campaign ID ✓") 
                print("   - Column Q (Advertised At): Date ✓")
            else:
                print("❌ FAILED: Column mapping is incorrect!")
                print(f"   Expected: ACTIVE, {mock_campaign_id}, {mock_date}")
                print(f"   Got: {row_656_after[15]}, {row_656_after[16]}, {row_656_after[17]}")
        else:
            print("❌ FAILED: Not enough columns in the row")
        
        # Clean up - clear the mock data
        print("🧹 Cleaning up mock data...")
        sheet.update_cell(657, 16, "")  # Clear Column O
        sheet.update_cell(657, 17, "")  # Clear Column P  
        sheet.update_cell(657, 18, "")  # Clear Column Q
        
        print("✅ Test completed and cleaned up!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_column_mapping()
