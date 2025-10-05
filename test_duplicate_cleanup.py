#!/usr/bin/env python3
"""
Test script for duplicate product cleanup functionality
"""

import sys
import os

# Add the project directory to the path
sys.path.append('/Users/saschavanwell/Documents/shopify-pinterest-automation')

def test_duplicate_cleanup():
    """Test the duplicate cleanup functionality"""
    try:
        print("🧪 Testing Duplicate Product Cleanup")
        print("=" * 50)
        
        # Import the cleanup function
        from scheduler_sheet1 import cleanup_duplicate_products
        
        # Run the cleanup
        print("🔍 Running duplicate cleanup...")
        result = cleanup_duplicate_products()
        
        if result:
            print("✅ Duplicate cleanup test completed successfully")
        else:
            print("❌ Duplicate cleanup test failed")
            
        return result
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_duplicate_cleanup()
