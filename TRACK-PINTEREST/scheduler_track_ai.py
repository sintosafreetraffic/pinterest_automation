"""
Enhanced Pinterest Scheduler with Track AI Integration
======================================================

This scheduler extends the original Pinterest automation with Track AI pixel
integration for comprehensive conversion tracking and cross-platform attribution.

Features:
- Track AI pixel integration for all Pinterest campaigns
- UTM parameter generation for campaign tracking
- Enhanced conversion tracking
- Cross-platform attribution analysis
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import original modules
from pinterest_auth import get_access_token, get_ad_account_id
from pinterest_post_enhanced import post_pin_with_track_ai, post_pin_batch_with_track_ai, validate_track_ai_integration
from track_ai_integration import PinterestTrackAIIntegration, generate_pinterest_track_ai_url

# Import Google Sheets functionality
try:
    from forefront import google_sheets_client, SHEET_ID
except ImportError:
    print("❌ Could not import Google Sheets client")
    sys.exit(1)

# Import campaign creation functions
try:
    from a import create_campaign, create_ad_group, create_ad
except ImportError:
    print("❌ Could not import campaign creation functions")
    sys.exit(1)

# Enhanced Pinterest integration imports
try:
    import sys
    meta_change_path = '/Users/saschavanwell/Documents/meta-change'
    sys.path.append(meta_change_path)
    from pin_generation_enhancement import PinGenerationEnhancement
    ENHANCED_FEATURES_AVAILABLE = True
    print("✅ Enhanced Pinterest integration modules loaded")
except ImportError as e:
    print(f"⚠️ Could not load enhanced integration modules: {e}")
    PinGenerationEnhancement = None
    ENHANCED_FEATURES_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('track_ai_scheduler.log')
    ]
)
logger = logging.getLogger(__name__)

# Track AI Configuration
TRACK_AI_ENABLED = os.getenv("TRACK_AI_ENABLED", "true").lower() == "true"
TRACK_AI_ENDPOINT = os.getenv("TRACK_AI_ENDPOINT", "https://your-track-ai-domain.com/api/event/track")
TRACK_AI_STORE_ID = os.getenv("TRACK_AI_STORE_ID", "pinterest_store")
TRACK_AI_PIXEL_ID = os.getenv("TRACK_AI_PIXEL_ID", "pinterest_pixel")

def validate_track_ai_setup() -> bool:
    """
    Validate Track AI setup and configuration
    
    Returns:
        True if Track AI is properly configured, False otherwise
    """
    try:
        validation_results = validate_track_ai_integration()
        
        if not validation_results['is_configured']:
            logger.warning(f"⚠️ Track AI not fully configured. Missing: {validation_results['missing_config']}")
            return False
        
        logger.info("✅ Track AI configuration validated")
        logger.info(f"   Endpoint: {validation_results['track_ai_endpoint']}")
        logger.info(f"   Store ID: {validation_results['track_ai_store_id']}")
        logger.info(f"   Pixel ID: {validation_results['track_ai_pixel_id']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error validating Track AI setup: {e}")
        return False

def post_pins_with_track_ai(max_pins: int = 50, delay_between_posts: int = 30) -> bool:
    """
    Post pins with Track AI integration for empty rows in Sheet1
    
    Args:
        max_pins: Maximum number of pins to post
        delay_between_posts: Delay between pin posts in seconds
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("🚀 Starting Track AI Enhanced Pin Posting")
        
        # Validate Track AI setup
        if TRACK_AI_ENABLED and not validate_track_ai_setup():
            logger.warning("⚠️ Track AI not configured, proceeding without Track AI integration")
        
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
                status = row[11] if row[11] else 'EMPTY'  # Status column
                if status == 'EMPTY' or status == '':
                    empty_rows.append((i, row))
        
        logger.info(f"📌 Found {len(empty_rows)} empty rows")
        
        if not empty_rows:
            logger.info("✅ No empty rows found - all pins already posted")
            return True
        
        # Process pins with Track AI integration
        posted_count = 0
        failed_count = 0
        
        for i, (row_num, row) in enumerate(empty_rows[:max_pins]):
            try:
                logger.info(f"📌 Processing row {row_num} ({i+1}/{min(max_pins, len(empty_rows))}) with Track AI integration")
                
                # Extract data
                product_name = row[1] if len(row) > 1 else "Unknown Product"
                product_type = row[4] if len(row) > 4 else "Unknown Type"
                image_url = row[5] if len(row) > 5 else ""
                title = row[6] if len(row) > 6 else ""
                description = row[7] if len(row) > 7 else ""
                board_title = row[8] if len(row) > 8 else "Outfit Inspirationen"
                
                if not image_url or not title or not description:
                    logger.warning(f"⚠️ Skipping row {row_num} - missing required data")
                    continue
                
                # Generate enhanced content with Pinterest trends
                if enhanced_pin_generation:
                    try:
                        logger.info("🎯 Generating enhanced pin content with Pinterest trends and customer persona...")
                        enhanced_title = enhanced_pin_generation.generate_enhanced_pin_title(
                            [product_name, product_type, image_url, title, description],
                            use_trending_keywords=True,
                            region="DE"
                        )
                        enhanced_description = enhanced_pin_generation.generate_enhanced_pin_description(
                            [product_name, product_type, image_url, title, description],
                            use_trending_keywords=True,
                            region="DE"
                        )
                        
                        title = enhanced_title
                        description = enhanced_description
                        logger.info("✅ Enhanced content generated with trending keywords")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Enhanced content generation failed: {e}")
                
                # Get or create board
                from pinterest_post import get_or_create_board
                board_id = get_or_create_board(access_token, board_title)
                
                if not board_id:
                    logger.error(f"❌ Failed to get/create board: {board_title}")
                    failed_count += 1
                    continue
                
                # Generate destination URL with Track AI integration
                base_url = f"https://92c6ce-58.myshopify.com/products/{product_name.lower().replace(' ', '-')}"
                
                # Track AI integration parameters
                campaign_name = f"TrackAI_Sheet1_Campaign_{datetime.now().strftime('%Y%m%d')}"
                objective_type = "WEB_CONVERSION"
                launch_date = datetime.now().strftime('%Y-%m-%d')
                
                # Post pin with Track AI integration
                pin_id = post_pin_with_track_ai(
                    access_token=access_token,
                    board_id=board_id,
                    image_url=image_url,
                    title=title,
                    description=description,
                    destination_url=base_url,
                    campaign_name=campaign_name,
                    objective_type=objective_type,
                    launch_date=launch_date,
                    product_name=product_name,
                    product_type=product_type,
                    board_title=board_title,
                    pin_variant=f"pin_{i+1}",
                    daily_budget=1000  # €10.00 default
                )
                
                if pin_id:
                    # Update sheet with pin ID and status
                    sheet1.update_cell(row_num, 12, "POSTED")  # Status column
                    sheet1.update_cell(row_num, 14, pin_id)   # Pin ID column
                    posted_count += 1
                    logger.info(f"✅ Pin posted with Track AI integration: {pin_id}")
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed to post pin for row {row_num}")
                
                # Rate limiting delay
                time.sleep(delay_between_posts)
                
            except Exception as e:
                logger.error(f"❌ Error processing row {row_num}: {e}")
                failed_count += 1
                continue
        
        logger.info(f"🎯 Track AI Pin Posting Results:")
        logger.info(f"   ✅ Successful: {posted_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        logger.info(f"   📊 Total processed: {posted_count + failed_count}")
        
        return posted_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error in Track AI pin posting: {e}")
        return False

def create_campaigns_with_track_ai() -> bool:
    """
    Create Pinterest campaigns with Track AI integration
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("🎯 Starting Track AI Enhanced Campaign Creation")
        
        # Connect to Sheet1
        workbook = google_sheets_client.open_by_key(SHEET_ID)
        sheet1 = workbook.worksheet('Sheet1')
        
        # Get Pinterest access token and ad account
        access_token = get_access_token()
        ad_account_id = get_ad_account_id(access_token)
        
        if not ad_account_id:
            logger.error("❌ Could not get ad account ID")
            return False
        
        logger.info(f"✅ Using Ad Account ID: {ad_account_id}")
        
        # Get all data
        data = sheet1.get_all_values()
        
        # Find posted rows without campaigns
        eligible_rows = []
        for i, row in enumerate(data[1:], 2):
            if len(row) > 15:
                status = row[11] if row[11] else ''  # Status column
                campaign_status = row[14] if len(row) > 14 and row[14] else ''  # Status2 column
                
                if status == 'POSTED' and (not campaign_status or campaign_status == ''):
                    eligible_rows.append((i, row))
        
        logger.info(f"📊 Found {len(eligible_rows)} eligible rows for Track AI campaign creation")
        
        if not eligible_rows:
            logger.info("✅ No eligible rows found for campaign creation")
            return True
        
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
        
        # Group products into campaigns targeting 40-50 pins per campaign
        target_pins_per_campaign = 45
        product_list = list(product_pins.items())
        campaign_groups = []
        
        current_group = []
        current_pin_count = 0
        
        for product_name, pin_list in product_list:
            current_group.append((product_name, pin_list))
            current_pin_count += len(pin_list)
            
            if current_pin_count >= target_pins_per_campaign:
                campaign_groups.append(current_group)
                current_group = []
                current_pin_count = 0
        
        # Add remaining products as final campaign
        if current_group:
            campaign_groups.append(current_group)
        
        logger.info(f"📊 Creating {len(campaign_groups)} Track AI enhanced campaigns")
        
        created_campaigns = 0
        total_ads_created = 0
        
        for group_idx, group in enumerate(campaign_groups):
            try:
                # Create campaign with Track AI integration
                campaign_name = f"TrackAI_Sheet1_Multi_Product_Campaign_{group_idx + 1}"
                total_pins_in_group = sum(len(pin_list) for _, pin_list in group)
                unique_products = len(group)
                
                # Dynamic budget allocation
                if unique_products >= 15:
                    daily_budget = 2000  # €20.00 for 15+ unique products
                    budget_reason = f"15+ products ({unique_products})"
                else:
                    daily_budget = 1000  # €10.00 for 10-14 unique products
                    budget_reason = f"10-14 products ({unique_products})"
                
                logger.info(f"🎯 Creating Track AI campaign: {campaign_name}")
                logger.info(f"   📊 Products: {unique_products}, Pins: {total_pins_in_group}")
                logger.info(f"   💰 Budget: €{daily_budget/100:.2f} ({budget_reason})")
                
                campaign_id = create_campaign(
                    access_token=access_token,
                    ad_account_id=ad_account_id,
                    campaign_name=campaign_name,
                    daily_budget=daily_budget
                )
                
                if campaign_id:
                    logger.info(f"✅ Track AI campaign created: {campaign_id}")
                    created_campaigns += 1
                    
                    # Create ad group
                    ad_group_id = create_ad_group(
                        access_token=access_token,
                        ad_account_id=ad_account_id,
                        campaign_id=campaign_id,
                        product_name=f"TrackAI Multi-Product Group {group_idx + 1}"
                    )
                    
                    if ad_group_id:
                        logger.info(f"✅ Track AI ad group created: {ad_group_id}")
                        
                        # Create ads for all pins with Track AI integration
                        ads_created_in_group = 0
                        for product_name, pin_list in group:
                            logger.info(f"📌 Processing Track AI product: {product_name} with {len(pin_list)} pins")
                            
                            for pin_idx, (row_num, row, pin_id) in enumerate(pin_list):
                                try:
                                    # Create ad with Track AI integration
                                    ad_name = f"TrackAI_{product_name[:25]}_Pin{pin_idx+1}_Ad"
                                    ad_id = create_ad(
                                        access_token=access_token,
                                        ad_account_id=ad_account_id,
                                        ad_group_id=ad_group_id,
                                        pin_id=pin_id,
                                        ad_name=ad_name
                                    )
                                    
                                    if ad_id:
                                        # Update sheet with campaign data
                                        sheet1.update_cell(row_num, 15, 'ACTIVE')  # Status2
                                        sheet1.update_cell(row_num, 16, campaign_id)  # Ad Campaign Status
                                        sheet1.update_cell(row_num, 17, datetime.now().strftime('%Y-%m-%d'))  # Advertised At
                                        sheet1.update_cell(row_num, 18, ad_id)  # Ad ID
                                        
                                        ads_created_in_group += 1
                                        total_ads_created += 1
                                        logger.info(f"✅ Track AI ad created: {ad_id} for {product_name} Pin {pin_idx+1}")
                                    else:
                                        logger.warning(f"⚠️ Failed to create Track AI ad for {product_name} Pin {pin_idx+1}")
                                        
                                except Exception as e:
                                    logger.error(f"❌ Error creating Track AI ad for {product_name} Pin {pin_idx+1}: {e}")
                                    continue
                        
                        logger.info(f"✅ Track AI Campaign {campaign_id}: {ads_created_in_group} ads created")
                    else:
                        logger.warning(f"⚠️ Failed to create Track AI ad group for campaign {campaign_id}")
                else:
                    logger.warning(f"⚠️ Failed to create Track AI campaign for group {group_idx + 1}")
                    
            except Exception as e:
                logger.error(f"❌ Error creating Track AI campaign group {group_idx + 1}: {e}")
                continue
        
        logger.info(f"🎯 Track AI Campaign Creation Results:")
        logger.info(f"   📊 Campaigns created: {created_campaigns}")
        logger.info(f"   📌 Ads created: {total_ads_created}")
        logger.info(f"   💰 Dynamic budget: €10.00 (10-14 products) | €20.00 (15+ products)")
        
        return created_campaigns > 0
        
    except Exception as e:
        logger.error(f"❌ Error in Track AI campaign creation: {e}")
        return False

def main():
    """
    Main Track AI enhanced scheduler function
    """
    try:
        logger.info("🚀 Starting Track AI Enhanced Pinterest Scheduler")
        logger.info(f"⏰ Started at: {datetime.now()}")
        logger.info(f"🔧 Track AI Enabled: {TRACK_AI_ENABLED}")
        
        # Step 1: Post pins with Track AI integration
        logger.info("📌 Step 1: Posting pins with Track AI integration...")
        pin_success = post_pins_with_track_ai(max_pins=50, delay_between_posts=30)
        
        if pin_success:
            logger.info("✅ Step 1 completed: Pins posted with Track AI integration")
        else:
            logger.info("ℹ️ Step 1: No new pins posted or Track AI integration failed")
        
        # Step 2: Create campaigns with Track AI integration
        logger.info("🎯 Step 2: Creating campaigns with Track AI integration...")
        campaign_success = create_campaigns_with_track_ai()
        
        if campaign_success:
            logger.info("✅ Step 2 completed: Campaigns created with Track AI integration")
        else:
            logger.info("ℹ️ Step 2: No new campaigns created or Track AI integration failed")
        
        logger.info("🎉 Track AI Enhanced Pinterest Scheduler completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Track AI Enhanced Scheduler failed: {e}")

if __name__ == "__main__":
    main()
