#!/usr/bin/env python3
"""
Test script to debug Pinterest posting issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pinterest_posting():
    """Test the Pinterest posting functionality"""
    print("🔍 Testing Pinterest posting functionality...")
    
    try:
        # Test 1: Import the function
        print("1. Testing import...")
        from pinterest_post import main
        print("✅ Successfully imported pinterest_post.main")
        
        # Test 2: Check if function is callable
        print("2. Testing function callability...")
        if callable(main):
            print("✅ Function is callable")
        else:
            print("❌ Function is not callable")
            return False
        
        # Test 3: Check environment variables
        print("3. Testing environment variables...")
        required_vars = ['PINTEREST_ACCESS_TOKEN', 'SHEET_ID']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            return False
        else:
            print("✅ All required environment variables are set")
        
        # Test 4: Check Google Sheets connection
        print("4. Testing Google Sheets connection...")
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
            client = gspread.authorize(creds)
            
            sheet_id = os.getenv('SHEET_ID')
            sheet = client.open_by_key(sheet_id).sheet1
            data = sheet.get_all_values()
            
            print(f"✅ Google Sheets connection successful - {len(data)} rows found")
            
            # Check how many products are ready for posting
            ready_count = 0
            for row in data[1:]:  # Skip header
                if len(row) > 11:  # Check if we have enough columns
                    status = row[11] if row[11] else 'Empty'
                    if status != 'POSTED':
                        ready_count += 1
            
            print(f"✅ Found {ready_count} products ready for posting")
            
        except Exception as e:
            print(f"❌ Google Sheets connection failed: {e}")
            return False
        
        # Test 5: Try to run the main function
        print("5. Testing Pinterest posting function...")
        try:
            print("🚀 Starting Pinterest posting...")
            main()
            print("✅ Pinterest posting completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Pinterest posting failed: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🧪 Pinterest Posting Test Script")
    print("=" * 50)
    
    success = test_pinterest_posting()
    
    print("=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed!")
        sys.exit(1)
