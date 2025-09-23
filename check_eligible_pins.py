#!/usr/bin/env python3
"""
Check which rows have eligible pins for campaign creation
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

def check_eligible_pins():
    """Check which rows have eligible pins for campaigns"""
    print("🔍 Checking eligible pins for campaign creation...")
    
    try:
        # Import the function that loads pins from sheet
        from a import load_pins_from_sheet
        
        # Load pins from sheet
        pins_by_product = load_pins_from_sheet()
        
        if not pins_by_product:
            print("❌ No eligible pins found for advertising")
            return
        
        print(f"📊 Found {len(pins_by_product)} products with eligible pins")
        print(f"📊 Total eligible pins: {sum(len(v) for v in pins_by_product.values())}")
        
        print("\n📋 Products with eligible pins:")
        for i, (product_name, pin_entries) in enumerate(pins_by_product.items(), 1):
            print(f"   {i}. {product_name}")
            print(f"      Pins: {len(pin_entries)}")
            for j, pin_entry in enumerate(pin_entries):
                pin_id = pin_entry.get('pin_id', 'N/A')
                row_number = pin_entry.get('row_number', 'N/A')
                print(f"         Pin {j+1}: {pin_id} (Row {row_number})")
            print()
        
        # Check if we have enough pins for multi-product campaigns
        total_pins = sum(len(v) for v in pins_by_product.values())
        products_count = len(pins_by_product)
        
        print(f"📊 Campaign Analysis:")
        print(f"   - Total products: {products_count}")
        print(f"   - Total pins: {total_pins}")
        print(f"   - Products per campaign: 10")
        print(f"   - Possible campaigns: {products_count // 10}")
        
        if products_count < 10:
            print("⚠️ WARNING: Not enough products for a 10-product campaign!")
            print(f"   Need: 10 products, Have: {products_count}")
        else:
            print(f"✅ Can create {products_count // 10} campaigns with 10 products each")
            remaining = products_count % 10
            if remaining > 0:
                print(f"   + {remaining} products remaining for next run")
        
    except Exception as e:
        print(f"❌ Error checking eligible pins: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_eligible_pins()
