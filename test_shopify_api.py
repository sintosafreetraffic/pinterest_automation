#!/usr/bin/env python3
"""
Test script to verify Shopify API connectivity and permissions
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_shopify_api():
    """Test basic Shopify API connectivity and permissions"""
    print("🧪 Testing Shopify API Connectivity")
    print("=" * 50)
    
    # Get environment variables
    admin_api_key = os.getenv("SHOPIFY_API_KEY")
    shop_url = os.getenv("SHOPIFY_STORE_URL")
    api_version = os.getenv("SHOPIFY_API_VERSION", "2023-10")
    
    # Extract domain from full URL
    if shop_url and shop_url.startswith("https://"):
        shop_domain = shop_url.replace("https://", "")
    else:
        shop_domain = shop_url
    
    print(f"📋 Configuration:")
    print(f"   🔑 API Key: {'✅ Set' if admin_api_key else '❌ Missing'}")
    print(f"   🏪 Shop Domain: {shop_domain}")
    print(f"   📅 API Version: {api_version}")
    
    if not admin_api_key or not shop_domain:
        print("❌ Missing required environment variables")
        return False
    
    headers = {"X-Shopify-Access-Token": admin_api_key}
    
    # Test 1: Basic shop info
    print(f"\n🔍 Test 1: Basic Shop Information")
    try:
        url = f"https://{shop_domain}/admin/api/{api_version}/shop.json"
        response = requests.get(url, headers=headers)
        print(f"   📡 URL: {url}")
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            shop_data = response.json()
            print(f"   ✅ Shop Name: {shop_data.get('shop', {}).get('name', 'Unknown')}")
            print(f"   ✅ Shop Domain: {shop_data.get('shop', {}).get('domain', 'Unknown')}")
        else:
            print(f"   ❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    # Test 2: List collections
    print(f"\n🔍 Test 2: List Collections")
    try:
        url = f"https://{shop_domain}/admin/api/{api_version}/collections.json"
        response = requests.get(url, headers=headers)
        print(f"   📡 URL: {url}")
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            collections = response.json().get('collections', [])
            print(f"   ✅ Found {len(collections)} collections")
            for collection in collections[:3]:  # Show first 3
                print(f"      - {collection.get('title')} (ID: {collection.get('id')})")
        else:
            print(f"   ❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    # Test 3: List products
    print(f"\n🔍 Test 3: List Products")
    try:
        url = f"https://{shop_domain}/admin/api/{api_version}/products.json?limit=5"
        response = requests.get(url, headers=headers)
        print(f"   📡 URL: {url}")
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            products = response.json().get('products', [])
            print(f"   ✅ Found {len(products)} products (showing first 5)")
            for product in products:
                print(f"      - {product.get('title')} (ID: {product.get('id')})")
        else:
            print(f"   ❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    # Test 4: Test collection access (READY FOR PINTEREST)
    print(f"\n🔍 Test 4: Access READY FOR PINTEREST Collection")
    ready_collection_id = os.getenv("SHOPIFY_COLLECTION_ID", "644749033796")
    try:
        url = f"https://{shop_domain}/admin/api/{api_version}/collections/{ready_collection_id}.json"
        response = requests.get(url, headers=headers)
        print(f"   📡 URL: {url}")
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            collection = response.json().get('collection', {})
            print(f"   ✅ Collection: {collection.get('title')}")
            print(f"   ✅ Product Count: {collection.get('products_count', 0)}")
        else:
            print(f"   ❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    # Test 5: Test collects API (this is what we need for collection moves)
    print(f"\n🔍 Test 5: Test Collects API (Collection Management)")
    try:
        url = f"https://{shop_domain}/admin/api/{api_version}/collects.json?limit=5"
        response = requests.get(url, headers=headers)
        print(f"   📡 URL: {url}")
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            collects = response.json().get('collects', [])
            print(f"   ✅ Found {len(collects)} collect relationships")
            for collect in collects[:3]:  # Show first 3
                print(f"      - Product ID: {collect.get('product_id')} in Collection ID: {collect.get('collection_id')}")
        else:
            print(f"   ❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    print(f"\n🎉 All API tests passed! Shopify API is working correctly.")
    return True

if __name__ == "__main__":
    test_shopify_api()