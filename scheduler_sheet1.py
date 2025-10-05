#!/usr/bin/env python3
"""
Enhanced Scheduler for Sheet1 (1000+ rows)
Handles pin posting and campaign creation for all rows in Sheet1
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add the project directory to the path
sys.path.append('/Users/saschavanwell/Documents/shopify-pinterest-automation')

from forefront import google_sheets_client, SHEET_ID
from pinterest_post import get_or_create_board, post_pin
from pinterest_auth import get_access_token, get_ad_account_id

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler_sheet1.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import campaign creation functions
try:
    from a import create_campaign, create_ad_group, create_ad, generate_pin_title, generate_pin_description, move_processed_products_to_generated_collection
    CAMPAIGN_FUNCTIONS_AVAILABLE = True
    logger.info("✅ Campaign creation functions loaded")
except ImportError as e:
    logger.warning(f"⚠️ Could not load campaign functions: {e}")
    create_campaign = None
    create_ad_group = None
    create_ad = None
    generate_pin_title = None
    generate_pin_description = None
    move_processed_products_to_generated_collection = None
    CAMPAIGN_FUNCTIONS_AVAILABLE = False

# Import board title generation functions
try:
    from forefront import generate_board_title_for_collection
    BOARD_TITLE_FUNCTIONS_AVAILABLE = True
    logger.info("✅ Board title generation functions loaded")
except ImportError as e:
    logger.warning(f"⚠️ Could not load board title functions: {e}")
    generate_board_title_for_collection = None
    BOARD_TITLE_FUNCTIONS_AVAILABLE = False

# Enhanced Pinterest integration imports
try:
    import sys
    meta_change_path = '/Users/saschavanwell/Documents/meta-change'
    sys.path.append(meta_change_path)
    
    from pin_generation_enhancement import PinGenerationEnhancement
    ENHANCED_FEATURES_AVAILABLE = True
    logger.info("✅ Enhanced Pinterest integration modules loaded")
except ImportError as e:
    logger.warning(f"⚠️ Could not load enhanced integration modules: {e}")
    PinGenerationEnhancement = None
    ENHANCED_FEATURES_AVAILABLE = False

def update_sheet1_row(sheet, row_num, updates):
    """Update specific row in Sheet1"""
    try:
        # Update Status column (column 12, index 11) - MAIN STATUS
        if 'status' in updates:
            sheet.update_cell(row_num, 12, updates['status'])
        
        # Update Board ID column (column 13, index 12)
        if 'board_id' in updates:
            sheet.update_cell(row_num, 13, updates['board_id'])
        
        # Update Pin ID column (column 14, index 13)
        if 'pin_id' in updates:
            sheet.update_cell(row_num, 14, updates['pin_id'])
        
        # Update Status2 column (column 15, index 14) - Use 'ACTIVE' instead of 'READY'
        if 'campaign_status' in updates:
            status_value = 'ACTIVE' if updates['campaign_status'] == 'ACTIVE' else updates['campaign_status']
            sheet.update_cell(row_num, 15, status_value)
        
        # Update "Ad Campaign Status" column (column 16, index 15) with campaign ID only
        if 'campaign_id' in updates:
            campaign_id = updates['campaign_id']
            sheet.update_cell(row_num, 16, campaign_id)
        
        # Update "Advertised At" column (column 17, index 16) with date only
        if 'campaign_id' in updates:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            sheet.update_cell(row_num, 17, today)
        
        # Update Ad ID column (column 18, index 17) - if it exists
        if 'ad_id' in updates:
            try:
                sheet.update_cell(row_num, 18, updates['ad_id'])
            except:
                pass  # Column might not exist
        
        return True
    except Exception as e:
        logger.error(f"Failed to update row {row_num}: {e}")
        return False

def cleanup_duplicate_products():
    """Remove products from NEEDS TO BE DONE collection if they're already in READY FOR PINTEREST collection"""
    try:
        logger.info("🧹 Starting Duplicate Product Cleanup")
        logger.info("   🔍 Removing products from NEEDS TO BE DONE (644626448708) if they're already in READY FOR PINTEREST (644749033796)")
        
        # Import collection management functions
        from forefront import get_collection_products, remove_product_from_collection
        
        # Get products from both collections
        needs_to_be_done_products = get_collection_products(644626448708)
        ready_for_pinterest_products = get_collection_products(644749033796)
        
        logger.info(f"📊 NEEDS TO BE DONE collection: {len(needs_to_be_done_products)} products")
        logger.info(f"📊 READY FOR PINTEREST collection: {len(ready_for_pinterest_products)} products")
        
        # Create a set of product IDs in READY FOR PINTEREST for fast lookup
        ready_product_ids = {product['id'] for product in ready_for_pinterest_products}
        
        # Find duplicates
        duplicates_to_remove = []
        for product in needs_to_be_done_products:
            if product['id'] in ready_product_ids:
                duplicates_to_remove.append(product)
        
        logger.info(f"🔍 Found {len(duplicates_to_remove)} duplicate products to remove from NEEDS TO BE DONE")
        
        if not duplicates_to_remove:
            logger.info("✅ No duplicate products found - cleanup not needed")
            return True
        
        # Remove duplicates from NEEDS TO BE DONE collection
        removed_count = 0
        for product in duplicates_to_remove:
            try:
                success = remove_product_from_collection(644626448708, product['id'])
                if success:
                    removed_count += 1
                    logger.info(f"✅ Removed duplicate: {product['title'][:50]}... (ID: {product['id']})")
                else:
                    logger.warning(f"⚠️ Failed to remove: {product['title'][:50]}... (ID: {product['id']})")
            except Exception as e:
                logger.error(f"❌ Error removing product {product['id']}: {e}")
                continue
        
        logger.info(f"🎯 Duplicate cleanup completed:")
        logger.info(f"   ✅ Removed: {removed_count} duplicate products")
        logger.info(f"   📊 Remaining in NEEDS TO BE DONE: {len(needs_to_be_done_products) - removed_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in duplicate cleanup: {e}")
        return False

def generate_content_and_move_products():
    """Generate 10 pins per product from READY FOR PINTEREST collection and move to GENERATED"""
    try:
        logger.info("🎯 Starting Content Generation and Collection Movement")
        logger.info("   🔍 This will generate 10 pins per product from READY FOR PINTEREST collection")
        logger.info("   📝 Add new rows to Google Sheet with generated content")
        logger.info("   📋 Then move products from READY FOR PINTEREST to GENERATED collection")
        
        # Import collection management functions
        from forefront import get_collection_products, remove_product_from_collection
        from a import add_product_to_collection
        
        # Get products from READY FOR PINTEREST collection
        ready_products = get_collection_products(644749033796)  # READY FOR PINTEREST collection ID
        logger.info(f"📊 Found {len(ready_products)} products in READY FOR PINTEREST collection")
        
        if not ready_products:
            logger.info("✅ No products in READY FOR PINTEREST collection - nothing to process")
            return True
        
        # Connect to Sheet1
        workbook = google_sheets_client.open_by_key(SHEET_ID)
        sheet1 = workbook.worksheet('Sheet1')
        
        # Get current data to find column indices
        data = sheet1.get_all_values()
        headers = data[0] if data else []
        
        # Find column indices
        product_name_idx = None
        product_url_idx = None
        pin_title_idx = None
        pin_description_idx = None
        board_title_idx = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'product name' in header_lower:
                product_name_idx = i
            elif 'product url' in header_lower:
                product_url_idx = i
            elif 'generated pin title' in header_lower:
                pin_title_idx = i
            elif 'generated pin description' in header_lower:
                pin_description_idx = i
            elif 'board title' in header_lower:
                board_title_idx = i
        
        if product_name_idx is None:
            logger.error("❌ Could not find 'Product Name' column")
            return False
        
        # Process each product in READY FOR PINTEREST collection
        total_pins_generated = 0
        products_processed = 0
        
        for product in ready_products:
            try:
                product_name = product.get('title', 'Unknown Product')
                product_id = product.get('id')
                product_url = f"https://92c6ce-58.myshopify.com/products/{product.get('handle', '')}"
                
                logger.info(f"📌 Processing product: {product_name}")
                logger.info(f"   🆔 Product ID: {product_id}")
                logger.info(f"   🔗 Product URL: {product_url}")
                
                # Generate 10 pins for this product
                pins_generated = 0
                for pin_num in range(1, 11):  # Generate 10 pins
                    try:
                        # Generate content for this pin
                        pin_title = ""
                        pin_description = ""
                        board_title = ""
                        
                        # Generate pin title
                        if generate_pin_title:
                            try:
                                pin_title = generate_pin_title(product_name, {}, target_language="de")
                                if not pin_title:
                                    pin_title = f"{product_name} - Pin {pin_num} - Jetzt entdecken!"
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to generate pin title for {product_name} Pin {pin_num}: {e}")
                                pin_title = f"{product_name} - Pin {pin_num} - Jetzt entdecken!"
                        else:
                            pin_title = f"{product_name} - Pin {pin_num} - Jetzt entdecken!"
                        
                        # Generate pin description
                        if generate_pin_description:
                            try:
                                pin_description = generate_pin_description(product_name, {}, target_language="de")
                                if not pin_description:
                                    pin_description = f"Entdecke {product_name} - Perfekt für deinen Style! Pin {pin_num}"
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to generate pin description for {product_name} Pin {pin_num}: {e}")
                                pin_description = f"Entdecke {product_name} - Perfekt für deinen Style! Pin {pin_num}"
                        else:
                            pin_description = f"Entdecke {product_name} - Perfekt für deinen Style! Pin {pin_num}"
                        
                        # Generate board title
                        if generate_board_title_for_collection:
                            try:
                                board_titles_cache = {}
                                board_title = generate_board_title_for_collection(product_name, board_titles_cache)
                                if not board_title:
                                    board_title = f"{product_name} Inspirationen"
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to generate board title for {product_name} Pin {pin_num}: {e}")
                                board_title = f"{product_name} Inspirationen"
                        else:
                            board_title = f"{product_name} Inspirationen"
                        
                        # Create new row in Google Sheet
                        new_row = [''] * len(headers)  # Initialize with empty values
                        
                        # Set the values in appropriate columns
                        if product_url_idx is not None:
                            new_row[product_url_idx] = product_url
                        if product_name_idx is not None:
                            new_row[product_name_idx] = product_name
                        if pin_title_idx is not None:
                            new_row[pin_title_idx] = pin_title
                        if pin_description_idx is not None:
                            new_row[pin_description_idx] = pin_description
                        if board_title_idx is not None:
                            new_row[board_title_idx] = board_title
                        
                        # Add row to sheet
                        try:
                            sheet1.append_row(new_row)
                            pins_generated += 1
                            total_pins_generated += 1
                            
                            logger.info(f"✅ Generated Pin {pin_num} for {product_name[:30]}...")
                        except Exception as sheet_error:
                            # Check if this is a Google Sheets rate limit error
                            error_str = str(sheet_error).lower()
                            if any(keyword in error_str for keyword in ['quota exceeded', 'rate limit', '429', 'resource_exhausted']):
                                logger.warning(f"⚠️ Google Sheets rate limit detected: {sheet_error}")
                                logger.info("🔄 Moving to next product due to rate limits")
                                break  # Break out of pin generation for this product
                            else:
                                logger.error(f"❌ Error adding row to sheet: {sheet_error}")
                                continue
                        
                    except Exception as e:
                        logger.error(f"❌ Error generating pin {pin_num} for {product_name}: {e}")
                        continue
                
                logger.info(f"✅ Generated {pins_generated} pins for {product_name}")
                
                # Move product from READY FOR PINTEREST to GENERATED collection
                try:
                    # Remove from READY FOR PINTEREST
                    remove_success = remove_product_from_collection(644749033796, product_id)
                    if remove_success:
                        # Add to GENERATED collection
                        add_success = add_product_to_collection(product_id, 651569889604)  # GENERATED collection ID
                        if add_success:
                            products_processed += 1
                            logger.info(f"✅ Moved {product_name} from READY FOR PINTEREST to GENERATED collection")
                        else:
                            logger.warning(f"⚠️ Failed to add {product_name} to GENERATED collection")
                    else:
                        logger.warning(f"⚠️ Failed to remove {product_name} from READY FOR PINTEREST collection")
                except Exception as e:
                    logger.error(f"❌ Error moving product {product_name}: {e}")
                    continue
                
            except Exception as e:
                logger.error(f"❌ Error processing product {product.get('title', 'Unknown')}: {e}")
                continue
        
        logger.info(f"🎯 Content generation and collection movement completed:")
        logger.info(f"   📌 Total pins generated: {total_pins_generated}")
        logger.info(f"   📦 Products processed: {products_processed}")
        logger.info(f"   📊 Pins per product: 10")
        
        # Return status that indicates if rate limits were hit
        if total_pins_generated == 0 and products_processed > 0:
            return "RATE_LIMITED"  # Indicate rate limits were hit
        else:
            return True
        
    except Exception as e:
        logger.error(f"❌ Error in content generation and collection movement: {e}")
        import traceback
        traceback.print_exc()
        return False

def post_pins_to_sheet1(max_pins=50, delay_between_posts=30):
    """Post pins for empty rows in Sheet1 with enhanced Pinterest trends and customer persona"""
    try:
        logger.info("🚀 Starting Sheet1 Enhanced Pin Posting with Pinterest Trends and Customer Persona")
        
        # Initialize enhanced features
        enhanced_pin_generation = None
        if ENHANCED_FEATURES_AVAILABLE and PinGenerationEnhancement:
            try:
                enhanced_pin_generation = PinGenerationEnhancement()
                logger.info("✅ Enhanced pin generation initialized with Pinterest trends and customer persona")
            except Exception as e:
                logger.warning(f"⚠️ Error initializing enhanced pin generation: {e}")
                enhanced_pin_generation = None
        
        # Connect to Sheet1
        workbook = google_sheets_client.open_by_key(SHEET_ID)
        sheet1 = workbook.worksheet('Sheet1')
        
        # Get Pinterest access token
        access_token = get_access_token()
        logger.info("✅ Pinterest authentication successful")
        
        # Get all data
        data = sheet1.get_all_values()
        logger.info(f"📊 Loaded {len(data)} rows from Sheet1")
        
        # Find empty rows
        empty_rows = []
        for i, row in enumerate(data[1:], 2):  # Skip header
            if len(row) > 11:
                status = row[11] if row[11] else 'EMPTY'  # Status column (column 12, index 11)
                if status == 'EMPTY' or status == '':
                    empty_rows.append((i, row))
        
        logger.info(f"📌 Found {len(empty_rows)} empty rows")
        
        if not empty_rows:
            logger.info("✅ No empty rows found - all pins already posted")
            return True
        
        # Process pins with rate limiting
        posted_count = 0
        failed_count = 0
        
        for i, (row_num, row) in enumerate(empty_rows[:max_pins]):
            try:
                logger.info(f"📌 Processing row {row_num} ({i+1}/{min(max_pins, len(empty_rows))})")
                
                # Extract data
                image_url = row[0] if len(row) > 0 else ''
                product_name = row[1] if len(row) > 1 else 'Unknown'
                product_url = row[2] if len(row) > 2 else ''
                
                # Use enhanced pin generation if available
                if enhanced_pin_generation:
                    try:
                        logger.info(f"🎯 Generating enhanced pin content with Pinterest trends and customer persona...")
                        
                        # Generate enhanced title and description with trending keywords
                        enhanced_title = enhanced_pin_generation.generate_enhanced_pin_title(
                            row, use_trending_keywords=True, region="DE"
                        )
                        enhanced_description = enhanced_pin_generation.generate_enhanced_pin_description(
                            row, use_trending_keywords=True, region="DE"
                        )
                        
                        title = enhanced_title
                        description = enhanced_description
                        
                        logger.info(f"✅ Enhanced content generated with trending keywords")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Enhanced generation failed, using fallback: {e}")
                        title = row[8] if len(row) > 8 else f"{product_name} - Jetzt entdecken!"
                        description = row[9] if len(row) > 9 else f"Entdecke {product_name} - Perfekt für deinen Style!"
                else:
                    # Fallback to original logic
                    title = row[8] if len(row) > 8 else f"{product_name} - Jetzt entdecken!"
                    description = row[9] if len(row) > 9 else f"Entdecke {product_name} - Perfekt für deinen Style!"
                
                board_title = row[10] if len(row) > 10 else 'Outfit Inspirationen'
                
                logger.info(f"   Product: {product_name[:50]}...")
                logger.info(f"   Board: {board_title}")
                
                # Get or create board
                board_id = get_or_create_board(access_token, board_title)
                logger.info(f"   Board ID: {board_id}")
                
                # Post pin
                try:
                    pin_id = post_pin(
                        access_token, 
                        board_id, 
                        image_url, 
                        title, 
                        description, 
                        product_url
                    )
                except Exception as e:
                    # Check if this is a rate limit error
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ['rate limit', 'quota exceeded', 'too many requests', '429']):
                        logger.warning(f"⚠️ Rate limit detected: {e}")
                        logger.info("🔄 Moving to campaign creation for already posted pins")
                        break
                    else:
                        logger.error(f"❌ Unexpected error posting pin: {e}")
                        pin_id = None
                
                if pin_id:
                    # Check if rate limited
                    if 'RATE_LIMITED' in str(pin_id):
                        logger.warning("⚠️ Rate limit detected - skipping remaining pins")
                        logger.info("🔄 Moving to campaign creation for already posted pins")
                        break
                    
                    logger.info(f"✅ Posted pin: {pin_id}")
                    
                    # Update sheet
                    update_success = update_sheet1_row(sheet1, row_num, {
                        'status': 'POSTED',
                        'board_id': board_id,
                        'pin_id': pin_id
                    })
                    
                    if update_success:
                        posted_count += 1
                        logger.info(f"✅ Updated row {row_num} with pin data")
                    else:
                        logger.warning(f"⚠️ Failed to update row {row_num}")
                else:
                    logger.warning(f"⚠️ Failed to post pin for row {row_num}")
                    failed_count += 1
                    
                    # Check if this is a rate limit error and break out
                    if failed_count >= 3:  # If we've failed 3 times in a row, likely rate limited
                        logger.warning("⚠️ Multiple consecutive failures detected - likely rate limited")
                        logger.info("🔄 Moving to campaign creation for already posted pins")
                        break
                
                # Rate limiting delay
                if i < len(empty_rows) - 1:  # Don't delay after last pin
                    logger.info(f"⏳ Waiting {delay_between_posts}s before next pin...")
                    time.sleep(delay_between_posts)
                
            except Exception as e:
                logger.error(f"❌ Error processing row {row_num}: {e}")
                failed_count += 1
                continue
        
        logger.info(f"🎯 Pin posting completed:")
        logger.info(f"   ✅ Posted: {posted_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        logger.info(f"   📊 Total processed: {posted_count + failed_count}")
        
        return posted_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error in pin posting: {e}")
        return False

def create_campaigns_for_sheet1():
    """Create campaigns for posted pins in Sheet1"""
    try:
        logger.info("🎯 Starting Sheet1 Campaign Creation")
        
        # Connect to Sheet1
        workbook = google_sheets_client.open_by_key(SHEET_ID)
        sheet1 = workbook.worksheet('Sheet1')
        
        # Get Pinterest access token
        access_token = get_access_token()
        
        # Get all data
        data = sheet1.get_all_values()
        
        # Find posted rows without campaigns
        eligible_rows = []
        for i, row in enumerate(data[1:], 2):
            if len(row) > 15:
                status = row[11] if row[11] else ''  # Status column (column 12, index 11)
                campaign_status = row[14] if len(row) > 14 and row[14] else ''  # Status2 column (moved one left)
                
                if status == 'POSTED' and (not campaign_status or campaign_status == ''):
                    eligible_rows.append((i, row))
        
        # Also find ALL pins of products that have some pins in campaigns but not all
        # This ensures we don't miss any pins of the same product
        product_campaign_status = {}
        for i, row in enumerate(data[1:], 2):
            if len(row) > 15:
                product_name = row[1] if len(row) > 1 else ''
                status = row[11] if row[11] else ''
                campaign_status = row[14] if len(row) > 14 and row[14] else ''
                pin_id = row[13] if len(row) > 13 else ''
                
                if status == 'POSTED' and pin_id and product_name:
                    if product_name not in product_campaign_status:
                        product_campaign_status[product_name] = {'total': 0, 'with_campaigns': 0, 'rows': []}
                    
                    product_campaign_status[product_name]['total'] += 1
                    product_campaign_status[product_name]['rows'].append((i, row))
                    
                    if campaign_status == 'ACTIVE':
                        product_campaign_status[product_name]['with_campaigns'] += 1
        
        # Add missing pins from products that have partial campaign coverage
        for product_name, stats in product_campaign_status.items():
            if stats['with_campaigns'] > 0 and stats['with_campaigns'] < stats['total']:
                logger.info(f"🔍 Found product with partial campaign coverage: {product_name}")
                logger.info(f"   📊 Total pins: {stats['total']}, With campaigns: {stats['with_campaigns']}")
                
                # Add all pins from this product that don't have campaigns
                for row_num, row in stats['rows']:
                    campaign_status = row[14] if len(row) > 14 and row[14] else ''
                    if campaign_status != 'ACTIVE':
                        # Check if already in eligible_rows
                        already_eligible = any(r[0] == row_num for r in eligible_rows)
                        if not already_eligible:
                            eligible_rows.append((row_num, row))
                            logger.info(f"   ➕ Added missing pin: Row {row_num}, Pin {row[13] if len(row) > 13 else 'N/A'}")
        
        logger.info(f"📊 Found {len(eligible_rows)} eligible rows for campaigns (including missing pins from partial products)")
        
        if not eligible_rows:
            logger.info("✅ No eligible rows found for campaigns")
            return True
        
        # Actually create campaigns if functions are available
        if CAMPAIGN_FUNCTIONS_AVAILABLE and create_campaign and create_ad_group:
            logger.info("🎯 Creating multi-product Pinterest campaigns with actual ads...")
            
            # Get ad account ID
            ad_account_id = get_ad_account_id(access_token)
            if not ad_account_id:
                logger.error("❌ Failed to get ad account ID")
                return False
            
            logger.info(f"✅ Using Ad Account ID: {ad_account_id}")
            
            # Group by product name to get ALL pins for each product
            product_pins = {}
            for row_num, row in eligible_rows:
                if len(row) > 1:
                    product_name = row[1]  # Product name
                    pin_id = row[13] if len(row) > 13 and row[13] else ''
                    
                    if pin_id:  # Only include rows with valid pin IDs
                        if product_name not in product_pins:
                            product_pins[product_name] = []
                        product_pins[product_name].append((row_num, row, pin_id))
            
            logger.info(f"📊 Found {len(product_pins)} unique products with pins")
            
            # Group products into campaigns targeting 40-50 pins per campaign (if needed)
            target_pins_per_campaign = 45  # Target 40-50 pins per campaign
            product_list = list(product_pins.items())
            campaign_groups = []
            
            current_group = []
            current_pin_count = 0
            
            for product_name, pin_list in product_list:
                # Add this product to current group
                current_group.append((product_name, pin_list))
                current_pin_count += len(pin_list)
                
                # If we've reached target pins, create campaign group
                if current_pin_count >= target_pins_per_campaign:
                    campaign_groups.append(current_group)
                    current_group = []
                    current_pin_count = 0
            
            # Add remaining products as final campaign (even if less than target)
            if current_group:
                campaign_groups.append(current_group)
            
            logger.info(f"📊 Creating {len(campaign_groups)} campaigns targeting {target_pins_per_campaign} pins each")
            
            created_campaigns = 0
            total_ads_created = 0
            
            for group_idx, group in enumerate(campaign_groups):
                try:
                    # Create one campaign for this group of products
                    campaign_name = f"Sheet1_Multi_Product_Campaign_{group_idx + 1}"
                    total_pins_in_group = sum(len(pin_list) for _, pin_list in group)
                    unique_products = len(group)
                    
                    # Dynamic budget allocation based on number of unique products
                    if unique_products >= 15:
                        daily_budget = 2000  # €20.00 for 15+ unique products
                        budget_reason = f"15+ products ({unique_products})"
                    else:
                        daily_budget = 1000  # €10.00 for 10-14 unique products
                        budget_reason = f"10-14 products ({unique_products})"
                    
                    logger.info(f"🎯 Creating campaign: {campaign_name} with {unique_products} unique products and {total_pins_in_group} total pins")
                    logger.info(f"💰 Budget: €{daily_budget/100:.2f} ({budget_reason})")
                    
                    campaign_id = create_campaign(
                        access_token=access_token,
                        ad_account_id=ad_account_id,
                        campaign_name=campaign_name,
                        daily_budget=daily_budget
                    )
                    
                    if campaign_id:
                        logger.info(f"✅ Campaign created: {campaign_id}")
                        created_campaigns += 1
                        
                        # Create ad group for this campaign
                        ad_group_id = create_ad_group(
                            access_token=access_token,
                            ad_account_id=ad_account_id,
                            campaign_id=campaign_id,
                            product_name=f"Multi-Product Group {group_idx + 1}"
                        )
                        
                        if ad_group_id:
                            logger.info(f"✅ Ad group created: {ad_group_id}")
                            
                            # Create ads for ALL pins of each product in this campaign
                            ads_created_in_group = 0
                            for product_name, pin_list in group:
                                logger.info(f"📌 Processing product: {product_name} with {len(pin_list)} pins")
                                
                                for pin_idx, (row_num, row, pin_id) in enumerate(pin_list):
                                    try:
                                        # Create ad (this links the pin to the campaign)
                                        ad_name = f"{product_name[:25]}_Pin{pin_idx+1}_Ad"
                                        ad_id = create_ad(
                                            access_token=access_token,
                                            ad_account_id=ad_account_id,
                                            ad_group_id=ad_group_id,
                                            pin_id=pin_id,
                                            ad_name=ad_name
                                        )
                                        
                                        if ad_id:
                                            # Update sheet with campaign data
                                            update_sheet1_row(sheet1, row_num, {
                                                'campaign_status': 'ACTIVE',
                                                'campaign_id': campaign_id,
                                                'ad_id': ad_id
                                            })
                                            ads_created_in_group += 1
                                            total_ads_created += 1
                                            logger.info(f"✅ Created ad for {product_name} Pin {pin_idx+1}: Ad {ad_id} (Pin: {pin_id})")
                                        else:
                                            logger.warning(f"⚠️ Failed to create ad for {product_name} Pin {pin_idx+1}")
                                            
                                    except Exception as e:
                                        logger.error(f"❌ Error creating ad for {product_name} Pin {pin_idx+1}: {e}")
                                        continue
                            
                            logger.info(f"✅ Campaign {campaign_id}: {ads_created_in_group} ads created")
                        else:
                            logger.warning(f"⚠️ Failed to create ad group for campaign {campaign_id}")
                    else:
                        logger.warning(f"⚠️ Failed to create campaign for group {group_idx + 1}")
                        
                except Exception as e:
                    logger.error(f"❌ Error creating campaign group {group_idx + 1}: {e}")
                    continue
            
            logger.info(f"🎯 Multi-product campaign creation completed:")
            logger.info(f"   📊 Campaigns created: {created_campaigns}")
            logger.info(f"   📌 Ads created: {total_ads_created}")
            logger.info(f"   💰 Dynamic budget: €10.00 (10-14 products) | €20.00 (15+ products)")
        else:
            # Fallback: just mark as ready for campaigns
            logger.info("⚠️ Campaign functions not available, marking as ready...")
            for row_num, row in eligible_rows[:10]:  # Process first 10
                update_sheet1_row(sheet1, row_num, {
                    'campaign_status': 'READY'
                })
                logger.info(f"✅ Marked row {row_num} as ready for campaigns")
            
            logger.info(f"🎯 Campaign preparation completed for {min(10, len(eligible_rows))} rows")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in campaign creation: {e}")
        return False

def main():
    """Main scheduler function for Sheet1"""
    logger.info("🚀 Starting Sheet1 Enhanced Scheduler")
    logger.info(f"⏰ Started at: {datetime.now()}")
    
    # Check if today is Sunday (campaign creation day)
    today = datetime.now()
    is_sunday = today.weekday() == 6  # Monday is 0, Sunday is 6
    logger.info(f"📅 Today is {today.strftime('%A')} - Campaign creation {'enabled' if is_sunday else 'disabled'}")
    
    try:
        # Step 0: Clean up duplicate products (runs twice daily)
        logger.info("🧹 Step 0: Cleaning up duplicate products from NEEDS TO BE DONE collection...")
        cleanup_success = cleanup_duplicate_products()
        
        if cleanup_success:
            logger.info("✅ Step 0 completed: Duplicate cleanup successful")
        else:
            logger.info("⚠️ Step 0: Duplicate cleanup had issues")
        
        # Step 1: Generate content and move products (runs twice daily)
        logger.info("📝 Step 1: Generating pin titles, descriptions, board titles and moving products...")
        content_success = generate_content_and_move_products()
        
        if content_success:
            logger.info("✅ Step 1 completed: Content generation and collection movement successful")
        else:
            logger.info("⚠️ Step 1: Content generation had issues")
        
        # Step 2: Post pins for empty rows (runs twice daily)
        logger.info("📌 Step 2: Posting pins for empty rows...")
        # Check if we hit rate limits during content generation
        if content_success == "RATE_LIMITED":
            logger.info("⚠️ Rate limits detected in Step 1 - skipping pin posting to avoid further rate limits")
            logger.info("🔄 Moving directly to campaign creation")
            pin_success = False  # Skip pin posting
        else:
            pin_success = post_pins_to_sheet1(max_pins=20, delay_between_posts=60)  # Conservative settings
        
        if pin_success:
            logger.info("✅ Step 2 completed: Pins posted successfully")
        else:
            logger.info("⚠️ Step 2: Pin posting had issues (rate limiting expected)")
        
        # Step 3: Create campaigns for posted pins (only on Sundays)
        if is_sunday:
            logger.info("🎯 Step 3: Creating campaigns for posted pins (Sunday campaign creation)...")
            campaign_success = create_campaigns_for_sheet1()
            
            if campaign_success:
                logger.info("✅ Step 3 completed: Campaigns created successfully")
            else:
                logger.info("⚠️ Step 3: Campaign creation had issues")
        else:
            logger.info("⏭️ Step 3: Skipped campaign creation (not Sunday)")
            logger.info("📅 Campaign creation is scheduled for Sundays only")
        
        logger.info("🎉 Sheet1 Enhanced Scheduler completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
