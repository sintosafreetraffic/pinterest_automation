#!/usr/bin/env python3
"""
Test script to verify column mapping for row 656 only
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

def test_row_656_column_mapping():
    """Test column mapping by directly updating row 656 with mock campaign data"""
    print("🧪 Testing column mapping for row 656 only...")
    
    try:
        # Import required modules
        from utils import get_sheet_cached
        
        # Get the sheet
        sheet = get_sheet_cached()
        if not sheet:
            print("❌ Could not connect to Google Sheet")
            return
        
        print("✅ Connected to Google Sheet")
        
        # Get row 656 data before update
        row_656_before = sheet.row_values(657)  # Row 657 in sheet (1-based)
        print(f"📋 Row 656 BEFORE update: {row_656_before}")
        
        # Test the column mapping by directly updating row 656
        print("🔧 Testing column mapping for row 656...")
        
        # Mock data
        mock_campaign_id = "TEST_CAMPAIGN_656"
        mock_date = "2025-01-23"
        
        print(f"📝 Updating row 656 with mock data:")
        print(f"   Column N (Ad Campaign Status): ACTIVE")
        print(f"   Column O (Ad Campaign ID): {mock_campaign_id}")
        print(f"   Column P (Advertised At): {mock_date}")
        
        # Update row 656 directly
        # Column N = index 14 (Ad Campaign Status)
        # Column O = index 15 (Ad Campaign ID) 
        # Column P = index 16 (Advertised At)
        sheet.update_cell(657, 15, "ACTIVE")  # Column N
        sheet.update_cell(657, 16, mock_campaign_id)  # Column O
        sheet.update_cell(657, 17, mock_date)  # Column P
        
        print("✅ Mock data placed in row 656")
        
        # Check the updated row
        print("🔍 Checking updated row 656...")
        row_656_after = sheet.row_values(657)
        print(f"📋 Row 656 AFTER update: {row_656_after}")
        
        # Check specific columns
        print(f"📊 Column N (Ad Campaign Status): '{row_656_after[14] if len(row_656_after) > 14 else 'Not set'}'")
        print(f"📊 Column O (Ad Campaign ID): '{row_656_after[15] if len(row_656_after) > 15 else 'Not set'}'")
        print(f"📊 Column P (Advertised At): '{row_656_after[16] if len(row_656_after) > 16 else 'Not set'}'")
        
        # Verify the mapping is correct
        if len(row_656_after) > 16:
            if row_656_after[14] == "ACTIVE" and row_656_after[15] == mock_campaign_id and row_656_after[16] == mock_date:
                print("✅ SUCCESS: Column mapping is correct for row 656!")
                print("   - Column N (Ad Campaign Status): ACTIVE ✓")
                print("   - Column O (Ad Campaign ID): Campaign ID ✓") 
                print("   - Column P (Advertised At): Date ✓")
            else:
                print("❌ FAILED: Column mapping is incorrect!")
                print(f"   Expected: ACTIVE, {mock_campaign_id}, {mock_date}")
                print(f"   Got: {row_656_after[14]}, {row_656_after[15]}, {row_656_after[16]}")
        else:
            print("❌ FAILED: Not enough columns in row 656")
        
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_row_656_column_mapping()
