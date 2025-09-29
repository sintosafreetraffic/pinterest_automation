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
    from a import create_campaign, create_ad_group, create_ad
    CAMPAIGN_FUNCTIONS_AVAILABLE = True
    logger.info("✅ Campaign creation functions loaded")
except ImportError as e:
    logger.warning(f"⚠️ Could not load campaign functions: {e}")
    create_campaign = None
    create_ad_group = None
    create_ad = None
    CAMPAIGN_FUNCTIONS_AVAILABLE = False

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
                pin_id = post_pin(
                    access_token, 
                    board_id, 
                    image_url, 
                    title, 
                    description, 
                    product_url
                )
                
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
    
    try:
        # Step 1: Post pins for empty rows
        logger.info("📌 Step 1: Posting pins for empty rows...")
        pin_success = post_pins_to_sheet1(max_pins=20, delay_between_posts=60)  # Conservative settings
        
        if pin_success:
            logger.info("✅ Step 1 completed: Pins posted successfully")
        else:
            logger.info("⚠️ Step 1: Pin posting had issues (rate limiting expected)")
        
        # Step 2: Create campaigns for posted pins (always run, even if pin posting was rate limited)
        logger.info("🎯 Step 2: Creating campaigns for posted pins...")
        campaign_success = create_campaigns_for_sheet1()
        
        if campaign_success:
            logger.info("✅ Step 2 completed: Campaigns prepared successfully")
        else:
            logger.info("⚠️ Step 2: Campaign creation had issues")
        
        logger.info("🎉 Sheet1 Enhanced Scheduler completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
