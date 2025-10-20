#!/usr/bin/env python3
"""
Test script to verify product name extraction from human name | product name format
"""

from a import generate_pin_title, generate_pin_description

def test_product_name_extraction():
    """Test the product name extraction logic"""
    print("🧪 TESTING PRODUCT NAME EXTRACTION")
    print("=" * 60)
    
    # Test cases with human names and product names
    test_cases = [
        "Hannah | Elegante Winterjacke",
        "John | Premium Leder Schuhe", 
        "Peter | Stilvolle Designer Tasche",
        "Sarah | Wunderschönes Kleid",
        "Michael | Komfortable Jeans Hose",
        "Anna | Trendy Sommer Sandalen",
        "David | Luxus Handtasche",
        "Lisa | Elegante Abendkleidung"
    ]
    
    print("📝 Testing Pin Title Generation:")
    print("-" * 40)
    
    for product_name in test_cases:
        print(f"\n🔍 Input: '{product_name}'")
        
        # Test German pin title
        title_de = generate_pin_title(product_name, {}, target_language="de")
        print(f"   🇩🇪 German Title: {title_de}")
        
        # Test English pin title  
        title_en = generate_pin_title(product_name, {}, target_language="en")
        print(f"   🇺🇸 English Title: {title_en}")
        
        print("-" * 40)
    
    print("\n📝 Testing Pin Description Generation:")
    print("-" * 40)
    
    for product_name in test_cases:
        print(f"\n🔍 Input: '{product_name}'")
        
        # Test German pin description
        desc_de = generate_pin_description(product_name, {}, target_language="de")
        print(f"   🇩🇪 German Description: {desc_de}")
        
        # Test English pin description
        desc_en = generate_pin_description(product_name, {}, target_language="en")
        print(f"   🇺🇸 English Description: {desc_en}")
        
        print("-" * 40)
    
    print("\n✅ Product name extraction test completed!")
    print("🎯 Verify that human names (Hannah, John, Peter, etc.) are NOT in the generated content")
    print("🎯 Only the product names should appear in titles and descriptions")

if __name__ == "__main__":
    test_product_name_extraction()
