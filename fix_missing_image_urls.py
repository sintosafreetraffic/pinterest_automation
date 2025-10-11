#!/usr/bin/env python3
"""
Quick script to fix missing image URLs in Google Sheet rows
This script will:
1. Find rows with empty image URLs but valid product URLs
2. Fetch the full product data from Shopify
3. Update the Google Sheet with the correct image URLs
"""

import os
import requests
import time
from dotenv import load_dotenv
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from bs4 import BeautifulSoup
import re

# Load environment variables
BASEDIR = Path(__file__).resolve().parent
DOTENV_PATH = BASEDIR / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, verbose=True, override=True)

# Get configuration
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_STORE_URL = "92c6ce-58.myshopify.com"
SHEET_ID = "1SutOYJ0UA-DDy1d4Xf86jf4wh8-ImNG5Tq0lcvMlqmE"

def setup_google_sheets():
    """Setup Google Sheets connection"""
    try:
        # Use service account credentials
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        workbook = client.open_by_key(SHEET_ID)
        sheet1 = workbook.worksheet('Sheet1')
        print("✅ Connected to Google Sheet successfully!")
        return sheet1
    except Exception as e:
        print(f"❌ Error connecting to Google Sheet: {e}")
        return None

def get_product_image_url(product_url, product_name="", pin_number=1):
    """Fetch product image URL from Shopify API with unique image selection and fallback strategies"""
    try:
        # Extract product handle from URL
        if 'myshopify.com/products/' not in product_url:
            return None
            
        product_handle = product_url.split('/products/')[-1]
        
        # Fetch product data from Shopify
        api_version = "2024-04"
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Strategy 1: Try to find by handle
        url = f"https://{SHOPIFY_STORE_URL}/admin/api/{api_version}/products.json"
        params = {"handle": product_handle}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        products = data.get('products', [])
        
        # Strategy 2: If not found by handle, try searching by title/name
        if not products and product_name:
            print(f"   🔍 Handle '{product_handle}' not found, searching by name...")
            search_params = {"title": product_name}
            response = requests.get(url, headers=headers, params=search_params)
            response.raise_for_status()
            
            data = response.json()
            products = data.get('products', [])
            
            if products:
                print(f"   ✅ Found product by name search")
        
        # Strategy 3: If still not found, try broader search
        if not products and product_name:
            print(f"   🔍 Trying broader search...")
            # Try searching with partial name
            name_parts = product_name.split('|')[0].strip().split()[:3]  # Get first 3 words
            for part in name_parts:
                if len(part) > 3:  # Only search with meaningful words
                    search_params = {"title": part}
                    response = requests.get(url, headers=headers, params=search_params)
                    response.raise_for_status()
                    
                    data = response.json()
                    products = data.get('products', [])
                    if products:
                        print(f"   ✅ Found product by partial name '{part}'")
                        break
        
        if products and len(products) > 0:
            product = products[0]
            if 'images' in product and product['images'] and len(product['images']) > 0:
                images = product['images']
                # Use modulo to cycle through images for different pins
                image_index = (pin_number - 1) % len(images)
                image_url = images[image_index].get('src', '')
                print(f"   🖼️ Found image {image_index + 1}/{len(images)}: {image_url[:50]}...")
                return image_url
            else:
                print(f"   ⚠️ No images found for product")
                return None
        else:
            print(f"   ⚠️ Product not found with any strategy")
            return None
            
    except Exception as e:
        print(f"   ❌ Error fetching product data: {e}")
        return None

def scrape_product_from_url(product_url):
    """Scrape product information directly from the Shopify product page"""
    try:
        print(f"   🌐 Scraping product page: {product_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract product title
        title_element = soup.find('h1', class_='product-title') or soup.find('h1', {'data-testid': 'product-title'}) or soup.find('h1')
        product_title = title_element.get_text().strip() if title_element else ""
        
        # Extract product images
        images = []
        
        # Look for product images in various formats
        img_selectors = [
            'img[data-src*="products"]',
            'img[src*="products"]', 
            '.product-image img',
            '.product-photos img',
            '[data-product-image] img',
            'img[alt*="' + product_title[:20] + '"]'
        ]
        
        for selector in img_selectors:
            img_elements = soup.select(selector)
            for img in img_elements:
                src = img.get('data-src') or img.get('src')
                if src and 'products' in src and src not in images:
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://' + SHOPIFY_STORE_URL + src
                    images.append(src)
        
        # Also look for JSON-LD structured data
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    if 'image' in data:
                        if isinstance(data['image'], list):
                            images.extend([img for img in data['image'] if isinstance(img, str)])
                        elif isinstance(data['image'], str):
                            images.append(data['image'])
            except:
                continue
        
        # Remove duplicates while preserving order
        unique_images = []
        for img in images:
            if img not in unique_images:
                unique_images.append(img)
        
        print(f"   📄 Found product title: {product_title[:50]}...")
        print(f"   🖼️ Found {len(unique_images)} images")
        
        return {
            'title': product_title,
            'images': unique_images,
            'handle': product_url.split('/products/')[-1] if '/products/' in product_url else None
        }
        
    except Exception as e:
        print(f"   ❌ Error scraping product page: {e}")
        return None

def fix_missing_image_urls():
    """Main function to fix missing image URLs"""
    print("🚀 Starting Image URL Fix Script")
    print("=" * 50)
    
    # Setup Google Sheets
    sheet1 = setup_google_sheets()
    if not sheet1:
        return False
    
    # Get all data
    print("📊 Loading data from Google Sheet...")
    data = sheet1.get_all_values()
    print(f"📊 Loaded {len(data)} rows")
    
    # Find rows with missing image URLs and group by product
    rows_to_fix = []
    product_pin_counts = {}  # Track pin numbers for each product
    
    for i, row in enumerate(data[1:], 2):  # Skip header
        if len(row) > 2:
            image_url = row[0] if len(row) > 0 else ''
            product_name = row[1] if len(row) > 1 else ''
            product_url = row[2] if len(row) > 2 else ''
            
            # Check if this row needs fixing
            if (not image_url or image_url.strip() == '') and product_url and 'myshopify.com' in product_url:
                # Count pins for this product to get unique image
                if product_url not in product_pin_counts:
                    product_pin_counts[product_url] = 0
                product_pin_counts[product_url] += 1
                pin_number = product_pin_counts[product_url]
                
                rows_to_fix.append((i, row, pin_number))
                print(f"📌 Row {i}: {product_name[:30]}... - Pin {pin_number} - {product_url}")
    
    print(f"\n🔍 Found {len(rows_to_fix)} rows with missing image URLs")
    
    if not rows_to_fix:
        print("✅ No rows need fixing!")
        return True
    
    # Fix each row
    fixed_count = 0
    failed_count = 0
    
    for row_num, row, pin_number in rows_to_fix:
        try:
            product_name = row[1] if len(row) > 1 else 'Unknown'
            product_url = row[2] if len(row) > 2 else ''
            
            print(f"\n🔧 Fixing row {row_num}: {product_name[:30]}... (Pin {pin_number})")
            
            # Get unique image URL based on pin number
            image_url = get_product_image_url(product_url, product_name, pin_number)
            
            # If API methods failed, try scraping the product page
            if not image_url:
                print(f"   🔄 API methods failed, trying web scraping...")
                scraped_data = scrape_product_from_url(product_url)
                
                if scraped_data and scraped_data['images']:
                    images = scraped_data['images']
                    # Use modulo to cycle through images for different pins
                    image_index = (pin_number - 1) % len(images)
                    image_url = images[image_index]
                    print(f"   🖼️ Found image {image_index + 1}/{len(images)} via scraping: {image_url[:50]}...")
            
            if image_url:
                # Update the row in Google Sheet
                sheet1.update_cell(row_num, 1, image_url)  # Column A (index 1 in gspread)
                print(f"   ✅ Updated with image URL")
                fixed_count += 1
            else:
                print(f"   ⚠️ Could not find image URL - skipping")
                failed_count += 1
            
            # Rate limiting
            time.sleep(0.5)  # Small delay to avoid rate limits
            
        except Exception as e:
            print(f"   ❌ Error fixing row {row_num}: {e}")
            failed_count += 1
            continue
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 Image URL Fix Summary:")
    print(f"   ✅ Fixed: {fixed_count} rows")
    print(f"   ❌ Failed: {failed_count} rows")
    print(f"   📊 Total processed: {fixed_count + failed_count}")
    
    return True

if __name__ == "__main__":
    print("🛠️  Image URL Fix Script")
    print("This script will fix missing image URLs in Google Sheet rows")
    print()
    
    # Check if we have the required API key
    if not SHOPIFY_API_KEY:
        print("❌ Error: SHOPIFY_API_KEY not found in .env file")
        exit(1)
    
    # Run the fix
    success = fix_missing_image_urls()
    
    if success:
        print("\n🎉 Image URL fix completed successfully!")
    else:
        print("\n❌ Image URL fix failed!")
