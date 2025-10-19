import os
import time
import requests
import datetime
import re
from utils import load_pins_from_sheet, plan_batch_updates, batch_write_to_sheet, get_sheet_cached, get_sheet_data
from pinterest_auth import get_ad_account_id, get_access_token
import random
from dotenv import load_dotenv
load_dotenv()  # This loads variables from .env into the environment

BASE_URL = "https://api.pinterest.com/v5"

SHOP_URL = os.getenv("SHOPIFY_STORE_URL")  # e.g., "https://myshop.myshopify.com"
ADMIN_API_KEY = os.getenv("SHOPIFY_API_KEY")
READY_COLLECTION_ID = os.getenv("SHOPIFY_COLLECTION_ID")
GENERATED_COLLECTION_ID = "651569889604"  # GENERATED collection ID
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2023-10")

# Extract domain from full URL for API calls
if SHOP_URL and SHOP_URL.startswith('https://'):
    SHOP_DOMAIN = SHOP_URL.replace('https://', '')
else:
    SHOP_DOMAIN = SHOP_URL

def extract_product_id_from_url(url):
    """Extract product ID from Shopify URL (both admin and product URLs)"""
    if not url:
        print(f"[DEBUG] extract_product_id_from_url: No URL provided")
        return None
    
    print(f"[DEBUG] extract_product_id_from_url: Processing URL: '{url}'")
    
    # Pattern 1: Admin URL - /admin/products/15264566083908
    admin_pattern = r'/admin/products/(\d+)'
    match = re.search(admin_pattern, url)
    if match:
        product_id = match.group(1)
        print(f"[DEBUG] extract_product_id_from_url: Found product ID from admin URL: '{product_id}'")
        return product_id
    
    # Pattern 2: Product URL - /products/product-handle (will be handled by main sheet lookup)
    product_pattern = r'/products/([^/?]+)'
    match = re.search(product_pattern, url)
    if match:
        product_handle = match.group(1)
        print(f"[DEBUG] extract_product_id_from_url: Found product handle: '{product_handle}'")
        print(f"[DEBUG] extract_product_id_from_url: Will get product ID from main sheet with collection info")
        return product_handle  # Return handle instead of None
    
    print(f"[DEBUG] extract_product_id_from_url: No product ID found in URL: '{url}'")
    return None

def load_second_sheet_data(sheet_id):
    """Load data from the second sheet (images/videos) and organize by product URL"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        print(f"[DEBUG] Loading second sheet with ID: {sheet_id}")
        
        # Load credentials
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the second sheet
        sheet = client.open_by_key(sheet_id).sheet1
        
        # Get raw data directly (ignore duplicate headers)
        print(f"[DEBUG] Getting raw data from second sheet...")
        raw_data = sheet.get_all_values()
        if not raw_data or len(raw_data) < 2:
            print(f"[DEBUG] No data found in second sheet")
            return {}
        
        print(f"[DEBUG] Found {len(raw_data)} rows in second sheet")
        
        # Process data using column positions:
        # Column E (index 4) = Product URL
        # Columns J-M (indices 9-12) = Images/Videos
        product_media = {}
        
        for i, row in enumerate(raw_data[1:], 1):  # Skip header row
            if len(row) > 12:  # Ensure we have enough columns
                product_url = row[4] if len(row) > 4 else ""  # Column E
                if product_url:
                    # Get images/videos from columns J-M (indices 9-12)
                    media_items = []
                    for col_idx in range(9, 13):  # Columns J, K, L, M
                        if col_idx < len(row) and row[col_idx]:
                            media_items.append(row[col_idx])
                    
                    if media_items:
                        product_media[product_url] = media_items
                        print(f"[DEBUG] Row {i}: Found {len(media_items)} media items for {product_url}")
        
        print(f"[DEBUG] Loaded media for {len(product_media)} products")
        return product_media
        
    except Exception as e:
        print(f"❌ Error loading second sheet: {e}")
        import traceback
        print(f"[DEBUG] Full error traceback: {traceback.format_exc()}")
        return {}

def load_second_sheet_data_with_facebook_scraping(sheet_id):
    """Load data from the second sheet (Facebook URLs) and scrape actual creatives"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import asyncio
        from final_facebook_scraper import FinalFacebookScraper
        
        print(f"[DEBUG] Loading second sheet with Facebook scraping: {sheet_id}")
        
        # Load credentials
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the second sheet
        sheet = client.open_by_key(sheet_id).sheet1
        
        # Get raw data directly (ignore duplicate headers)
        print(f"[DEBUG] Getting raw data from second sheet...")
        raw_data = sheet.get_all_values()
        if not raw_data or len(raw_data) < 2:
            print(f"[DEBUG] No data found in second sheet")
            return {}
        
        print(f"[DEBUG] Found {len(raw_data)} rows in second sheet")
        
        # Process data using column positions:
        # Column E (index 4) = Product URL
        # Columns J-M (indices 9-12) = Facebook URLs
        product_media = {}
        
        for i, row in enumerate(raw_data[1:], 1):  # Skip header row
            if len(row) > 12:  # Ensure we have enough columns
                product_url = row[4] if len(row) > 4 else ""  # Column E
                if product_url:
                    # Get Facebook URLs from columns J-M (indices 9-12)
                    facebook_urls = []
                    for col_idx in range(9, 13):  # Columns J, K, L, M
                        if col_idx < len(row) and row[col_idx]:
                            facebook_urls.append(row[col_idx])
                    
                    if facebook_urls:
                        print(f"[DEBUG] Row {i}: Found {len(facebook_urls)} Facebook URLs for {product_url}")
                        
                        # Scrape actual creatives from Facebook URLs
                        scraped_creatives = []
                        scraper = FinalFacebookScraper()
                        
                        for j, facebook_url in enumerate(facebook_urls):
                            print(f"[DEBUG] Scraping Facebook URL {j+1}/{len(facebook_urls)}: {facebook_url[:100]}...")
                            
                            try:
                                # Run the async scraper
                                result = asyncio.run(scraper.scrape_facebook_ad_creative(facebook_url))
                                
                                if result['success']:
                                    creative_data = {
                                        'media_url': result['media_url'],
                                        'media_type': result['media_type'],
                                        'facebook_url': facebook_url,
                                        'ad_id': result['ad_id']
                                    }
                                    scraped_creatives.append(creative_data)
                                    print(f"[DEBUG] ✅ Successfully scraped {result['media_type']}: {result['media_url'][:100]}...")
                                else:
                                    print(f"[DEBUG] ❌ Failed to scrape {facebook_url}: {result['error']}")
                                    
                            except Exception as e:
                                print(f"[DEBUG] ❌ Error scraping {facebook_url}: {e}")
                                continue
                        
                        if scraped_creatives:
                            product_media[product_url] = scraped_creatives
                            print(f"[DEBUG] Row {i}: Successfully scraped {len(scraped_creatives)} creatives for {product_url}")
                        else:
                            print(f"[DEBUG] Row {i}: No valid creatives found for {product_url}")
        
        print(f"[DEBUG] Loaded scraped creatives for {len(product_media)} products")
        return product_media
        
    except Exception as e:
        print(f"❌ Error loading second sheet with Facebook scraping: {e}")
        import traceback
        print(f"[DEBUG] Full error traceback: {traceback.format_exc()}")
        return {}

def upload_scraped_creatives_to_pinterest(access_token, scraped_creatives, board_id, product_name, existing_pin_data=None, target_language="de"):
    """Upload scraped creatives (from Facebook scraping) to Pinterest and create pins"""
    created_pins = []  # List of (pin_id, media_type) tuples
    
    try:
        print(f"   [DEBUG] Processing {len(scraped_creatives)} scraped creatives for {product_name}")
        
        for i, creative in enumerate(scraped_creatives):
            try:
                media_url = creative['media_url']
                media_type = creative['media_type']
                facebook_url = creative.get('facebook_url', '')
                ad_id = creative.get('ad_id', '')
                
                print(f"   [DEBUG] Processing creative {i+1}/{len(scraped_creatives)}:")
                print(f"   [DEBUG]   Media Type: {media_type}")
                print(f"   [DEBUG]   Media URL: {media_url[:100]}...")
                print(f"   [DEBUG]   Facebook URL: {facebook_url[:100]}...")
                print(f"   [DEBUG]   Ad ID: {ad_id}")
                
                # Generate proper marketing-focused titles and descriptions
                title = generate_pin_title(product_name, {}, existing_pin_data, target_language)
                description = generate_pin_description(product_name, {}, existing_pin_data, target_language)
                
                # Create pin for this creative
                result = upload_single_creative_to_pinterest(
                    access_token, 
                    media_url, 
                    media_type, 
                    board_id, 
                    title, 
                    description, 
                    existing_pin_data, 
                    product_name, 
                    len(created_pins) + 1
                )
                
                if result:
                    pin_id, pin_media_type = result
                    created_pins.append((pin_id, pin_media_type))
                    print(f"   ✅ Created {media_type} pin {len(created_pins)}: {pin_id}")
                else:
                    print(f"   ❌ Failed to create {media_type} pin from scraped creative")
                    
            except Exception as e:
                print(f"   [DEBUG] Error processing creative {i+1}: {e}")
                continue
        
        print(f"   📊 Total scraped creatives processed: {len(created_pins)}")
        return created_pins
        
    except Exception as e:
        print(f"   [DEBUG] Error uploading scraped creatives: {e}")
        return created_pins

def generate_slideshow_video_creative(product_images, music_folder_path, output_path, duration_per_image=1.0):
    """Generate a 10-second slideshow video with background music and text overlay"""
    try:
        import os
        import random
        import subprocess
        from PIL import Image, ImageDraw, ImageFont

        print(f"   [DEBUG] Generating slideshow video with {len(product_images)} images")

        # Select up to 10 images (1 second each = 10 seconds total)
        selected_images = product_images[:10]
        if len(selected_images) < 10:
            # Repeat images if we have fewer than 10
            while len(selected_images) < 10:
                selected_images.extend(product_images[:min(10-len(selected_images), len(product_images))])

        # Get random music file from music folder
        music_files = []
        if os.path.exists(music_folder_path):
            for file in os.listdir(music_folder_path):
                if file.lower().endswith(('.mp3', '.wav', '.m4a', '.aac')):
                    music_files.append(os.path.join(music_folder_path, file))

        if not music_files:
            print(f"   [DEBUG] No music files found in {music_folder_path}")
            return None

        selected_music = music_files[0]  # Use first music file
        print(f"   [DEBUG] Using background music: {os.path.basename(selected_music)}")

        # Create temporary directory for video frames
        temp_dir = 'creative_examples/test_generation/temp_video_frames'
        os.makedirs(temp_dir, exist_ok=True)

        # Process images with quality enhancements
        frame_size = (1080, 1080)  # Square format for Pinterest
        frame_paths = []

        for i, img_path in enumerate(selected_images):
            try:
                # Load and enhance image quality
                img = Image.open(img_path)
                img = img.resize(frame_size, Image.Resampling.LANCZOS)
                
                # Apply quality enhancements
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.2)  # Increase sharpness
                
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.1)  # Increase contrast slightly
                
                # Save as frame
                frame_path = f'{temp_dir}/frame_{i:03d}.jpg'
                img.save(frame_path, 'JPEG', quality=100, optimize=True)
                frame_paths.append(frame_path)
                print(f'   [DEBUG] Created enhanced frame {i+1}/{len(selected_images)}')
                
            except Exception as e:
                print(f'   [DEBUG] Error processing image {i+1}: {e}')
                continue

        print(f"   [DEBUG] Created {len(frame_paths)} enhanced video frames")

        # Create video using ffmpeg with text overlay
        print(f"   [DEBUG] Creating video with ffmpeg and text overlay...")

        try:
            # Create video from images (1 second per image)
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-framerate', '1',  # 1 frame per second
                '-i', f'{temp_dir}/frame_%03d.jpg',  # Input pattern
                '-i', selected_music,  # Audio input
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                '-shortest',  # End when shortest input ends
                '-r', '24',  # Output frame rate
                '-vf', 'drawtext=fontfile=/System/Library/Fonts/Arial.ttf:text="Jetzt kaufen – 50% Rabatt für kurze Zeit":fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.8:boxborderw=10:enable=\'between(t,7,10)\'',
                output_path
            ]
            
            print(f"   [DEBUG] Running ffmpeg with text overlay...")
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ Generated slideshow video with text overlay: {output_path}")
            else:
                print(f"   [DEBUG] FFmpeg error: {result.stderr}")
                # Fallback without text overlay
                print(f"   [DEBUG] Creating fallback video without text overlay...")
                ffmpeg_cmd_fallback = [
                    'ffmpeg',
                    '-y',
                    '-framerate', '1',
                    '-i', f'{temp_dir}/frame_%03d.jpg',
                    '-i', selected_music,
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-pix_fmt', 'yuv420p',
                    '-shortest',
                    '-r', '24',
                    output_path
                ]
                result = subprocess.run(ffmpeg_cmd_fallback, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   ✅ Generated slideshow video (fallback): {output_path}")
                else:
                    print(f"   ❌ Failed to create video: {result.stderr}")
                    return None
                    
        except Exception as e:
            print(f"   [DEBUG] Error creating video: {e}")
            return None

        # Clean up temporary frames
        print(f"   [DEBUG] Cleaning up temporary files...")
        for frame_path in frame_paths:
            try:
                os.remove(frame_path)
            except:
                pass

        try:
            os.rmdir(temp_dir)
        except:
            pass

        print(f"   ✅ Generated enhanced slideshow video: {output_path}")
        return output_path

    except Exception as e:
        print(f"   [DEBUG] Error generating slideshow video: {e}")
        return None

def generate_quad_image_creative(product_images, output_path):
    """Generate a 4-quadrant image creative"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        
        print(f"   [DEBUG] Generating 4-quadrant image with {len(product_images)} images")
        
        # Select 4 images
        selected_images = product_images[:4]
        if len(selected_images) < 4:
            # Repeat images if we have fewer than 4
            while len(selected_images) < 4:
                selected_images.extend(product_images[:min(4-len(selected_images), len(product_images))])
        
        # Create a square canvas (1080x1080 for Pinterest)
        canvas_size = 1080
        canvas = Image.new('RGB', (canvas_size, canvas_size), 'white')
        
        # Calculate quadrant size
        quadrant_size = canvas_size // 2
        
        # Place images in quadrants
        for i, image_path in enumerate(selected_images[:4]):
            try:
                # Load and resize image
                img = Image.open(image_path)
                img = img.resize((quadrant_size, quadrant_size), Image.Resampling.LANCZOS)
                
                # Calculate position
                x = (i % 2) * quadrant_size
                y = (i // 2) * quadrant_size
                
                # Paste image onto canvas
                canvas.paste(img, (x, y))
                
            except Exception as e:
                print(f"   [DEBUG] Error processing image {i+1}: {e}")
                continue
        
        # Add subtle border between quadrants
        draw = ImageDraw.Draw(canvas)
        # Vertical line
        draw.line([(quadrant_size, 0), (quadrant_size, canvas_size)], fill='lightgray', width=2)
        # Horizontal line
        draw.line([(0, quadrant_size), (canvas_size, quadrant_size)], fill='lightgray', width=2)
        
        # Save the image
        canvas.save(output_path, 'JPEG', quality=95)
        
        print(f"   ✅ Generated 4-quadrant image: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"   [DEBUG] Error generating 4-quadrant image: {e}")
        return None

def generate_enhanced_showcase_creative(product_images, output_path):
    """Generate an enhanced product showcase with full-page coverage and high quality"""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
        import os

        print(f"   [DEBUG] Generating enhanced showcase creative with {len(product_images)} images")

        if len(product_images) < 1:
            print(f"   [DEBUG] Need at least 1 image for showcase")
            return None

        # Create a high-quality canvas (1080x1080 for Pinterest)
        canvas_size = 1080
        canvas = Image.new('RGB', (canvas_size, canvas_size), 'black')  # Black background for better contrast

        # Select up to 4 images for showcase
        selected_images = product_images[:4]
        if len(selected_images) < 4:
            # Repeat images if we have fewer than 4
            while len(selected_images) < 4:
                selected_images.extend(product_images[:min(4-len(selected_images), len(product_images))])

        # Calculate grid layout (2x2)
        quadrant_size = canvas_size // 2
        positions = [(0, 0), (quadrant_size, 0), (0, quadrant_size), (quadrant_size, quadrant_size)]

        for i, (x, y) in enumerate(positions):
            if i < len(selected_images):
                try:
                    # Load and enhance image quality
                    img = Image.open(selected_images[i])
                    
                    # Enhance image quality
                    img = img.resize((quadrant_size, quadrant_size), Image.Resampling.LANCZOS)
                    
                    # Apply quality enhancements
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.2)  # Increase sharpness
                    
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.1)  # Increase contrast slightly
                    
                    # Paste image onto canvas with no gaps
                    canvas.paste(img, (x, y))
                    
                except Exception as e:
                    print(f"   [DEBUG] Error processing image {i+1}: {e}")
                    continue

        # Add subtle border between quadrants (optional)
        draw = ImageDraw.Draw(canvas)
        draw.line([(quadrant_size, 0), (quadrant_size, canvas_size)], fill='white', width=2)
        draw.line([(0, quadrant_size), (canvas_size, quadrant_size)], fill='white', width=2)

        # Save with maximum quality
        canvas.save(output_path, 'JPEG', quality=100, optimize=True)

        print(f"   ✅ Generated enhanced showcase creative: {output_path}")
        return output_path

    except Exception as e:
        print(f"   [DEBUG] Error generating enhanced showcase creative: {e}")
        return None

def generate_carousel_style_creative(product_images, output_path):
    """Generate a carousel-style creative showing multiple products"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        
        print(f"   [DEBUG] Generating carousel-style creative with {len(product_images)} images")
        
        # Select up to 6 images for carousel
        selected_images = product_images[:6]
        
        # Create canvas (1080x1920 for Pinterest story format)
        canvas_width = 1080
        canvas_height = 1920
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        
        # Calculate image positions (3x2 grid)
        img_width = 300
        img_height = 300
        margin = 50
        
        for i, image_path in enumerate(selected_images):
            try:
                # Load and resize image
                img = Image.open(image_path)
                img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
                
                # Calculate position
                x = margin + (i % 3) * (img_width + margin)
                y = margin + (i // 3) * (img_height + margin)
                
                # Paste image onto canvas
                canvas.paste(img, (x, y))
                
            except Exception as e:
                print(f"   [DEBUG] Error processing image {i+1}: {e}")
                continue
        
        # Add title at the top
        draw = ImageDraw.Draw(canvas)
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            subtitle_font = ImageFont.truetype("arial.ttf", 40)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        draw.text((canvas_width//2 - 200, 50), "SHOP THE LOOK", fill='black', font=title_font)
        draw.text((canvas_width//2 - 150, 120), "Multiple Styles Available", fill='gray', font=subtitle_font)
        
        # Save the image
        canvas.save(output_path, 'JPEG', quality=95)
        
        print(f"   ✅ Generated carousel-style creative: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"   [DEBUG] Error generating carousel-style creative: {e}")
        return None

def generate_all_creative_variations(product_images, product_name, output_dir, music_folder_path):
    """Generate all creative variations for a product"""
    try:
        import os

        print(f"   [DEBUG] Generating all creative variations for {product_name}")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        generated_creatives = []

        # 1. Slideshow video with music and text overlay
        if len(product_images) >= 2:
            slideshow_path = os.path.join(output_dir, f"{product_name}_slideshow.mp4")
            slideshow_result = generate_slideshow_video_creative(product_images, music_folder_path, slideshow_path)
            if slideshow_result:
                generated_creatives.append({
                    'type': 'slideshow_video',
                    'path': slideshow_result,
                    'media_type': 'video'
                })

        # 2. Enhanced 4-quadrant image with quality improvements
        if len(product_images) >= 2:
            quad_path = os.path.join(output_dir, f"{product_name}_quad.jpg")
            quad_result = generate_quad_image_creative(product_images, quad_path)
            if quad_result:
                generated_creatives.append({
                    'type': 'quad_image',
                    'path': quad_result,
                    'media_type': 'image'
                })

        # 3. Enhanced showcase creative (replaces before/after)
        if len(product_images) >= 1:
            showcase_path = os.path.join(output_dir, f"{product_name}_showcase.jpg")
            showcase_result = generate_enhanced_showcase_creative(product_images, showcase_path)
            if showcase_result:
                generated_creatives.append({
                    'type': 'enhanced_showcase',
                    'path': showcase_result,
                    'media_type': 'image'
                })

        # 4. Carousel-style creative
        if len(product_images) >= 2:
            carousel_path = os.path.join(output_dir, f"{product_name}_carousel.jpg")
            carousel_result = generate_carousel_style_creative(product_images, carousel_path)
            if carousel_result:
                generated_creatives.append({
                    'type': 'carousel',
                    'path': carousel_result,
                    'media_type': 'image'
                })

        print(f"   ✅ Generated {len(generated_creatives)} creative variations")
        return generated_creatives

    except Exception as e:
        print(f"   [DEBUG] Error generating creative variations: {e}")
        return []

def get_product_id_by_handle_and_collection(product_handle, collection_id):
    """Get product ID from Shopify using product handle and collection ID"""
    try:
        print(f"[DEBUG] Getting product ID by handle: '{product_handle}' in collection: '{collection_id}'")
        
        # First try to get from the specific collection
        if collection_id:
            url = f"https://{SHOP_DOMAIN}/admin/api/{SHOPIFY_API_VERSION}/collections/{collection_id}/products.json"
            headers = {"X-Shopify-Access-Token": ADMIN_API_KEY}
            params = {"handle": product_handle}
            
            print(f"[DEBUG] Searching in collection: {url}")
            response = requests.get(url, headers=headers, params=params)
            print(f"[DEBUG] Collection lookup response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                if products:
                    product_id = str(products[0].get('id', ''))
                    print(f"[DEBUG] Found product ID by handle in collection: {product_id}")
                    return product_id
                else:
                    print(f"[DEBUG] No products found with handle '{product_handle}' in collection {collection_id}")
            else:
                print(f"[DEBUG] Collection API error: {response.status_code} - {response.text}")
        
        # Fallback: search all products
        print(f"[DEBUG] Falling back to search all products")
        url = f"https://{SHOP_DOMAIN}/admin/api/{SHOPIFY_API_VERSION}/products.json"
        headers = {"X-Shopify-Access-Token": ADMIN_API_KEY}
        params = {"handle": product_handle}
        
        response = requests.get(url, headers=headers, params=params)
        print(f"[DEBUG] All products lookup response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            if products:
                product_id = str(products[0].get('id', ''))
                print(f"[DEBUG] Found product ID by handle in all products: {product_id}")
                return product_id
        
        print(f"[DEBUG] No product found with handle: '{product_handle}'")
        return None
        
    except Exception as e:
        print(f"❌ Error getting product ID by handle: {e}")
        return None

def get_product_id_from_shopify(product_name):
    """Get product ID directly from Shopify using product name"""
    try:
        print(f"[DEBUG] Getting product ID from Shopify for: '{product_name}'")
        print(f"[DEBUG] SHOP_URL: {SHOP_URL}")
        print(f"[DEBUG] SHOP_DOMAIN: {SHOP_DOMAIN}")
        print(f"[DEBUG] ADMIN_API_KEY: {'SET' if ADMIN_API_KEY else 'NOT SET'}")
        print(f"[DEBUG] READY_COLLECTION_ID: {READY_COLLECTION_ID}")
        print(f"[DEBUG] SHOPIFY_API_VERSION: {SHOPIFY_API_VERSION}")
        
        # Search in the READY FOR PINTEREST collection first
        if READY_COLLECTION_ID:
            print(f"[DEBUG] Searching in READY FOR PINTEREST collection: {READY_COLLECTION_ID}")
            url = f"https://{SHOP_DOMAIN}/admin/api/{SHOPIFY_API_VERSION}/collections/{READY_COLLECTION_ID}/products.json"
        else:
            print(f"[DEBUG] No collection ID, searching all products")
            url = f"https://{SHOP_DOMAIN}/admin/api/{SHOPIFY_API_VERSION}/products.json"
        
        print(f"[DEBUG] Shopify API URL: {url}")
        
        headers = {"X-Shopify-Access-Token": ADMIN_API_KEY}
        params = {"title": product_name}
        
        print(f"[DEBUG] Making request to Shopify API...")
        response = requests.get(url, headers=headers, params=params)
        print(f"[DEBUG] Shopify API response status: {response.status_code}")
        print(f"[DEBUG] Shopify API response text: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            print(f"[DEBUG] Found {len(products)} products matching '{product_name}'")
            
            for product in products:
                shopify_title = product.get('title', '').strip()
                product_id = str(product.get('id', ''))
                print(f"[DEBUG] Shopify product: '{shopify_title}' (ID: {product_id})")
                
                # Check for exact match or partial match
                if (shopify_title.lower() == product_name.lower() or 
                    product_name.lower() in shopify_title.lower() or
                    shopify_title.lower() in product_name.lower()):
                    print(f"[DEBUG] Found matching product in Shopify: '{shopify_title}' (ID: {product_id})")
                    return product_id
            
            print(f"[DEBUG] No exact match found in Shopify for '{product_name}'")
            
            # Try a broader search without title filter
            print(f"[DEBUG] Trying broader search without title filter...")
            url_broad = f"https://{SHOP_DOMAIN}/admin/api/{SHOPIFY_API_VERSION}/products.json"
            response_broad = requests.get(url_broad, headers=headers)
            print(f"[DEBUG] Broad search response status: {response_broad.status_code}")
            
            if response_broad.status_code == 200:
                data_broad = response_broad.json()
                products_broad = data_broad.get('products', [])
                print(f"[DEBUG] Found {len(products_broad)} total products in store")
                
                for product in products_broad:
                    shopify_title = product.get('title', '').strip()
                    product_id = str(product.get('id', ''))
                    
                    # Check for partial match
                    if (product_name.lower() in shopify_title.lower() or
                        shopify_title.lower() in product_name.lower()):
                        print(f"[DEBUG] Found partial match in Shopify: '{shopify_title}' (ID: {product_id})")
                        return product_id
        else:
            print(f"[DEBUG] Shopify API error: {response.status_code} - {response.text}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting product ID from Shopify: {e}")
        import traceback
        print(f"[DEBUG] Full error traceback: {traceback.format_exc()}")
        return None

def get_product_id_from_main_sheet(product_name):
    """Get product ID from main sheet data by product name"""
    try:
        print(f"[DEBUG] Getting product ID for: '{product_name}'")
        
        sheet = get_sheet_cached()
        headers, data_rows = get_sheet_data(sheet)
        
        print(f"[DEBUG] Main sheet headers: {headers}")
        print(f"[DEBUG] Main sheet has {len(data_rows)} data rows")
        
        # Find the product name column first
        name_col_idx = None
        for i, header in enumerate(headers):
            if 'product name' in header.lower():
                name_col_idx = i
                break
        
        # Show all product names in main sheet for debugging
        if data_rows and name_col_idx is not None:
            print(f"[DEBUG] Product names in main sheet (column {name_col_idx}):")
            for i, row in enumerate(data_rows):
                if len(row) > name_col_idx:
                    print(f"  Row {i+1}: '{row[name_col_idx] if row[name_col_idx] else 'EMPTY'}'")
        
        # Find the product URL column and collection column
        url_col_idx = None
        collection_col_idx = None
        for i, header in enumerate(headers):
            if 'product url' in header.lower():
                url_col_idx = i
                print(f"[DEBUG] Found product URL column at index {i}: '{header}'")
            elif 'collection' in header.lower() and 'id' in header.lower():
                collection_col_idx = i
                print(f"[DEBUG] Found collection column at index {i}: '{header}'")
        
        if name_col_idx is None or url_col_idx is None:
            print(f"⚠️ Could not find product name or URL columns in main sheet")
            print(f"[DEBUG] name_col_idx: {name_col_idx}, url_col_idx: {url_col_idx}")
            return None
        
        # Search for the product
        for i, row in enumerate(data_rows):
            if len(row) > max(name_col_idx, url_col_idx):
                row_product_name = row[name_col_idx].strip().lower()
                print(f"[DEBUG] Row {i+1}: Comparing '{row_product_name}' with '{product_name.lower()}'")
                
                if row_product_name == product_name.lower():
                    product_url = row[url_col_idx]
                    collection_id = row[collection_col_idx] if collection_col_idx is not None and len(row) > collection_col_idx else None
                    
                    print(f"[DEBUG] Found matching product! URL: '{product_url}', Collection ID: '{collection_id}'")
                    
                    # Extract handle from URL
                    handle_or_id = extract_product_id_from_url(product_url)
                    print(f"[DEBUG] Extracted handle/ID: '{handle_or_id}'")
                    
                    if handle_or_id:
                        # If it's a handle (not a numeric ID), get the product ID from Shopify
                        if not handle_or_id.isdigit():
                            product_id = get_product_id_by_handle_and_collection(handle_or_id, collection_id)
                            print(f"[DEBUG] Got product ID from Shopify: '{product_id}'")
                            return product_id
                        else:
                            # It's already a product ID
                            print(f"[DEBUG] Already have product ID: '{handle_or_id}'")
                            return handle_or_id
                    
                    return None
                else:
                    # Also check for partial matches
                    if product_name.lower() in row_product_name or row_product_name in product_name.lower():
                        print(f"[DEBUG] Row {i+1}: Partial match found! '{row_product_name}' contains '{product_name.lower()}' or vice versa")
                        product_url = row[url_col_idx]
                        collection_id = row[collection_col_idx] if collection_col_idx is not None and len(row) > collection_col_idx else None
                        
                        print(f"[DEBUG] Using partial match! URL: '{product_url}', Collection ID: '{collection_id}'")
                        
                        # Extract handle from URL
                        handle_or_id = extract_product_id_from_url(product_url)
                        print(f"[DEBUG] Extracted handle/ID: '{handle_or_id}'")
                        
                        if handle_or_id:
                            # If it's a handle (not a numeric ID), get the product ID from Shopify
                            if not handle_or_id.isdigit():
                                product_id = get_product_id_by_handle_and_collection(handle_or_id, collection_id)
                                print(f"[DEBUG] Got product ID from Shopify: '{product_id}'")
                                return product_id
                            else:
                                # It's already a product ID
                                print(f"[DEBUG] Already have product ID: '{handle_or_id}'")
                                return handle_or_id
                        
                        return None
        
        print(f"⚠️ Product '{product_name}' not found in main sheet")
        return None
        
    except Exception as e:
        print(f"❌ Error getting product ID from main sheet: {e}")
        import traceback
        print(f"[DEBUG] Full error traceback: {traceback.format_exc()}")
        return None

def get_board_id_by_title(access_token, board_title):
    """Get board ID from Pinterest using exact board title match with pagination"""
    try:
        import requests
        
        all_boards = []
        page_size = 25
        bookmark = None
        
        print(f"[DEBUG] Fetching ALL boards from Pinterest (with pagination)...")
        
        # Fetch all boards with pagination
        while True:
            # Get user's boards with pagination
            url = "https://api.pinterest.com/v5/boards"
            params = {
                "page_size": page_size
            }
            if bookmark:
                params["bookmark"] = bookmark
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                boards_data = response.json()
                boards = boards_data.get('items', [])
                all_boards.extend(boards)
                
                print(f"[DEBUG] Fetched {len(boards)} boards (total so far: {len(all_boards)})")
                
                # Check if there are more pages
                bookmark = boards_data.get('bookmark')
                if not bookmark:
                    break
            else:
                print(f"[DEBUG] Error fetching boards: {response.status_code} - {response.text}")
                break
        
        print(f"[DEBUG] Total boards fetched: {len(all_boards)}")
        print(f"[DEBUG] Searching for exact match of board title: '{board_title}'")
        
        # Show first 10 and last 10 board names for debugging
        board_names = [board.get('name', '') for board in all_boards]
        if len(board_names) > 20:
            print(f"[DEBUG] First 10 boards: {board_names[:10]}")
            print(f"[DEBUG] Last 10 boards: {board_names[-10:]}")
        else:
            print(f"[DEBUG] All boards: {board_names}")
        
        # Search for board with exact matching title
        for board in all_boards:
            board_name = board.get('name', '').strip()
            board_title_clean = board_title.strip()
            
            if board_name == board_title_clean:
                board_id = board.get('id', '')
                print(f"[DEBUG] Found exact match for board '{board_title}' with ID: {board_id}")
                return board_id
            
            # Also try case-insensitive comparison
            if board_name.lower() == board_title_clean.lower():
                board_id = board.get('id', '')
                print(f"[DEBUG] Found case-insensitive match for board '{board_title}' with ID: {board_id}")
                return board_id
        
        print(f"[DEBUG] No exact match found for board '{board_title}' in {len(all_boards)} boards")
        return None
            
    except Exception as e:
        print(f"[DEBUG] Error getting board ID by title: {e}")
        return None

def find_board_by_partial_name(access_token, board_title):
    """Find board ID using partial name matching as fallback with pagination"""
    try:
        import requests
        
        all_boards = []
        page_size = 25
        bookmark = None
        
        print(f"[DEBUG] Fetching ALL boards for partial matching (with pagination)...")
        
        # Fetch all boards with pagination
        while True:
            url = "https://api.pinterest.com/v5/boards"
            params = {
                "page_size": page_size
            }
            if bookmark:
                params["bookmark"] = bookmark
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                boards_data = response.json()
                boards = boards_data.get('items', [])
                all_boards.extend(boards)
                
                # Check if there are more pages
                bookmark = boards_data.get('bookmark')
                if not bookmark:
                    break
            else:
                print(f"[DEBUG] Error fetching boards for partial match: {response.status_code} - {response.text}")
                break
        
        print(f"[DEBUG] Total boards for partial matching: {len(all_boards)}")
        print(f"[DEBUG] Searching for partial match of board title: '{board_title}'")
        
        # Try different partial matching strategies
        search_terms = [
            board_title.strip(),
            board_title.strip().lower(),
            board_title.strip().upper(),
            # Extract key words from the title
            ' '.join([word for word in board_title.split() if len(word) > 3])
        ]
        
        for search_term in search_terms:
            if not search_term:
                continue
                
            print(f"[DEBUG] Trying search term: '{search_term}'")
            
            for board in all_boards:
                board_name = board.get('name', '').strip()
                board_name_lower = board_name.lower()
                search_term_lower = search_term.lower()
                
                # Check if search term is contained in board name
                if search_term_lower in board_name_lower:
                    board_id = board.get('id', '')
                    print(f"[DEBUG] Found partial match: '{search_term}' in board '{board_name}' with ID: {board_id}")
                    return board_id
                
                # Check if board name is contained in search term
                if board_name_lower in search_term_lower:
                    board_id = board.get('id', '')
                    print(f"[DEBUG] Found reverse partial match: board '{board_name}' in '{search_term}' with ID: {board_id}")
                    return board_id
        
        print(f"[DEBUG] No partial match found for board '{board_title}' in {len(all_boards)} boards")
        return None
            
    except Exception as e:
        print(f"[DEBUG] Error finding board by partial name: {e}")
        return None

def detect_language(text):
    """Detect if text is German or English based on common words"""
    if not text:
        return 'en'  # Default to English
    
    text_lower = text.lower()
    
    # German indicators
    german_words = ['und', 'mit', 'für', 'von', 'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'eines', 'ist', 'sind', 'haben', 'hat', 'werden', 'wird', 'können', 'kann', 'müssen', 'muss', 'sollen', 'soll', 'dürfen', 'darf', 'wollen', 'will', 'mögen', 'mag', 'gehen', 'geht', 'kommen', 'kommt', 'sehen', 'sieht', 'hören', 'hört', 'sprechen', 'spricht', 'denken', 'denkt', 'wissen', 'weiß', 'glauben', 'glaubt', 'finden', 'findet', 'machen', 'macht', 'nehmen', 'nimmt', 'geben', 'gibt', 'sagen', 'sagt', 'fragen', 'fragt', 'antworten', 'antwortet', 'helfen', 'hilft', 'arbeiten', 'arbeitet', 'leben', 'lebt', 'lieben', 'liebt', 'träumen', 'träumt', 'lachen', 'lacht', 'weinen', 'weint', 'schreiben', 'schreibt', 'lesen', 'liest', 'lernen', 'lernt', 'lehren', 'lehrt', 'spielen', 'spielt', 'tanzen', 'tanzt', 'singen', 'singt', 'malen', 'malt', 'zeichnen', 'zeichnet', 'bauen', 'baut', 'reparieren', 'repariert', 'kochen', 'kocht', 'backen', 'backt', 'putzen', 'putzt', 'waschen', 'wäscht', 'kaufen', 'kauft', 'verkaufen', 'verkauft', 'bezahlen', 'bezahlt', 'sparen', 'spart', 'ausgeben', 'gibt aus', 'verdienen', 'verdient', 'verlieren', 'verliert', 'gewinnen', 'gewinnt', 'versuchen', 'versucht', 'schaffen', 'schafft', 'gelingen', 'gelingt', 'misslingen', 'misslingt', 'erfolgreich', 'erfolglos', 'glücklich', 'unglücklich', 'zufrieden', 'unzufrieden', 'stolz', 'traurig', 'fröhlich', 'nervös', 'ruhig', 'aufgeregt', 'entspannt', 'müde', 'wach', 'hungrig', 'satt', 'durstig', 'krank', 'gesund', 'stark', 'schwach', 'groß', 'klein', 'lang', 'kurz', 'breit', 'schmal', 'dick', 'dünn', 'schwer', 'leicht', 'schnell', 'langsam', 'alt', 'jung', 'neu', 'alt', 'schön', 'hässlich', 'gut', 'schlecht', 'richtig', 'falsch', 'wahr', 'falsch', 'möglich', 'unmöglich', 'wichtig', 'unwichtig', 'interessant', 'langweilig', 'einfach', 'schwer', 'teuer', 'billig', 'reich', 'arm', 'frei', 'gefangen', 'sicher', 'gefährlich', 'ruhig', 'laut', 'hell', 'dunkel', 'warm', 'kalt', 'heiß', 'kühl', 'trocken', 'nass', 'sauber', 'schmutzig', 'voll', 'leer', 'offen', 'geschlossen', 'neu', 'alt', 'modern', 'altmodisch', 'populär', 'unpopulär', 'bekannt', 'unbekannt', 'berühmt', 'unbekannt', 'erfolgreich', 'erfolglos', 'glücklich', 'unglücklich', 'zufrieden', 'unzufrieden', 'stolz', 'traurig', 'fröhlich', 'nervös', 'ruhig', 'aufgeregt', 'entspannt', 'müde', 'wach', 'hungrig', 'satt', 'durstig', 'krank', 'gesund', 'stark', 'schwach', 'groß', 'klein', 'lang', 'kurz', 'breit', 'schmal', 'dick', 'dünn', 'schwer', 'leicht', 'schnell', 'langsam', 'alt', 'jung', 'neu', 'alt', 'schön', 'hässlich', 'gut', 'schlecht', 'richtig', 'falsch', 'wahr', 'falsch', 'möglich', 'unmöglich', 'wichtig', 'unwichtig', 'interessant', 'langweilig', 'einfach', 'schwer', 'teuer', 'billig', 'reich', 'arm', 'frei', 'gefangen', 'sicher', 'gefährlich', 'ruhig', 'laut', 'hell', 'dunkel', 'warm', 'kalt', 'heiß', 'kühl', 'trocken', 'nass', 'sauber', 'schmutzig', 'voll', 'leer', 'offen', 'geschlossen', 'neu', 'alt', 'modern', 'altmodisch', 'populär', 'unpopulär', 'bekannt', 'unbekannt', 'berühmt', 'unbekannt']
    
    # Count German words
    german_count = sum(1 for word in german_words if word in text_lower)
    
    # If we find German words, it's likely German
    if german_count > 0:
        return 'de'
    
    return 'en'  # Default to English

def generate_pin_title(product_name, creative_data, existing_pin_data=None, target_language="de"):
    """Generate an engaging pin title based on product name and creative data in the specified target language"""
    try:
        # Use the manually selected target language
        language = target_language
        
        print(f"   [DEBUG] Using target language: {language}")
        
        # Clean product name
        clean_name = product_name.replace('|', '').strip()
        
        if language == 'de':  # German
            # Extract key product features from the name
            if 'jacke' in clean_name.lower() or 'jacket' in clean_name.lower():
                if 'winter' in clean_name.lower() or 'gefuttert' in clean_name.lower():
                    return f"🔥 Warme Winterjacke - Stilvoll & Gemütlich"
                else:
                    return f"✨ Elegante Jacke - Perfekt für jede Saison"
            elif 'kleid' in clean_name.lower() or 'dress' in clean_name.lower():
                return f"💫 Wunderschönes Kleid - Mühelos Elegant"
            elif 'hose' in clean_name.lower() or 'pants' in clean_name.lower():
                return f"👖 Premium Hose - Komfort trifft Stil"
            elif 'schuhe' in clean_name.lower() or 'shoes' in clean_name.lower():
                return f"👟 Stilvolle Schuhe - Steigern Sie Ihr Spiel"
            elif 'tasche' in clean_name.lower() or 'bag' in clean_name.lower():
                return f"👜 Designer Tasche - Tragen Sie mit Stil"
            else:
                return f"✨ {clean_name} - Premium Qualität"
        else:  # English
            # Extract key product features from the name
            if 'jacke' in clean_name.lower() or 'jacket' in clean_name.lower():
                if 'winter' in clean_name.lower() or 'gefuttert' in clean_name.lower():
                    return f"🔥 Cozy Winter Jacket - Stay Warm & Stylish"
                else:
                    return f"✨ Elegant Jacket - Perfect for Every Season"
            elif 'kleid' in clean_name.lower() or 'dress' in clean_name.lower():
                return f"💫 Stunning Dress - Effortlessly Elegant"
            elif 'hose' in clean_name.lower() or 'pants' in clean_name.lower():
                return f"👖 Premium Pants - Comfort Meets Style"
            elif 'schuhe' in clean_name.lower() or 'shoes' in clean_name.lower():
                return f"👟 Stylish Shoes - Step Up Your Game"
            elif 'tasche' in clean_name.lower() or 'bag' in clean_name.lower():
                return f"👜 Designer Bag - Carry in Style"
            else:
                return f"✨ {clean_name} - Premium Quality"
            
    except Exception as e:
        print(f"   [DEBUG] Error generating pin title: {e}")
        return f"✨ {product_name} - Premium Quality"

def generate_pin_description(product_name, creative_data, existing_pin_data=None, target_language="de"):
    """Generate an engaging pin description based on product name and creative data in the specified target language"""
    try:
        # Use the manually selected target language
        language = target_language
        
        # Clean product name
        clean_name = product_name.replace('|', '').strip()
        
        if language == 'de':  # German
            # Choose description based on product type
            if 'jacke' in clean_name.lower() or 'jacket' in clean_name.lower():
                if 'winter' in clean_name.lower() or 'gefuttert' in clean_name.lower():
                    return f"Bleiben Sie warm und stilvoll diesen Winter mit {clean_name}. Premium-Isolierung trifft auf modernes Design. Perfekt für kalte Wetterabenteuer! ❄️✨"
                else:
                    return f"Schichten Sie stilvoll mit {clean_name}. Vielseitiges Design, das für jede Saison funktioniert. Von lässig bis schick - diese Jacke hat Sie abgedeckt! 🌟"
            elif 'kleid' in clean_name.lower() or 'dress' in clean_name.lower():
                return f"Lassen Sie überall Köpfe drehen mit {clean_name}. Schmeichelnde Silhouette und Premium-Stoff schaffen den perfekten Look für jeden Anlass. Eleganz neu definiert! 💃✨"
            elif 'hose' in clean_name.lower() or 'pants' in clean_name.lower():
                return f"Komfort trifft auf Stil mit {clean_name}. Perfekte Passform und Premium-Materialien machen diese Hose zu einem Kleiderschrank-Essential. Ziehen Sie sich stilvoll oder lässig an! 👖💫"
            elif 'schuhe' in clean_name.lower() or 'shoes' in clean_name.lower():
                return f"Treten Sie stilvoll auf mit {clean_name}. Überlegener Komfort und auffälliges Design machen diese Schuhe perfekt für jedes Abenteuer. Gehen Sie mit Selbstvertrauen! 👟🔥"
            elif 'tasche' in clean_name.lower() or 'bag' in clean_name.lower():
                return f"Tragen Sie Ihre Essentials mit Stil mit {clean_name}. Großzügiges Design trifft auf sophisticated Ästhetik. Das perfekte Accessoire für den modernen Lifestyle! 👜✨"
            else:
                # German generic descriptions
                german_descriptions = [
                    f"Entdecken Sie die perfekte Mischung aus Stil und Komfort mit {clean_name}. Hergestellt aus Premium-Materialien und mit Liebe zum Detail. Jetzt shoppen und Ihre Garderobe aufwerten! ✨",
                    f"Verwandeln Sie Ihr Aussehen mit {clean_name}. Dieses atemberaubende Stück kombiniert modernes Design mit zeitloser Eleganz. Perfekt für jeden Anlass! 💫",
                    f"Fügen Sie Ihren Sammlung eine Prise Raffinesse hinzu mit {clean_name}. Premium-Qualität trifft auf zeitgemäßen Stil. Verpassen Sie es nicht! 🔥",
                    f"Erleben Sie Luxus und Komfort mit {clean_name}. Sorgfältig für den modernen Lifestyle gefertigt. Shoppen Sie die neuesten Trends! 👑",
                    f"Machen Sie eine Aussage mit {clean_name}. Außergewöhnliche Qualität und atemberaubendes Design in einem perfekten Stück. Bestellen Sie noch heute! ⭐"
                ]
                import random
                return random.choice(german_descriptions)
        else:  # English
            # Choose description based on product type
            if 'jacke' in clean_name.lower() or 'jacket' in clean_name.lower():
                if 'winter' in clean_name.lower() or 'gefuttert' in clean_name.lower():
                    return f"Stay warm and stylish this winter with {clean_name}. Premium insulation meets modern design. Perfect for cold weather adventures! ❄️✨"
                else:
                    return f"Layer up in style with {clean_name}. Versatile design that works for any season. From casual to chic, this jacket has you covered! 🌟"
            elif 'kleid' in clean_name.lower() or 'dress' in clean_name.lower():
                return f"Turn heads wherever you go with {clean_name}. Flattering silhouette and premium fabric create the perfect look for any occasion. Elegance redefined! 💃✨"
            elif 'hose' in clean_name.lower() or 'pants' in clean_name.lower():
                return f"Comfort meets style with {clean_name}. Perfect fit and premium materials make these pants a wardrobe essential. Dress up or down with confidence! 👖💫"
            elif 'schuhe' in clean_name.lower() or 'shoes' in clean_name.lower():
                return f"Step out in style with {clean_name}. Superior comfort and eye-catching design make these shoes perfect for any adventure. Walk with confidence! 👟🔥"
            elif 'tasche' in clean_name.lower() or 'bag' in clean_name.lower():
                return f"Carry your essentials in style with {clean_name}. Spacious design meets sophisticated aesthetics. The perfect accessory for the modern lifestyle! 👜✨"
            else:
                # English generic descriptions
                english_descriptions = [
                    f"Discover the perfect blend of style and comfort with {clean_name}. Made with premium materials and attention to detail. Shop now and elevate your wardrobe! ✨",
                    f"Transform your look with {clean_name}. This stunning piece combines modern design with timeless elegance. Perfect for any occasion! 💫",
                    f"Add a touch of sophistication to your collection with {clean_name}. Premium quality meets contemporary style. Don't miss out! 🔥",
                    f"Experience luxury and comfort with {clean_name}. Carefully crafted for the modern lifestyle. Shop the latest trends! 👑",
                    f"Make a statement with {clean_name}. Exceptional quality and stunning design in one perfect piece. Order yours today! ⭐"
                ]
                import random
                return random.choice(english_descriptions)
            
    except Exception as e:
        print(f"   [DEBUG] Error generating pin description: {e}")
        return f"Discover the perfect blend of style and comfort with {product_name}. Made with premium materials and attention to detail. Shop now and elevate your wardrobe! ✨"

def upload_all_creatives_to_pinterest(access_token, creative_data, board_id, product_name, existing_pin_data=None, target_language="de"):
    """Upload ALL creatives (images/videos) from second sheet to Pinterest and create pins"""
    created_pins = []  # List of (pin_id, media_type) tuples
    
    try:
        print(f"   [DEBUG] Creative data keys: {list(creative_data.keys())}")
        print(f"   [DEBUG] Creative data values: {list(creative_data.values())}")
        
        # Look for media URLs in columns J through M (index 9-12)
        # Convert to list to access by index
        creative_values = list(creative_data.values())
        
        # Check columns J through M (index 9-12) for ALL creatives
        for i in range(9, 13):  # J=9, K=10, L=11, M=12
            value = creative_values[i]
            if value and isinstance(value, str) and value.strip():
                print(f"   [DEBUG] Checking column {chr(65 + i)} (index {i}): '{value}'")
                
                # Clean the URL (remove @ prefix if present)
                clean_value = value.strip()
                if clean_value.startswith('@'):
                    clean_value = clean_value[1:]
                
                # Check if it's a valid URL (including Facebook CDN URLs)
                is_valid_url = (any(ext in clean_value.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov', '.avi', '.webm']) or
                               'fbcdn.net' in clean_value.lower() or 'facebook.com' in clean_value.lower())
                
                print(f"   [DEBUG] URL validation: {is_valid_url} for '{clean_value[:100]}...'")
                
                if is_valid_url:
                    # Determine if it's an image or video
                    is_image = any(ext in clean_value.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
                    is_video = any(ext in clean_value.lower() for ext in ['.mp4', '.mov', '.avi', '.webm'])
                    
                    print(f"   [DEBUG] Initial detection - is_image: {is_image}, is_video: {is_video}")
                    
                    # Special handling for Facebook CDN URLs
                    if 'fbcdn.net' in clean_value.lower():
                        if any(ext in clean_value.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                            is_image = True
                        elif any(ext in clean_value.lower() for ext in ['.mp4', '.mov', '.avi', '.webm']):
                            is_video = True
                        print(f"   [DEBUG] After FB CDN check - is_image: {is_image}, is_video: {is_video}")
                    
                    if is_image or is_video:
                        media_type = "image" if is_image else "video"
                        print(f"   [DEBUG] Found {media_type} URL: {clean_value}")
                        
                        # Create pin for this creative
                        # Generate proper marketing-focused titles and descriptions
                        title = generate_pin_title(product_name, {}, existing_pin_data, target_language)
                        description = generate_pin_description(product_name, {}, existing_pin_data, target_language)
                        
                        result = upload_single_creative_to_pinterest(access_token, clean_value, media_type, board_id, title, description, existing_pin_data, product_name, len(created_pins) + 1)
                        if result:
                            pin_id, pin_media_type = result
                            created_pins.append((pin_id, pin_media_type))
                            print(f"   ✅ Created {media_type} pin {len(created_pins)}: {pin_id}")
                        else:
                            print(f"   ❌ Failed to create {media_type} pin from: {clean_value}")
                    else:
                        print(f"   [DEBUG] URL is valid but not recognized as image or video: {clean_value[:100]}...")
                else:
                    print(f"   [DEBUG] URL not valid, skipping: {clean_value[:100]}...")
        
        print(f"   📊 Total creatives processed: {len(created_pins)}")
        return created_pins
        
    except Exception as e:
        print(f"   [DEBUG] Error uploading creatives: {e}")
        return created_pins

def upload_single_creative_to_pinterest(access_token, creative_url, media_type, board_id, title, description, existing_pin_data, product_name, creative_number):
    """
    Upload a single creative (image or video) to Pinterest and create a pin
    """
    print(f"   [DEBUG] Processing {media_type} creative: {creative_url[:100]}...")
    
    # Get media_id for the creative
    if media_type == "image":
        # For images, we'll use the URL directly
        media_id = None
    else:  # video
        # Upload video using proper 4-step process
        media_id = upload_video_to_pinterest(access_token, creative_url)
        if not media_id:
            print(f"   ❌ Failed to upload video")
            return None
    
    # Pinterest requires a cover image for video pins - try 11 different methods to find/generate one
    print(f"   [DEBUG] Pinterest requires cover image for video pins, trying 11 methods to find/generate...")
    cover_image_url = None
    
    # Methods 1-5: Use existing pin's images
    if existing_pin_data:
        for size in ['564x', 'originals', '736x', '474x', '236x']:
            if existing_pin_data.get('media', {}).get('images', {}).get(size, {}).get('url'):
                cover_image_url = existing_pin_data['media']['images'][size]['url']
                print(f"   [METHOD {list(['564x', 'originals', '736x', '474x', '236x']).index(size)+1}] Using existing pin's {size} image: {cover_image_url}")
                break
    
    # Method 6: Use product image from Shopify data
    if not cover_image_url and existing_pin_data and existing_pin_data.get('product_image_url'):
        cover_image_url = existing_pin_data['product_image_url']
        print(f"   [METHOD 6] Using product image from Shopify: {cover_image_url}")
    
    # Method 7: Use first image from product images array
    if not cover_image_url and existing_pin_data and existing_pin_data.get('product_images') and len(existing_pin_data['product_images']) > 0:
        cover_image_url = existing_pin_data['product_images'][0]
        print(f"   [METHOD 7] Using first product image: {cover_image_url}")
    
    # Method 8: Use a reliable placeholder service (Picsum)
    if not cover_image_url:
        cover_image_url = "https://picsum.photos/564/564"
        print(f"   [METHOD 8] Using reliable placeholder image: {cover_image_url}")
    
    # Method 9: Use a simple colored background from a reliable service (Dummyimage)
    if not cover_image_url:
        cover_image_url = "https://dummyimage.com/564x564/4ECDC4/FFFFFF.png&text=Product+Video"
        print(f"   [METHOD 9] Using dummy image service: {cover_image_url}")
    
    # Method 10: Use a simple colored background from another service (Placehold.co)
    if not cover_image_url:
        cover_image_url = "https://placehold.co/564x564/FF6B6B/FFFFFF/png?text=Video+Pin"
        print(f"   [METHOD 10] Using placehold.co service: {cover_image_url}")
    
    # Method 11: Create a simple base64-encoded image directly using PIL
    if not cover_image_url:
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            import base64
            img = Image.new('RGB', (564, 564), color='#FF6B6B')
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            text = "Product Video"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (564 - text_width) // 2
            y = (564 - text_height) // 2
            draw.text((x, y), text, fill='white', font=font)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            cover_image_url = f"data:image/png;base64,{img_str}"
            print(f"   [METHOD 11] Created base64 image directly: {cover_image_url[:50]}...")
        except Exception as e:
            print(f"   [METHOD 11] Failed to create base64 image: {e}")
    
    # Create pin data
    pin_data = {
        "board_id": board_id,
        "title": title,
        "description": description,
        "link": existing_pin_data.get('product_url', '') if existing_pin_data else '',
        "alt_text": f"Additional {media_type} creative {creative_number} for {product_name}"
    }
    
    # Add media source based on type
    if media_type == "image":
        pin_data["media_source"] = {
            "source_type": "image_url",
            "url": creative_url
        }
    else:  # video
        pin_data["media_source"] = {
            "source_type": "video_id",
            "cover_image_url": cover_image_url if cover_image_url else "https://picsum.photos/564/564",
            "media_id": media_id
        }
    
    # Create pin
    import requests
    url = "https://api.pinterest.com/v5/pins"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    if media_type == "video":
        print(f"   [DEBUG] Creating video pin using proper Pinterest API format...")
        
        # Validate media_id before proceeding
        if not media_id:
            print(f"   ❌ No media_id available for video pin creation")
            return None
            
        print(f"   [DEBUG] Using media_id: {media_id}")
        print(f"   [DEBUG] Using cover_image_url: {cover_image_url}")
        
        # Use the correct format from Pinterest documentation
        pin_data = {
            "board_id": board_id,
            "title": title,
            "description": description,
            "media_source": {
                "source_type": "video_id",
                "cover_image_url": cover_image_url if cover_image_url else "https://picsum.photos/564/564",
                "media_id": media_id
            }
        }
        
        print(f"   [DEBUG] Pin data: {pin_data}")
        
        try:
            print(f"   [DEBUG] Sending video pin creation request...")
            response = requests.post(url, headers=headers, json=pin_data)
            print(f"   [DEBUG] Response status: {response.status_code}")
            print(f"   [DEBUG] Response text: {response.text[:500]}")
            
            if response.status_code == 201:
                pin_id = response.json().get('id')
                print(f"   ✅ SUCCESS: Created video pin with proper format: {pin_id}")
                return (pin_id, "video")
            else:
                print(f"   ❌ Failed to create video pin: {response.status_code} - {response.text[:200]}")
                # Try to get more details about the error
                try:
                    error_data = response.json()
                    print(f"   [DEBUG] Error details: {error_data}")
                except:
                    pass
                return None
        except Exception as e:
            print(f"   ❌ Error creating video pin: {e}")
            return None
    else:
        # For images, use the original method
        response = requests.post(url, headers=headers, json=pin_data)
        if response.status_code == 201:
            pin_id = response.json().get('id')
            print(f"   ✅ Successfully created {media_type} pin: {pin_id}")
            return (pin_id, "image")
        else:
            print(f"   ❌ Error creating {media_type} pin: {response.status_code} - {response.text}")
            return None

def upload_video_to_pinterest(access_token, video_url):
    """
    Upload video to Pinterest using the proper 4-step process:
    1. Register intent to upload
    2. Upload to AWS S3
    3. Confirm upload
    4. Return media_id for pin creation
    """
    print(f"   [DEBUG] Starting proper 4-step video upload process...")
    print(f"   [DEBUG] Downloading video from: {video_url[:100]}...")
    
    # Download video content
    try:
        response = requests.get(video_url, timeout=30)
        response.raise_for_status()
        video_content = response.content
        print(f"   [DEBUG] Downloaded video, size: {len(video_content)} bytes")
    except Exception as e:
        print(f"   ❌ Failed to download video: {e}")
        return None
    
    # Step 1: Register intent to upload
    print(f"   [STEP 1] Registering intent to upload video...")
    try:
        register_url = "https://api.pinterest.com/v5/media"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "media_type": "video"
        }
        response = requests.post(register_url, headers=headers, json=data)
        if response.status_code == 201:
            response_data = response.json()
            media_id = response_data.get('media_id')
            upload_url = response_data.get('upload_url')
            upload_parameters = response_data.get('upload_parameters', {})
            print(f"   ✅ Step 1 SUCCESS: media_id = {media_id}")
            print(f"   [DEBUG] Upload URL: {upload_url}")
            print(f"   [DEBUG] Upload parameters: {upload_parameters}")
        else:
            print(f"   ❌ Step 1 failed: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"   ❌ Step 1 error: {e}")
        return None
    
    # Step 2: Upload video file to Pinterest Media AWS bucket
    print(f"   [STEP 2] Uploading video to AWS S3...")
    try:
        import io
        # Create a file-like object from the video content
        video_file = io.BytesIO(video_content)
        
        # Prepare multipart form data
        files = {
            'file': ('video.mp4', video_file, 'video/mp4')
        }
        
        # Add all upload parameters as form data
        form_data = upload_parameters.copy()
        
        # Make the upload request (no Bearer token needed for S3)
        upload_response = requests.post(upload_url, files=files, data=form_data)
        if upload_response.status_code == 204:
            print(f"   ✅ Step 2 SUCCESS: Video uploaded to AWS S3")
        else:
            print(f"   ❌ Step 2 failed: {upload_response.status_code} - {upload_response.text[:200]}")
            return None
    except Exception as e:
        print(f"   ❌ Step 2 error: {e}")
        return None
    
    # Step 3: Confirm upload with extended timeout and better error handling
    print(f"   [STEP 3] Confirming upload status...")
    try:
        import time
        max_attempts = 30  # Increased from 10 to 30 attempts
        wait_time = 3      # Increased from 2 to 3 seconds between attempts
        
        for attempt in range(max_attempts):
            confirm_url = f"https://api.pinterest.com/v5/media/{media_id}"
            confirm_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            confirm_response = requests.get(confirm_url, headers=confirm_headers)
            if confirm_response.status_code == 200:
                confirm_data = confirm_response.json()
                status = confirm_data.get('status')
                print(f"   [DEBUG] Upload status: {status} (attempt {attempt + 1}/{max_attempts})")
                
                if status == 'succeeded':
                    print(f"   ✅ Step 3 SUCCESS: Video upload confirmed")
                    break
                elif status == 'failed':
                    print(f"   ❌ Step 3 failed: Upload failed - {confirm_data}")
                    print(f"   [DEBUG] Trying fallback method...")
                    return upload_video_to_pinterest_fallback(access_token, video_url)
                elif status == 'registered':
                    # Still processing, wait and try again
                    if attempt < max_attempts - 1:
                        print(f"   [DEBUG] Still processing, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"   ❌ Step 3 failed: Upload stuck in 'registered' status after {max_attempts} attempts")
                        print(f"   [DEBUG] This might be due to video format/size issues. Trying fallback method...")
                        # Try fallback method
                        return upload_video_to_pinterest_fallback(access_token, video_url)
                else:
                    # Unknown status, wait and try again
                    if attempt < max_attempts - 1:
                        print(f"   [DEBUG] Unknown status '{status}', waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"   ❌ Step 3 failed: Unknown status '{status}' after {max_attempts} attempts")
                        return None
            else:
                print(f"   ❌ Step 3 failed: {confirm_response.status_code} - {confirm_response.text[:200]}")
                return None
    except Exception as e:
        print(f"   ❌ Step 3 error: {e}")
        return None
    
    print(f"   ✅ All 4 steps completed successfully! media_id = {media_id}")
    return media_id

def upload_video_to_pinterest_fallback(access_token, video_url):
    """
    Fallback method for video upload when the official 4-step process fails.
    Uses direct URL method as an alternative.
    """
    print(f"   [FALLBACK] Trying alternative video upload method...")
    print(f"   [DEBUG] Video URL: {video_url[:100]}...")
    
    try:
        # Method: Direct URL upload (simpler approach)
        url = "https://api.pinterest.com/v5/media"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "media_type": "video",
            "source_url": video_url
        }
        
        print(f"   [FALLBACK] Attempting direct URL upload...")
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            response_data = response.json()
            media_id = response_data.get('media_id')
            print(f"   ✅ FALLBACK SUCCESS: Got media_id = {media_id}")
            return media_id
        else:
            print(f"   ❌ FALLBACK failed: {response.status_code} - {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   ❌ FALLBACK error: {e}")
        return None

READY_COLLECTION_ID = os.getenv("SHOPIFY_COLLECTION_ID")  # numeric ID of "READY FOR PINTEREST"
SHOPIFY_API_VERSION = "2023-10"

def get_product_id_by_title(title, api_key=ADMIN_API_KEY, shop_url=SHOP_URL, api_version=SHOPIFY_API_VERSION):
    """
    Fetches Shopify Product ID by its title. Returns None if not found.
    """
    url = f"https://{SHOP_DOMAIN}/admin/api/{api_version}/products.json"
    params = {"title": title}
    headers = {"X-Shopify-Access-Token": api_key}
    try:
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        time.sleep(0.6)  # Rate limiting
        products = resp.json().get("products", [])
        if not products:
            print(f"[SHOPIFY] Product '{title}' not found.")
            return None
        return products[0]["id"]
    except Exception as e:
        print(f"[SHOPIFY] Error getting product ID for '{title}': {e}")
        return None

def remove_product_from_collection(product_id, collection_id=READY_COLLECTION_ID, api_key=ADMIN_API_KEY, shop_url=SHOP_URL, api_version=SHOPIFY_API_VERSION):
    """
    Removes a product from a manual collection by deleting the relevant collect object.
    """
    # Use SHOP_DOMAIN instead of full URL for API calls
    url = f"https://{SHOP_DOMAIN}/admin/api/{api_version}/collects.json"
    params = {"collection_id": collection_id, "product_id": product_id, "fields": "id"}
    headers = {"X-Shopify-Access-Token": api_key}
    try:
        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()
        time.sleep(0.6)  # Rate limiting: 2 calls per second = 0.5s delay, using 0.6s for safety
        collects = r.json().get("collects", [])
        if not collects:
            print(f"[COLLECTION] Product {product_id} not in collection {collection_id}.")
            return False
        collect_id = collects[0]["id"]
        del_url = f"https://{SHOP_DOMAIN}/admin/api/{api_version}/collects/{collect_id}.json"
        del_resp = requests.delete(del_url, headers=headers)
        time.sleep(0.6)  # Rate limiting
        if del_resp.status_code in (200, 204):
            print(f"[COLLECTION] ✅ Removed product {product_id} from collection {collection_id}.")
            return True
        else:
            print(f"[COLLECTION] ❌ Failed to remove product {product_id} (Collect ID: {collect_id}). {del_resp.text}")
            return False
    except Exception as e:
        print(f"[COLLECTION] Exception: {e}")
        return False

def add_product_to_collection(product_id, collection_id, api_key=ADMIN_API_KEY, shop_url=SHOP_URL, api_version=SHOPIFY_API_VERSION):
    """
    Adds a product to a manual collection by creating a collect object.
    """
    url = f"https://{SHOP_DOMAIN}/admin/api/{api_version}/collects.json"
    headers = {"X-Shopify-Access-Token": api_key, "Content-Type": "application/json"}
    data = {
        "collect": {
            "product_id": product_id,
            "collection_id": collection_id
        }
    }
    try:
        r = requests.post(url, headers=headers, json=data)
        time.sleep(0.6)  # Rate limiting
        if r.status_code in (200, 201):
            print(f"[COLLECTION] ✅ Added product {product_id} to collection {collection_id}.")
            return True
        else:
            print(f"[COLLECTION] ❌ Failed to add product {product_id} to collection {collection_id}. {r.text}")
            return False
    except Exception as e:
        print(f"[COLLECTION] Exception: {e}")
        return False

def move_product_between_collections(product_id, from_collection_id, to_collection_id, api_key=ADMIN_API_KEY, shop_url=SHOP_URL, api_version=SHOPIFY_API_VERSION):
    """
    Moves a product from one collection to another.
    First removes from source collection, then adds to destination collection.
    """
    print(f"[COLLECTION] Moving product {product_id} from collection {from_collection_id} to {to_collection_id}")
    
    # Step 1: Remove from source collection
    remove_success = remove_product_from_collection(product_id, from_collection_id, api_key, shop_url, api_version)
    if not remove_success:
        print(f"[COLLECTION] ⚠️ Could not remove product {product_id} from collection {from_collection_id}")
        return False
    
    # Step 2: Add to destination collection
    add_success = add_product_to_collection(product_id, to_collection_id, api_key, shop_url, api_version)
    if not add_success:
        print(f"[COLLECTION] ❌ Failed to add product {product_id} to collection {to_collection_id}")
        return False
    
    print(f"[COLLECTION] ✅ Successfully moved product {product_id} from {from_collection_id} to {to_collection_id}")
    return True

def move_processed_products_to_generated_collection():
    """
    Checks Google Sheet for products that already have generated pin titles/descriptions
    and moves them from READY FOR PINTEREST collection to GENERATED collection.
    This prevents duplicate processing of products that already have pin content.
    
    Performs multiple passes until no more products need to be moved to ensure
    complete cleanup and prevent any duplicate generation.
    """
    print(f"\n🔄 Starting collection cleanup: Moving processed products to GENERATED collection...")
    print(f"   📋 Source collection: READY FOR PINTEREST (ID: {READY_COLLECTION_ID})")
    print(f"   📋 Destination collection: GENERATED (ID: {GENERATED_COLLECTION_ID})")
    print(f"   🔄 Will perform multiple passes until 0 products need moving")
    
    if not READY_COLLECTION_ID:
        print("❌ READY_COLLECTION_ID not configured. Cannot proceed with collection cleanup.")
        return False
    
    try:
        # Get data from Google Sheet
        from utils import get_sheet_cached
        sheet = get_sheet_cached()
        sheet_data = sheet.get_all_values()
        if not sheet_data or len(sheet_data) < 2:  # Need at least header + 1 row
            print("⚠️ No data found in Google Sheet or only headers present.")
            return False
        
        headers = sheet_data[0]
        print(f"📊 Found {len(sheet_data)-1} rows in Google Sheet")
        
        # Find column indices
        product_url_idx = None
        pin_title_idx = None
        pin_description_idx = None
        
        for i, header in enumerate(headers):
            if 'product url' in header.lower():
                product_url_idx = i
            elif 'generated pin title' in header.lower():
                pin_title_idx = i
            elif 'generated pin description' in header.lower():
                pin_description_idx = i
        
        if product_url_idx is None:
            print("❌ Could not find 'Product URL' column in Google Sheet")
            return False
        
        if pin_title_idx is None or pin_description_idx is None:
            print("❌ Could not find 'Generated Pin Title' or 'Generated Pin Description' columns in Google Sheet")
            return False
        
        print(f"📋 Found columns: Product URL (index {product_url_idx}), Pin Title (index {pin_title_idx}), Pin Description (index {pin_description_idx})")
        
        # Perform multiple passes until no more products need to be moved
        total_moved = 0
        pass_number = 1
        max_passes = 10  # Safety limit to prevent infinite loops
        
        while pass_number <= max_passes:
            print(f"\n🔄 === PASS {pass_number} === Checking Google Sheet for processed products...")
            
            # First, find all products in Google Sheet that have generated content
            processed_products_in_sheet = []
            for row_idx, row in enumerate(sheet_data[1:], start=2):  # Skip header, start from row 2
                if len(row) <= max(product_url_idx, pin_title_idx, pin_description_idx):
                    continue
                
                sheet_product_url = row[product_url_idx].strip() if len(row) > product_url_idx else ""
                pin_title = row[pin_title_idx].strip() if len(row) > pin_title_idx else ""
                pin_description = row[pin_description_idx].strip() if len(row) > pin_description_idx else ""
                
                # Check if this product has generated pin content
                if sheet_product_url and pin_title and pin_description:
                    processed_products_in_sheet.append({
                        'url': sheet_product_url,
                        'title': pin_title,
                        'description': pin_description,
                        'row': row_idx
                    })
            
            print(f"📊 Found {len(processed_products_in_sheet)} products in Google Sheet with generated content")
            
            if not processed_products_in_sheet:
                print("✅ No products with generated content found in Google Sheet")
                break
            
            # Get products currently in READY FOR PINTEREST collection
            print(f"🔄 Fetching products from READY FOR PINTEREST collection...")
            from forefront import get_collection_products
            ready_products = get_collection_products(READY_COLLECTION_ID)
            if not ready_products:
                print("✅ No products found in READY FOR PINTEREST collection")
                break
            
            print(f"📦 Found {len(ready_products)} products in READY FOR PINTEREST collection")
            
            # Check each processed product from Google Sheet to see if it's still in READY FOR PINTEREST
            products_to_move = []
            for sheet_product in processed_products_in_sheet:
                sheet_url = sheet_product['url']
                
                # Look for this product in the READY FOR PINTEREST collection
                for shopify_product in ready_products:
                    product_id = str(shopify_product['id'])
                    product_handle = shopify_product.get('handle', '')
                    product_title = shopify_product.get('title', '')
                    
                    # Check if this is the same product (by URL or handle)
                    is_same_product = False
                    if sheet_url and product_handle:
                        # Try to match by URL or handle
                        if product_handle in sheet_url or sheet_url in shopify_product.get('url', ''):
                            is_same_product = True
                    
                    if is_same_product:
                        print(f"✅ Found processed product still in READY FOR PINTEREST: {product_title} (ID: {product_id})")
                        products_to_move.append({
                            'id': product_id,
                            'title': product_title,
                            'url': sheet_url,
                            'sheet_row': sheet_product['row']
                        })
                        break
            
            if not products_to_move:
                print(f"✅ Pass {pass_number}: No processed products found in READY FOR PINTEREST collection")
                print(f"🎉 Collection cleanup completed! No more products need to be moved.")
                break
            
            print(f"🔄 Pass {pass_number}: Found {len(products_to_move)} processed products to move to GENERATED collection")
            
            # Move products to GENERATED collection
            moved_count = 0
            for product in products_to_move:
                product_id = product['id']
                product_title = product['title']
                
                print(f"🔄 Moving product: {product_title} (ID: {product_id})")
                
                success = move_product_between_collections(
                    product_id, 
                    READY_COLLECTION_ID, 
                    GENERATED_COLLECTION_ID
                )
                
                if success:
                    moved_count += 1
                    print(f"✅ Successfully moved {product_title} to GENERATED collection")
                else:
                    print(f"❌ Failed to move {product_title} to GENERATED collection")
            
            total_moved += moved_count
            print(f"✅ Pass {pass_number}: Successfully moved {moved_count} products")
            
            # If we moved 0 products in this pass, we're done
            if moved_count == 0:
                print(f"✅ Pass {pass_number}: No products were moved. Cleanup complete.")
                break
            
            pass_number += 1
        
        if pass_number > max_passes:
            print(f"⚠️ Reached maximum number of passes ({max_passes}). Stopping to prevent infinite loop.")
        
        print(f"\n🎉 Collection cleanup completed!")
        print(f"   ✅ Total products moved: {total_moved}")
        print(f"   📋 Products moved from READY FOR PINTEREST to GENERATED collection")
        print(f"   🔄 Completed {pass_number-1} passes")
        
        return total_moved > 0
        
    except Exception as e:
        print(f"❌ Error during collection cleanup: {e}")
        return False

def get_next_tuesday_date_string():
    now = datetime.datetime.utcnow()
    today = now.date()
    weekday = today.weekday()
    days_until_tuesday = (1 - weekday + 7) % 7
    tuesday_candidate = today + datetime.timedelta(days=days_until_tuesday)
    # If today is already Tuesday after 00:01, get the next week
    tuesday_time = datetime.datetime.combine(tuesday_candidate, datetime.time(0, 1))
    if now >= tuesday_time:
        tuesday_candidate = tuesday_candidate + datetime.timedelta(days=7)
    return tuesday_candidate.strftime('%Y-%m-%d')

def get_next_tuesday_02_01_unix():
    now = datetime.datetime.utcnow()
    today = now.date()
    weekday = today.weekday()  # Monday = 0, Tuesday = 1, ..., Sunday = 6

    days_until_tuesday = (1 - weekday + 7) % 7
    tuesday_candidate = today + datetime.timedelta(days=days_until_tuesday)
    tuesday_time = datetime.datetime.combine(tuesday_candidate, datetime.time(0, 1))

    # If we're already past this Tuesday 00:01 UTC, jump to next week
    if now >= tuesday_time:
        tuesday_time = tuesday_time + datetime.timedelta(days=7)
    # Add 2 hours (for CEST)
    tuesday_time_plus_2h = tuesday_time + datetime.timedelta(hours=2)
    return int(tuesday_time_plus_2h.timestamp())

def get_start_time_from_launch_date(launch_date):
    """
    Convert launch_date string to Unix timestamp for Pinterest API
    
    Args:
        launch_date (str): Date in YYYY-MM-DD format
        
    Returns:
        int: Unix timestamp for the launch date at 02:01 UTC (for CEST timezone)
    """
    try:
        # Parse the launch date
        launch_date_obj = datetime.datetime.strptime(launch_date, "%Y-%m-%d").date()
        
        # Create datetime object for 02:01 UTC (for CEST timezone)
        launch_datetime = datetime.datetime.combine(launch_date_obj, datetime.time(2, 1))
        
        # Convert to UTC if needed (assuming input is in local time)
        # For immediate start, use current time + 1 minute
        if launch_date == datetime.datetime.now().strftime('%Y-%m-%d'):
            launch_datetime = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
        
        return int(launch_datetime.timestamp())
    except ValueError:
        # Fallback to next Tuesday if date parsing fails
        print(f"[WARNING] Invalid launch date '{launch_date}', falling back to next Tuesday")
        return get_next_tuesday_02_01_unix()

def safe_request(method, url, **kwargs):
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(method, url, **kwargs)
            print(f"[DEBUG] Attempt {attempt}: {method} {url} {kwargs.get('json') or ''}")
            print(f"[DEBUG] Response {response.status_code}: {response.text[:500]}")
            if response.status_code in (200, 201):
                return response
            elif 400 <= response.status_code < 500:
                print(f"[ERROR] Client error: {response.status_code} {response.text}")
                break
            else:
                print(f"[WARN] Retrying due to status {response.status_code}")
        except Exception as ex:
            print(f"[EXCEPTION] Network or code error: {ex}")
        time.sleep(2)
    return None

def create_campaign(access_token, ad_account_id, campaign_name, start_time=None, launch_date=None, daily_budget=100, objective_type="WEB_CONVERSION"):
    

    url = f"{BASE_URL}/ad_accounts/{ad_account_id}/campaigns"

    if start_time is None:
        start_time = get_next_tuesday_02_01_unix()
    if launch_date is None:
        launch_date = get_next_tuesday_date_string()

    campaign_full_name = f"{launch_date} UTC {campaign_name} | {objective_type}"

    # Convert cents to microeuros: 1 cent = 10,000 microeuros (1 euro = 1,000,000 microeuros)
    daily_spend_cap_microeuros = daily_budget * 10000
    print(f"[DEBUG] Daily budget conversion: {daily_budget} cents -> {daily_spend_cap_microeuros} microeuros (€{daily_budget/100:.2f})")
    
    payload = [{
        "ad_account_id": ad_account_id,
        "name": campaign_full_name,
        "status": "ACTIVE",
        "objective_type": objective_type,
        "daily_spend_cap": daily_spend_cap_microeuros,
        "is_flexible_daily_budgets": True,
        "start_time": start_time,
        "is_performance_plus": True
    }]

    print(f"[API] create_campaign: objective_type={payload[0]['objective_type']}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    print(f"[DEBUG] Creating campaign with payload (must be array of dict):\n{payload}")
    response = safe_request('POST', url, json=payload, headers=headers)
    if not response:
        print(f"[ERROR] Could not create campaign after retries.")
        return None

    try:
        resp_json = response.json()
        print(f"[DEBUG] Raw campaign creation response: {resp_json}")
        items = resp_json.get("items")
        if items:
            for item in items:
                data = item.get("data", item)
                cid = data.get("id")
                if cid:
                    print(f"[SUCCESS] Campaign created with ID: {cid}")
                    return cid
        if "id" in resp_json:
            print(f"[SUCCESS] Campaign created with ID: {resp_json['id']}")
            return resp_json['id']
    except Exception as e:
        print(f"[ERROR] Unexpected format or exception: {e}, response: {response.text}")
    print("[ERROR] No campaign ID found in Pinterest API response.")
    return None

def create_campaign_consideration(access_token, ad_account_id, campaign_name, start_time=None, launch_date=None):
    
    url = f"{BASE_URL}/ad_accounts/{ad_account_id}/campaigns"

    if start_time is None:
        start_time = get_next_tuesday_02_01_unix()
    if launch_date is None:
        launch_date = get_next_tuesday_date_string()

    objective_type = "CONSIDERATION"
    campaign_full_name = f"{launch_date} UTC {campaign_name} | {objective_type}"

    payload = [{
        "ad_account_id": ad_account_id,
        "name": campaign_full_name,
        "status": "ACTIVE",
        "objective_type": "CONSIDERATION",
        "daily_spend_cap": 1000000,
        "is_flexible_daily_budgets": True,
        "start_time": start_time,
        "is_performance_plus": True
    }]
    print(f"[API] create_campaign_consideration: objective_type={payload[0]['objective_type']}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    print(f"[DEBUG] Creating consideration campaign with payload:\n{payload}")
    response = safe_request('POST', url, json=payload, headers=headers)
    if not response:
        print(f"[ERROR] Could not create consideration campaign after retries.")
        return None

    try:
        resp_json = response.json()
        print(f"[DEBUG] Raw consideration campaign creation response: {resp_json}")
        items = resp_json.get("items")
        if items:
            for item in items:
                data = item.get("data", item)
                cid = data.get("id")
                if cid:
                    print(f"[SUCCESS] Consideration campaign created with ID: {cid}")
                    return cid
        if "id" in resp_json:
            print(f"[SUCCESS] Consideration campaign created with ID: {resp_json['id']}")
            return resp_json['id']
    except Exception as e:
        print(f"[ERROR] Unexpected format or exception: {e}, response: {response.text}")
    print("[ERROR] No campaign ID found in Pinterest API response.")
    return None


def create_ad_group(access_token, ad_account_id, campaign_id, product_name, max_retries=3):
    import time
    url = f"{BASE_URL}/ad_accounts/{ad_account_id}/ad_groups"
    payload = [{
        "ad_account_id": ad_account_id,
        "campaign_id": campaign_id,
        "name": f"{product_name} Ad Group",
        "status": "ACTIVE",
        "bid_strategy_type": "AUTOMATIC_BID",
        "billable_event": "IMPRESSION",  # <-- For WEB_CONVERSION!
        "optimization_goal_metadata": {
            "conversion_tag_v3_goal_metadata": {
                "conversion_event": "CHECKOUT"
            }
        },
        "targeting_spec": {
            "LOCATION": ["DE"]  # Customize as needed
        },
        "creative_optimization": True   
    }]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for attempt in range(1, max_retries + 1):
        print(f"[DEBUG] Attempt {attempt}: POST {url} {payload}")
        response = requests.post(url, json=payload, headers=headers)
        print(f"[DEBUG] Response {response.status_code}: {response.text}")
        try:
            data = response.json()
        except Exception as e:
            print(f"[ERROR] Could not decode JSON: {e}")
            if attempt == max_retries:
                return None
            time.sleep(2)
            continue

        # Check if a group was created
        if response.status_code in (200, 201):
            try:
                # New API returns: {"items": [{"data": {..., "id": "xxxx"}}]}
                ad_group_id = data["items"][0]["data"]["id"]
                print(f"[SUCCESS] Ad group created with ID: {ad_group_id}")
                return ad_group_id
            except Exception as e:
                print(f"[ERROR] Unexpected format in ad group response: {data}")
                if attempt == max_retries:
                    return None
        else:
            # Check if there are exceptions in the response
            if "items" in data and data["items"] and "exceptions" in data["items"][0]:
                print(f"[ERROR] API Exception: {data['items'][0]['exceptions']}")
            else:
                print(f"[ERROR] Ad group creation failed: {data}")
            if attempt == max_retries:
                return None
            time.sleep(2)

    print("[FATAL] Ad group creation failed after retries.")
    return None


def validate_pin_exists(access_token, pin_id):
    """Validate if a pin exists before creating an ad"""
    try:
        url = f"{BASE_URL}/pins/{pin_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        
        print(f"[DEBUG] Validating pin {pin_id}: {response.status_code}")
        
        if response.status_code == 200:
            pin_data = response.json()
            print(f"[DEBUG] Pin {pin_id} exists: {pin_data.get('id', 'No ID')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️ Pin {pin_id} not found (404) - skipping ad creation")
            return False
        else:
            print(f"⚠️ Could not validate pin {pin_id}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ Error validating pin {pin_id}: {e}")
        return False

def create_ad(access_token, ad_account_id, ad_group_id, pin_id, ad_name, creative_type="REGULAR", max_retries=3):
    # Validate pin exists before creating ad
    if not validate_pin_exists(access_token, pin_id):
        return None
    
    url = f"{BASE_URL}/ad_accounts/{ad_account_id}/ads"
    payload = {
        "ad_group_id": ad_group_id,
        "pin_id": pin_id if isinstance(pin_id, str) else pin_id.get("pin_id", ""),  # ensure string here
        "status": "ACTIVE",
        "creative_type": creative_type,  # REGULAR for images, VIDEO for video pins
        "name": ad_name,
        "customizable_cta_type": "ON_SALE"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for attempt in range(1, max_retries + 1):
        print(f"[DEBUG] Creating ad for pin {pin_id} with payload:\n{payload}")
        response = requests.post(url, json=[payload], headers=headers)  # <-- CHANGED TO [payload]
        print(f"[DEBUG] Attempt {attempt}: POST {url} {[payload]}")
        print(f"[DEBUG] Response {response.status_code}: {response.text}")
        try:
            data = response.json()
        except Exception as e:
            print(f"[ERROR] Could not decode JSON: {e}")
            if attempt == max_retries:
                return None
            time.sleep(2)
            continue

        if response.status_code in (200, 201):
            # Check for Pinterest API errors in the response
            if "items" in data and len(data["items"]) > 0:
                item = data["items"][0]
                if "exceptions" in item:
                    error_code = item["exceptions"].get("code")
                    error_message = item["exceptions"].get("message", "")
                    if error_code == 2941 and "Pin not found" in error_message:
                        print(f"❌ Pin {pin_id} not found (2941) - skipping ad creation")
                        return None
                    else:
                        print(f"❌ Pinterest API error: {error_code} - {error_message}")
                        if attempt == max_retries:
                            return None
                        time.sleep(2)
                        continue
                elif "data" in item:
                    try:
                        ad_id = item["data"]["id"]
                        print(f"[SUCCESS] Created Ad ID: {ad_id}")
                        return ad_id
                    except Exception as e:
                        print(f"[ERROR] Could not extract ad ID: {e}")
                        if attempt == max_retries:
                            return None
            else:
                print(f"[ERROR] No items in response: {data}")
                if attempt == max_retries:
                    return None
        else:
            if "items" in data and data["items"] and "exceptions" in data["items"][0]:
                print(f"[ERROR] API Exception: {data['items'][0]['exceptions']}")
            else:
                print(f"[ERROR] Ad creation failed: {data}")
            if attempt == max_retries:
                return None
            time.sleep(2)
    print(f"[ERROR] Could not create ad after retries for pin {pin_id}")
    return None

def run(campaign_mode="single_product", products_per_campaign=1, daily_budget=100, campaign_type="WEB_CONVERSION", target_language="de", enable_second_sheet=False, second_sheet_id="", campaign_start_date="next_tuesday", custom_start_date=""):
    """
    Run Pinterest campaign automation
    
    Args:
        campaign_mode (str): "single_product" or "multi_product"
        products_per_campaign (int): Number of products per campaign (for multi_product mode)
        daily_budget (int): Daily budget in cents
        campaign_type (str): "WEB_CONVERSION", "CONSIDERATION", or "CATALOG_SALES"
        enable_second_sheet (bool): Whether to process a second sheet with images/videos
        second_sheet_id (str): Google Sheet ID for the second sheet
        campaign_start_date (str): "immediate", "next_tuesday", or "custom"
        custom_start_date (str): Custom start date in YYYY-MM-DD format (if campaign_start_date="custom")
    """
    print("🚀 Pinterest Campaign Automation Started")
    print(f"📊 Campaign Mode: {campaign_mode}")
    if campaign_mode == "multi_product":
        print(f"📊 Products per Campaign: {products_per_campaign}")
    if enable_second_sheet:
        print(f"📊 Second Sheet Enabled: {second_sheet_id}")

    access_token = get_access_token()
    ad_account_id = get_ad_account_id(access_token)
    pins_by_product = load_pins_from_sheet()
    if not pins_by_product:
        print("⚠️ No eligible pins found for advertising.")
        print("✅ AUTOMATION RUN COMPLETE: All available content has been processed")
        return "NO_ELIGIBLE_PINS"

    print(f"[INFO] Found {sum(len(v) for v in pins_by_product.values())} eligible pins across {len(pins_by_product)} products.")

    # All products for the selected campaign type
    all_products = list(pins_by_product.items())
    random.shuffle(all_products)

    print(f"[DEBUG] Total products: {len(all_products)}")
    print(f"[DEBUG] Products for {campaign_type} campaigns: {[p[0] for p in all_products]}")

    pin_updates = {}
    campaign_tracking = {}  # Track campaign IDs by product name for second sheet processing
    
    # Determine launch date based on user selection
    if campaign_start_date == "immediate":
        launch_date = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"📅 Campaigns will start immediately (today: {launch_date})")
    elif campaign_start_date == "custom" and custom_start_date:
        launch_date = custom_start_date
        print(f"📅 Campaigns will start on custom date: {launch_date}")
    else:  # default to next_tuesday
        launch_date = get_next_tuesday_date_string()
        print(f"📅 Campaigns will start next Tuesday: {launch_date}")

    # --- Campaign creation based on selected type ---
    print(f"==== {campaign_type} CAMPAIGN LOOP ====")
    
    if campaign_mode == "single_product":
        # One product per campaign (original behavior)
        for product_name, pin_entries in all_products:
            print(f"[ACTION] Creating **{campaign_type}** campaign for '{product_name}' with {len(pin_entries)} pins.")
            start_time = get_start_time_from_launch_date(launch_date)
            campaign_id = create_campaign(access_token, ad_account_id, product_name, start_time=start_time, launch_date=launch_date, daily_budget=daily_budget, objective_type=campaign_type)
            if not campaign_id:
                print("[FATAL] Campaign creation failed, skipping product.")
                continue
            
            # Track campaign ID for second sheet processing
            campaign_tracking[product_name] = {
                'campaign_id': campaign_id,
                'ad_group_id': None,
                'pins': []
            }
            
            ad_group_id = create_ad_group(access_token, ad_account_id, campaign_id, product_name)
            if not ad_group_id:
                print("[FATAL] Ad group creation failed, skipping product.")
                continue
            
            # Update campaign tracking with ad group ID
            campaign_tracking[product_name]['ad_group_id'] = ad_group_id
            
            # Create ads for all pins in the campaign
            for i, pin_entry in enumerate(pin_entries):
                pin_id = pin_entry['pin_id']
                print(f"   📌 Creating ad for pin {pin_id} in campaign {campaign_id}")
                ad_name = f"{product_name} - Pin {i+1} Ad"
                ad_id = create_ad(access_token, ad_account_id, ad_group_id, pin_id, ad_name)
                if ad_id:
                    from datetime import datetime
                    today = datetime.now().strftime('%Y-%m-%d')
                    pin_updates[pin_id] = {
                        'Ad Campaign Status': 'ACTIVE',
                        'Ad Campaign ID': campaign_id,
                        'Advertised At': today
                    }
                    # Track pin for second sheet processing
                    campaign_tracking[product_name]['pins'].append(pin_id)
                    print(f"   ✅ Successfully created ad {ad_id} for pin {pin_id}")
                else:
                    print(f"   ❌ Failed to create ad for pin {pin_id}")
    
    elif campaign_mode == "multi_product":
        # Multiple products per campaign - ONE ad group only (Pinterest Performance+ limitation)
        for i in range(0, len(all_products), products_per_campaign):
            batch_products = all_products[i:i + products_per_campaign]
            campaign_name = f"Multi-Product Campaign {i//products_per_campaign + 1}"
            
            print(f"[ACTION] Creating **{campaign_type}** campaign '{campaign_name}' with {len(batch_products)} products.")
            start_time = get_start_time_from_launch_date(launch_date)
            campaign_id = create_campaign(access_token, ad_account_id, campaign_name, start_time=start_time, launch_date=launch_date, daily_budget=daily_budget, objective_type=campaign_type)
            if not campaign_id:
                print("[FATAL] Campaign creation failed, skipping batch.")
                continue
            
            # Create ONE ad group for the entire campaign (Pinterest Performance+ requirement)
            ad_group_name = f"Mixed Products Ad Group {i//products_per_campaign + 1}"
            print(f"  📦 Creating single ad group '{ad_group_name}' for all {len(batch_products)} products.")
            ad_group_id = create_ad_group(access_token, ad_account_id, campaign_id, ad_group_name)
            if not ad_group_id:
                print(f"[FATAL] Ad group creation failed, skipping campaign.")
                continue
            
            # Add ALL products' pins to the single ad group
            for product_name, pin_entries in batch_products:
                print(f"  📦 Adding {len(pin_entries)} pins from '{product_name}' to shared ad group.")
                for j, pin_entry in enumerate(pin_entries):
                    pin_id = pin_entry['pin_id']
                    print(f"   📌 Creating ad for pin {pin_id} (from {product_name}) in campaign {campaign_id}")
                    ad_name = f"{product_name} - Pin {j+1} Ad"
                    ad_id = create_ad(access_token, ad_account_id, ad_group_id, pin_id, ad_name)
                    if ad_id:
                        from datetime import datetime
                        today = datetime.now().strftime('%Y-%m-%d')
                        pin_updates[pin_id] = {
                            'Ad Campaign Status': 'ACTIVE',
                            'Ad Campaign ID': campaign_id,
                            'Advertised At': today
                        }
                        print(f"   ✅ Successfully created ad {ad_id} for pin {pin_id}")
                    else:
                        print(f"   ❌ Failed to create ad for pin {pin_id}")

    # --- Consideration campaigns (CONSIDERATION) - DISABLED ---
    # print("==== CONSIDERATION CAMPAIGN LOOP ====")
    # for product_name, pin_entries in consideration_products:
    #     print(f"[ACTION] Creating **CONSIDERATION** campaign for '{product_name}' with {len(pin_entries)} pins.")
    #     campaign_id = create_campaign_consideration(access_token, ad_account_id, product_name, launch_date=launch_date)
    #     if not campaign_id:
    #         print("[FATAL] Consideration campaign creation failed, skipping product.")
    #         continue
    #     ad_group_id = create_ad_group(access_token, ad_account_id, campaign_id, product_name)
    #     if not ad_group_id:
    #         print("[FATAL] Ad group creation failed, skipping product.")
    #         continue
    #     for pin_entry in pin_entries:
    #         pin_id = pin_entry['pin_id']
    #         ad_id = create_ad(access_token, ad_account_id, ad_group_id, pin_id, f"{product_name} Ad")
    #         if ad_id:
    #             pin_updates[pin_id] = {'Ad Campaign ID': campaign_id, 'Ad Campaign Status': 'ACTIVE'}
    #         else:
    #             print(f"[FAIL] Skipped pin {pin_id} due to ad creation error.")

    print(f"[DEBUG] pin_updates to write: {pin_updates}")

    # Process second sheet if enabled
    if enable_second_sheet and second_sheet_id:
        print(f"\n--- Processing Second Sheet: {second_sheet_id} ---")
        print(f"[DEBUG] Campaign tracking: {campaign_tracking}")
        
        second_sheet_data = load_second_sheet_data(second_sheet_id)
        
        if second_sheet_data:
            print(f"📊 Found {len(second_sheet_data)} products in second sheet")
            print(f"[DEBUG] Second sheet data keys: {list(second_sheet_data.keys())}")
            
            # Process each product from the main sheet
            for product_name, pin_entries in all_products:
                print(f"\n[DEBUG] Processing product: '{product_name}'")
                
                # Get product ID from main sheet using handle + collection
                product_id = get_product_id_from_main_sheet(product_name)
                print(f"[DEBUG] Product ID from main sheet: {product_id}")
                
                if product_id and product_id in second_sheet_data:
                    print(f"🎯 Found matching creative for '{product_name}' by product ID: {product_id}")
                    creative_data = second_sheet_data[product_id]
                    print(f"   📸 Found creative data for product: {product_name}")
                    
                    # Check if we have campaign tracking for this product
                    if product_name in campaign_tracking:
                        campaign_info = campaign_tracking[product_name]
                        campaign_id = campaign_info['campaign_id']
                        ad_group_id = campaign_info['ad_group_id']
                        
                        print(f"[DEBUG] Campaign info for '{product_name}': {campaign_info}")
                        
                        # Get board ID from the first pin entry
                        board_id = None
                        board_title = None
                        if pin_entries:
                            print(f"[DEBUG] Pin entries for '{product_name}': {pin_entries}")
                            # Try different possible keys for board ID
                            first_pin = pin_entries[0]
                            print(f"[DEBUG] First pin entry keys: {list(first_pin.keys())}")
                            
                            # First try to get board ID directly
                            for key in ['board_id', 'boardId', 'board', 'Board ID']:
                                if key in first_pin:
                                    board_id = first_pin[key]
                                    print(f"[DEBUG] Found board ID using key '{key}': {board_id}")
                                    break
                            
                            # If no board ID found, try to get board title and resolve to ID
                            if not board_id:
                                for key in ['board_title', 'boardTitle', 'board_name', 'Board Title']:
                                    if key in first_pin:
                                        board_title = first_pin[key]
                                        print(f"[DEBUG] Found board title using key '{key}': {board_title}")
                                        break
                                
                                if board_title:
                                    print(f"[DEBUG] Attempting to resolve board title '{board_title}' to board ID...")
                                    print(f"[DEBUG] Board title length: {len(board_title)} characters")
                                    print(f"[DEBUG] Board title bytes: {board_title.encode('utf-8')}")
                                    
                                    # Get board ID from Pinterest using board title
                                    board_id = get_board_id_by_title(access_token, board_title)
                                    if board_id:
                                        print(f"[DEBUG] Successfully resolved board title '{board_title}' to board ID: {board_id}")
                                    else:
                                        print(f"[DEBUG] Could not resolve board title '{board_title}' to board ID")
                                        # Fallback: try to find board by partial name match
                                        board_id = find_board_by_partial_name(access_token, board_title)
                                        if board_id:
                                            print(f"[DEBUG] Found board using partial name match: {board_id}")
                                        else:
                                            print(f"[DEBUG] No board found even with partial name matching")
                                            
                                            # Additional fallback: try common variations
                                            variations = [
                                                "Sommer Outfit Inspirationen",
                                                "sommer outfit inspirationen", 
                                                "SOMMER OUTFIT INSPIRATIONEN",
                                                "Sommer-Outfit-Inspirationen",
                                                "Sommer Outfit",
                                                "Outfit Inspirationen"
                                            ]
                                            
                                            for variation in variations:
                                                print(f"[DEBUG] Trying variation: '{variation}'")
                                                board_id = get_board_id_by_title(access_token, variation)
                                                if board_id:
                                                    print(f"[DEBUG] Found board using variation '{variation}': {board_id}")
                                                    break
                                            
                                            if not board_id:
                                                print(f"[DEBUG] No board found with any variation")
                                else:
                                    print(f"[DEBUG] No board title found in pin data")
                        
                        if not board_id:
                            print(f"⚠️ No board ID found for '{product_name}', skipping creative upload")
                            print(f"[DEBUG] Available keys in first pin: {list(pin_entries[0].keys()) if pin_entries else 'No pin entries'}")
                            continue
                        
                        # Upload ALL creatives to Pinterest (multiple creatives per product)
                        print(f"   📸 Processing creative data: {creative_data}")
                        
                        # Get existing pin data for title/description reference
                        existing_pin_data = None
                        if pin_entries and len(pin_entries) > 0:
                            existing_pin_data = pin_entries[0]
                            print(f"   [DEBUG] Using existing pin data for title/description: {existing_pin_data}")
                        
                        # Process all creatives from the second sheet
                        created_pins = upload_all_creatives_to_pinterest(access_token, creative_data, board_id, product_name, existing_pin_data, target_language)
                        
                        for i, (new_pin_id, pin_media_type) in enumerate(created_pins):
                            if new_pin_id:
                                print(f"   ✅ Successfully created pin {i+1}: {new_pin_id} (type: {pin_media_type})")
                                
                                # Create ad for the additional pin in existing campaign
                                ad_name = f"{product_name} - Additional Creative {i+1} Ad"
                                
                                # Determine creative type for ad creation
                                creative_type = "VIDEO" if pin_media_type == "video" else "REGULAR"
                                ad_id = create_ad(access_token, ad_account_id, ad_group_id, new_pin_id, ad_name, creative_type)
                                
                                if ad_id:
                                    print(f"   ✅ Successfully created ad {ad_id} for additional pin {new_pin_id}")
                                    from datetime import datetime
                                    today = datetime.now().strftime('%Y-%m-%d')
                                    pin_updates[new_pin_id] = {
                                        'Ad Campaign Status': 'ACTIVE',
                                        'Ad Campaign ID': campaign_id,
                                        'Advertised At': today
                                    }
                                    # Track the new pin
                                    campaign_tracking[product_name]['pins'].append(new_pin_id)
                                else:
                                    print(f"   ❌ Failed to create ad for additional pin {new_pin_id}")
                            else:
                                print(f"   ❌ Failed to create pin {i+1} for product: {product_name}")
                        
                        if not created_pins:
                            print(f"   ❌ No creatives found for product: {product_name}")
                    else:
                        print(f"⚠️ No campaign tracking found for '{product_name}'")
                else:
                    print(f"⚠️ No additional creatives found for '{product_name}' (ID: {product_id})")
                    if not product_id:
                        print(f"   [DEBUG] Product ID extraction failed for: '{product_name}'")
                    elif product_id not in second_sheet_data:
                        print(f"   [DEBUG] Product ID {product_id} not found in second sheet data")
                        print(f"   [DEBUG] Available product IDs in second sheet: {list(second_sheet_data.keys())[:10]}...")
        else:
            print("❌ Could not load second sheet data")
    else:
        print(f"[DEBUG] Second sheet processing disabled or no sheet ID provided")
        print(f"[DEBUG] enable_second_sheet: {enable_second_sheet}, second_sheet_id: {second_sheet_id}")

    # After processing all products, update the sheet in one batch:
    sheet = get_sheet_cached()
    headers, data_rows = get_sheet_data(sheet)
    print("[DEBUG] Sheet headers:", headers)   # <--- Moved here!
    batch_updates = plan_batch_updates(headers, data_rows, pin_updates)
    print("[DEBUG] Batch updates to write:", batch_updates)   # Also print batch_updates
    batch_write_to_sheet(sheet, batch_updates)


def generate_extra_creatives_for_non_active_rows(sheet_data, music_folder_path="music", output_dir="creative_examples/generated_creatives"):
    """
    Generate 4 creative types for products with non-ACTIVE rows
    """
    try:
        import os
        from collections import defaultdict
        
        print(f"🎨 Starting extra creative generation for non-ACTIVE rows...")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Group rows by product name, filtering for non-ACTIVE rows
        product_groups = defaultdict(list)
        non_active_count = 0
        
        for row_idx, row in enumerate(sheet_data):
            if len(row) > 10:  # Ensure we have enough columns
                product_name = row[1] if len(row) > 1 else ""  # Column B
                status2 = row[10] if len(row) > 10 else ""  # Column K (Status2)
                
                if product_name and status2 != 'ACTIVE':
                    product_groups[product_name].append((row_idx, row))
                    non_active_count += 1
        
        print(f"📊 Found {non_active_count} non-ACTIVE rows across {len(product_groups)} products")
        
        if not product_groups:
            print("✅ No non-ACTIVE rows found - all campaigns are already active!")
            return {}
        
        # Process each product group
        generated_creatives = {}
        
        for product_name, rows in product_groups.items():
            print(f"\n🎯 Processing product: {product_name} ({len(rows)} non-ACTIVE rows)")
            
            # Get existing pin data from first row for this product
            first_row = rows[0][1]  # Get the row data
            existing_pin_data = {
                'pin_title': first_row[2] if len(first_row) > 2 else "",  # Column C
                'pin_description': first_row[3] if len(first_row) > 3 else "",  # Column D
                'board_title': first_row[4] if len(first_row) > 4 else "",  # Column E
            }
            
            print(f"   📝 Using existing pin data: {existing_pin_data}")
            
            # Find product images from main sheet for this product
            product_images = []
            for row_idx, row in sheet_data:
                if len(row) > 1 and row[1] == product_name:  # Same product name
                    # Look for image URLs in columns (assuming images are in later columns)
                    for col_idx in range(5, min(len(row), 15)):  # Check columns F-O
                        if row[col_idx] and (row[col_idx].startswith('http') or row[col_idx].endswith(('.jpg', '.jpeg', '.png', '.gif'))):
                            product_images.append(row[col_idx])
            
            print(f"   📸 Found {len(product_images)} images for {product_name}")
            
            if len(product_images) < 2:
                print(f"   ⚠️ Not enough images for {product_name} (need at least 2, found {len(product_images)})")
                continue
            
            # Generate 4 creative types
            product_creatives = {}
            
            # 1. Slideshow Video
            slideshow_path = os.path.join(output_dir, f"{product_name}_slideshow.mp4")
            slideshow_result = generate_slideshow_video_creative(product_images, music_folder_path, slideshow_path)
            if slideshow_result:
                product_creatives['slideshow'] = slideshow_path
                print(f"   ✅ Generated slideshow video: {slideshow_path}")
            
            # 2. Quadrant Creative
            quadrant_path = os.path.join(output_dir, f"{product_name}_quadrant.jpg")
            quadrant_result = generate_quad_image_creative(product_images, quadrant_path)
            if quadrant_result:
                product_creatives['quadrant'] = quadrant_path
                print(f"   ✅ Generated quadrant creative: {quadrant_path}")
            
            # 3. Showcase Creative
            showcase_path = os.path.join(output_dir, f"{product_name}_showcase.jpg")
            showcase_result = generate_enhanced_showcase_creative(product_images, showcase_path)
            if showcase_result:
                product_creatives['showcase'] = showcase_path
                print(f"   ✅ Generated showcase creative: {showcase_path}")
            
            # 4. Carousel Creative
            carousel_path = os.path.join(output_dir, f"{product_name}_carousel.jpg")
            carousel_result = generate_carousel_style_creative(product_images, carousel_path)
            if carousel_result:
                product_creatives['carousel'] = carousel_path
                print(f"   ✅ Generated carousel creative: {carousel_path}")
            
            if product_creatives:
                generated_creatives[product_name] = {
                    'creatives': product_creatives,
                    'pin_data': existing_pin_data,
                    'rows': rows
                }
                print(f"   🎉 Generated {len(product_creatives)} creatives for {product_name}")
            else:
                print(f"   ❌ Failed to generate any creatives for {product_name}")
        
        print(f"\n🎨 Extra creative generation completed!")
        print(f"📊 Generated creatives for {len(generated_creatives)} products")
        
        return generated_creatives
        
    except Exception as e:
        print(f"❌ Error in generate_extra_creatives_for_non_active_rows: {e}")
        return {}

def add_creative_rows_to_sheet(sheet, generated_creatives):
    """
    Add new rows to the sheet for generated creatives
    """
    try:
        print(f"📝 Adding creative rows to sheet...")
        
        # Get current sheet data
        headers, data_rows = get_sheet_data(sheet)
        print(f"📊 Current sheet has {len(data_rows)} rows")
        
        # Prepare new rows
        new_rows = []
        
        for product_name, product_data in generated_creatives.items():
            creatives = product_data['creatives']
            pin_data = product_data['pin_data']
            existing_rows = product_data['rows']
            
            print(f"   📝 Adding {len(creatives)} creative rows for {product_name}")
            
            # Find the last row for this product to insert after it
            last_row_idx = max([row_idx for row_idx, _ in existing_rows])
            
            for creative_type, creative_path in creatives.items():
                # Create new row data
                new_row = [''] * len(headers)  # Initialize with empty values
                
                # Fill in the data
                new_row[0] = ''  # Column A - Auto-generated
                new_row[1] = product_name  # Column B - Product Name
                new_row[2] = pin_data['pin_title']  # Column C - Pin Title
                new_row[3] = pin_data['pin_description']  # Column D - Pin Description
                new_row[4] = pin_data['board_title']  # Column E - Board Title
                new_row[5] = creative_path  # Column F - Creative Path
                new_row[6] = creative_type  # Column G - Creative Type
                new_row[7] = 'READY'  # Column H - Status
                new_row[8] = ''  # Column I - Pin ID (will be filled after posting)
                new_row[9] = ''  # Column J - Ad Campaign Status
                new_row[10] = 'PENDING'  # Column K - Status2
                new_row[11] = ''  # Column L - Ad Campaign ID
                new_row[12] = ''  # Column M - Advertised At
                
                new_rows.append({
                    'row_index': last_row_idx + 1,
                    'data': new_row
                })
                
                print(f"     ✅ Prepared {creative_type} creative row for {product_name}")
        
        # Add rows to sheet
        if new_rows:
            print(f"📝 Adding {len(new_rows)} new rows to sheet...")
            
            # Sort by row index to insert in correct order
            new_rows.sort(key=lambda x: x['row_index'])
            
            for row_data in new_rows:
                try:
                    # Insert row at the specified index
                    sheet.insert_row(row_data['data'], row_data['row_index'] + 1)  # +1 because sheets are 1-indexed
                    print(f"   ✅ Added row at index {row_data['row_index']}")
                except Exception as e:
                    print(f"   ❌ Failed to add row at index {row_data['row_index']}: {e}")
            
            print(f"🎉 Successfully added {len(new_rows)} creative rows to sheet!")
        else:
            print("ℹ️ No new rows to add")
            
    except Exception as e:
        print(f"❌ Error adding creative rows to sheet: {e}")

if __name__ == "__main__":
    run()

