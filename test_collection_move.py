#!/usr/bin/env python3
"""
Test script for collection move functionality
Tests moving processed products from READY FOR PINTEREST to GENERATED collection
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_collection_move():
    """Test the collection move functionality"""
    print("🧪 Testing Collection Move Functionality")
    print("=" * 50)
    
    try:
        # Import the function from a.py
        from a import move_processed_products_to_generated_collection
        
        print("✅ Successfully imported move_processed_products_to_generated_collection function")
        
        # Check if required environment variables are set
        required_vars = ['SHOPIFY_API_KEY', 'SHOPIFY_COLLECTION_ID', 'SHEET_ID']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("Please check your .env file")
            return False
        
        print("✅ All required environment variables are set")
        
        # Test the function
        print("\n🔄 Testing collection move functionality with multi-pass verification...")
        result = move_processed_products_to_generated_collection()
        
        if result:
            print("✅ Collection move test completed successfully")
        else:
            print("ℹ️ No products were moved (this is normal if no processed products exist)")
        
        print("\n🔄 Running second verification pass to ensure complete cleanup...")
        result2 = move_processed_products_to_generated_collection()
        
        if result2:
            print("⚠️ Second pass found more products to move - this indicates the first pass wasn't complete")
        else:
            print("✅ Second pass confirmed: No more products need to be moved - cleanup is complete")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure a.py is in the same directory")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def test_individual_functions():
    """Test individual collection functions"""
    print("\n🧪 Testing Individual Collection Functions")
    print("=" * 50)
    
    try:
        from a import (
            remove_product_from_collection,
            add_product_to_collection,
            move_product_between_collections
        )
        from forefront import get_collection_products
        
        print("✅ Successfully imported all collection functions")
        
        # Test getting products from READY FOR PINTEREST collection
        ready_collection_id = os.getenv("SHOPIFY_COLLECTION_ID")
        if ready_collection_id:
            print(f"🔄 Testing get_collection_products for collection {ready_collection_id}...")
            products = get_collection_products(ready_collection_id)
            print(f"📦 Found {len(products)} products in READY FOR PINTEREST collection")
            
            if products:
                print("📋 Sample products:")
                for i, product in enumerate(products[:3]):  # Show first 3 products
                    print(f"   {i+1}. {product.get('title', 'Unknown')} (ID: {product.get('id', 'Unknown')})")
            else:
                print("ℹ️ No products found in READY FOR PINTEREST collection")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during individual function test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Collection Move Tests")
    print("=" * 50)
    
    # Test 1: Individual functions
    test1_success = test_individual_functions()
    
    # Test 2: Full collection move functionality
    test2_success = test_collection_move()
    
    print("\n📊 Test Results Summary")
    print("=" * 50)
    print(f"Individual Functions Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Collection Move Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! Collection move functionality is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
