#!/usr/bin/env python3
"""
Enhanced Scheduler for Shopify-Pinterest Automation
Runs the complete automation workflow with Pinterest trends and audience insights integration
"""

import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Enhanced Pinterest integration imports
meta_change_path = '/Users/saschavanwell/Documents/meta-change'
sys.path.append(meta_change_path)

try:
    from pin_generation_enhancement import PinGenerationEnhancement
    logger.info("✅ Enhanced Pinterest integration modules loaded")
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Could not load enhanced integration modules: {e}")
    PinGenerationEnhancement = None
    ENHANCED_FEATURES_AVAILABLE = False

# Enhanced features configuration
ENHANCED_FEATURES_ENABLED = True  # Set to False to disable enhanced features
TRENDING_KEYWORDS_ENABLED = True  # Set to False to disable trending keywords
AUDIENCE_INSIGHTS_ENABLED = True  # Set to False to disable audience insights
DEFAULT_REGION = "DE"  # Default region for trending keywords

# Initialize enhanced integration
enhanced_pin_generation = None
if ENHANCED_FEATURES_AVAILABLE and PinGenerationEnhancement:
    try:
        enhanced_pin_generation = PinGenerationEnhancement()
        logger.info("✅ Enhanced pin generation initialized")
    except Exception as e:
        logger.warning(f"⚠️ Error initializing enhanced pin generation: {e}")
        enhanced_pin_generation = None

def run_enhanced_automation_workflow():
    """
    Run the complete automation workflow with Pinterest trends and audience insights integration:
    1. Move processed products to GENERATED collection
    2. Generate enhanced pin titles and descriptions with trending keywords and audience insights
    3. Create Pinterest pins (handle anti-spam gracefully)
    4. Create Pinterest campaigns (multi-product, 10 euro budget)
    """
    try:
        # Setup Google credentials first
        logger.info("🔧 Setting up Google credentials...")
        from fix_credentials import setup_google_credentials
        if not setup_google_credentials():
            logger.error("❌ Failed to setup Google credentials")
            return False
        
        # Setup Pinterest token
        logger.info("🔧 Setting up Pinterest token...")
        from fix_pinterest_token import setup_pinterest_token
        if not setup_pinterest_token():
            logger.warning("⚠️ Failed to setup Pinterest token - pin creation and campaigns may fail")
        
        logger.info("🚀 Starting Enhanced Shopify-Pinterest Automation Workflow")
        logger.info(f"⏰ Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Enhanced features status
        if ENHANCED_FEATURES_ENABLED and enhanced_pin_generation:
            logger.info("🎯 Enhanced features enabled:")
            logger.info(f"   ✅ Trending keywords: {'Enabled' if TRENDING_KEYWORDS_ENABLED else 'Disabled'}")
            logger.info(f"   ✅ Audience insights: {'Enabled' if AUDIENCE_INSIGHTS_ENABLED else 'Disabled'}")
            logger.info(f"   ✅ Region: {DEFAULT_REGION}")
        else:
            logger.info("⚠️ Enhanced features disabled - using original pin generation")
        
        # Step 1: Move processed products to GENERATED collection
        logger.info("📋 Step 1: Moving processed products to GENERATED collection...")
        try:
            from a import move_processed_products_to_generated_collection
            move_success = move_processed_products_to_generated_collection()
            if move_success:
                logger.info("✅ Step 1 completed: Processed products moved to GENERATED collection")
            else:
                logger.info("ℹ️ Step 1: No products were moved (normal if no processed products exist)")
        except Exception as e:
            logger.warning(f"⚠️ Step 1 failed: {e}. Continuing to next step...")
        
        # Step 2: Generate enhanced pin titles and descriptions with Pinterest trends and customer persona
        logger.info("🤖 Step 2: Checking for products needing enhanced content generation with Pinterest trends and customer persona...")
        try:
            from forefront import run_step1_content_generation_enhanced
            # Use the READY FOR PINTEREST collection ID
            ready_collection_id = os.getenv("SHOPIFY_COLLECTION_ID", "644749033796")
            content_success = run_step1_content_generation_enhanced(ready_collection_id)
            if content_success:
                logger.info("✅ Step 2 completed: Enhanced pin titles and descriptions generated with Pinterest trends and customer persona")
            else:
                logger.info("ℹ️ Step 2: No new content generation needed (products already have content)")
        except Exception as e:
            logger.warning(f"⚠️ Step 2 failed: {e}. Continuing to next step...")
        
        # Step 3: Create Pinterest pins (handle anti-spam gracefully)
        logger.info("📌 Step 3: Creating Pinterest pins...")
        try:
            from forefront import run_step2_pinterest_posting
            pins_success = run_step2_pinterest_posting()
            if pins_success:
                logger.info("✅ Step 3 completed: Pinterest pins created")
            else:
                logger.warning("⚠️ Step 3: Pin creation failed (possibly due to Pinterest anti-spam)")
                logger.info("ℹ️ Continuing to campaign creation despite pin creation failure...")
        except Exception as e:
            logger.warning(f"⚠️ Step 3 failed: {e}. Continuing to campaign creation...")
        
        # Step 4: Create Pinterest campaigns (multi-product, 10 products per campaign, 10 euro budget)
        logger.info("🎯 Step 4: Creating Pinterest campaigns (multi-product, 10 products per campaign, 10 euro budget)...")
        try:
            from forefront import run_step3_campaign_creation
            # Configure for multi-product campaigns: 10 products per campaign, 10 euro budget
            second_sheet_id = os.getenv("SECOND_SHEET_ID")
            if not second_sheet_id:
                logger.error("❌ CRITICAL ERROR: SECOND_SHEET_ID environment variable is required for multi-product campaigns!")
                logger.error("Please set SECOND_SHEET_ID in your .env file")
                return False
            
            campaign_success = run_step3_campaign_creation(second_sheet_id)
            if campaign_success:
                logger.info("✅ Step 4 completed: Pinterest campaigns created")
            else:
                logger.warning("⚠️ Step 4: Campaign creation failed")
        except Exception as e:
            logger.warning(f"⚠️ Step 4 failed: {e}")
        
        logger.info("🎉 Enhanced automation workflow completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced automation workflow failed: {e}")
        return False

def run_original_automation_workflow():
    """
    Run the original automation workflow (fallback)
    """
    try:
        # Setup Google credentials first
        logger.info("🔧 Setting up Google credentials...")
        from fix_credentials import setup_google_credentials
        if not setup_google_credentials():
            logger.error("❌ Failed to setup Google credentials")
            return False
        
        # Setup Pinterest token
        logger.info("🔧 Setting up Pinterest token...")
        from fix_pinterest_token import setup_pinterest_token
        if not setup_pinterest_token():
            logger.warning("⚠️ Failed to setup Pinterest token - pin creation and campaigns may fail")
        
        logger.info("🚀 Starting Original Shopify-Pinterest Automation Workflow")
        logger.info(f"⏰ Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Move processed products to GENERATED collection
        logger.info("📋 Step 1: Moving processed products to GENERATED collection...")
        try:
            from a import move_processed_products_to_generated_collection
            move_success = move_processed_products_to_generated_collection()
            if move_success:
                logger.info("✅ Step 1 completed: Processed products moved to GENERATED collection")
            else:
                logger.info("ℹ️ Step 1: No products were moved (normal if no processed products exist)")
        except Exception as e:
            logger.warning(f"⚠️ Step 1 failed: {e}. Continuing to next step...")
        
        # Step 2: Generate pin titles and descriptions (skip if already done)
        logger.info("🤖 Step 2: Checking for products needing content generation...")
        try:
            from forefront import run_step1_content_generation
            # Use the READY FOR PINTEREST collection ID
            ready_collection_id = os.getenv("SHOPIFY_COLLECTION_ID", "644749033796")
            content_success = run_step1_content_generation(ready_collection_id)
            if content_success:
                logger.info("✅ Step 2 completed: Pin titles and descriptions generated")
            else:
                logger.info("ℹ️ Step 2: No new content generation needed (products already have content)")
        except Exception as e:
            logger.warning(f"⚠️ Step 2 failed: {e}. Continuing to next step...")
        
        # Step 3: Create Pinterest pins (handle anti-spam gracefully)
        logger.info("📌 Step 3: Creating Pinterest pins...")
        try:
            from forefront import run_step2_pinterest_posting
            pins_success = run_step2_pinterest_posting()
            if pins_success:
                logger.info("✅ Step 3 completed: Pinterest pins created")
            else:
                logger.warning("⚠️ Step 3: Pin creation failed (possibly due to Pinterest anti-spam)")
                logger.info("ℹ️ Continuing to campaign creation despite pin creation failure...")
        except Exception as e:
            logger.warning(f"⚠️ Step 3 failed: {e}. Continuing to campaign creation...")
        
        # Step 4: Create Pinterest campaigns (multi-product, 10 products per campaign, 10 euro budget)
        logger.info("🎯 Step 4: Creating Pinterest campaigns (multi-product, 10 products per campaign, 10 euro budget)...")
        try:
            from forefront import run_step3_campaign_creation
            # Configure for multi-product campaigns: 10 products per campaign, 10 euro budget
            second_sheet_id = os.getenv("SECOND_SHEET_ID")
            if not second_sheet_id:
                logger.error("❌ CRITICAL ERROR: SECOND_SHEET_ID environment variable is required for multi-product campaigns!")
                logger.error("Please set SECOND_SHEET_ID in your .env file")
                return False
            
            campaign_success = run_step3_campaign_creation(second_sheet_id)
            if campaign_success:
                logger.info("✅ Step 4 completed: Pinterest campaigns created")
            else:
                logger.warning("⚠️ Step 4: Campaign creation failed")
        except Exception as e:
            logger.warning(f"⚠️ Step 4 failed: {e}")
        
        logger.info("🎉 Original automation workflow completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Original automation workflow failed: {e}")
        return False

def main():
    """Main function to run the enhanced automation workflow"""
    
    logger.info("🚀 Starting Enhanced Shopify-Pinterest Automation")
    logger.info("=" * 60)
    
    # Check if enhanced features are available
    if ENHANCED_FEATURES_ENABLED and enhanced_pin_generation:
        logger.info("🎯 Enhanced features available - using enhanced workflow")
        success = run_enhanced_automation_workflow()
    else:
        logger.info("⚠️ Enhanced features not available - using original workflow")
        success = run_original_automation_workflow()
    
    if success:
        logger.info("✅ Automation completed successfully!")
    else:
        logger.error("❌ Automation failed!")
    
    return success

if __name__ == "__main__":
    main()
