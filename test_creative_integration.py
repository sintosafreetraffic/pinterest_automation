#!/usr/bin/env python3
"""
Test script for creative integration - Generate 4 creative types for non-ACTIVE rows
"""

import os
import sys
from a import generate_extra_creatives_for_non_active_rows, add_creative_rows_to_sheet
from utils import get_sheet_cached, get_sheet_data

def test_creative_integration():
    """Test the creative integration system"""
    print("🧪 TESTING CREATIVE INTEGRATION")
    print("=" * 60)
    
    try:
        # Get sheet data
        print("📊 Loading sheet data...")
        sheet = get_sheet_cached()
        headers, data_rows = get_sheet_data(sheet)
        
        print(f"📊 Sheet has {len(data_rows)} rows")
        print(f"📊 Headers: {headers}")
        
        # Count non-ACTIVE rows
        non_active_count = 0
        active_count = 0
        
        for row in data_rows:
            if len(row) > 10:  # Ensure we have enough columns
                status2 = row[10] if len(row) > 10 else ""  # Column K (Status2)
                if status2 == 'ACTIVE':
                    active_count += 1
                else:
                    non_active_count += 1
        
        print(f"📊 Status2 breakdown:")
        print(f"   - ACTIVE rows: {active_count}")
        print(f"   - Non-ACTIVE rows: {non_active_count}")
        
        if non_active_count == 0:
            print("✅ All rows are ACTIVE - no extra creatives needed!")
            return
        
        # Test creative generation (without actually adding to sheet)
        print(f"\n🎨 Testing creative generation for non-ACTIVE rows...")
        
        # Generate creatives
        generated_creatives = generate_extra_creatives_for_non_active_rows(
            data_rows, 
            music_folder_path="music", 
            output_dir="creative_examples/test_generated_creatives"
        )
        
        if generated_creatives:
            print(f"\n🎉 Creative generation test completed!")
            print(f"📊 Generated creatives for {len(generated_creatives)} products:")
            
            for product_name, product_data in generated_creatives.items():
                creatives = product_data['creatives']
                print(f"   🎯 {product_name}: {len(creatives)} creatives")
                for creative_type, creative_path in creatives.items():
                    if os.path.exists(creative_path):
                        file_size = os.path.getsize(creative_path)
                        print(f"     ✅ {creative_type}: {creative_path} ({file_size} bytes)")
                    else:
                        print(f"     ❌ {creative_type}: {creative_path} (file not found)")
            
            # Ask user if they want to add rows to sheet
            print(f"\n❓ Do you want to add these creative rows to the sheet?")
            print(f"   This will add {sum(len(p['creatives']) for p in generated_creatives.values())} new rows")
            
            response = input("   Type 'yes' to add rows to sheet, or 'no' to skip: ").lower().strip()
            
            if response == 'yes':
                print(f"\n📝 Adding creative rows to sheet...")
                add_creative_rows_to_sheet(sheet, generated_creatives)
                print(f"✅ Creative rows added to sheet!")
            else:
                print(f"ℹ️ Skipping sheet update - creatives generated but not added to sheet")
        else:
            print(f"❌ No creatives were generated")
        
    except Exception as e:
        print(f"❌ Error in test_creative_integration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_creative_integration()
