#!/usr/bin/env python3
"""
Scheduler for Shopify-Pinterest Automation
Runs the complete automation workflow twice daily
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

def run_automation_workflow():
    """
    Run the complete automation workflow with smooth progression:
    1. Move processed products to GENERATED collection
    2. Generate pin titles and descriptions for new products (skip if already done)
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
        
        logger.info("🚀 Starting Shopify-Pinterest Automation Workflow")
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
        
        # Step 4: Create Pinterest campaigns (multi-product, 10 euro budget)
        logger.info("🎯 Step 4: Creating Pinterest campaigns (multi-product, 10 euro budget)...")
        try:
            from forefront import run_step3_campaign_creation
            # Configure for multi-product campaigns: 10 products, 10 euro budget
            second_sheet_id = os.getenv("SECOND_SHEET_ID", "")
            enable_second_sheet = bool(second_sheet_id)
            
            campaigns_success = run_step3_campaign_creation(
                campaign_mode="multi_product",
                products_per_campaign=10,
                daily_budget=1000,  # 10 euro in cents
                campaign_type="WEB_CONVERSION",
                target_language="de",
                enable_second_sheet=enable_second_sheet,
                second_sheet_id=second_sheet_id,
                campaign_start_date="next_tuesday",
                custom_start_date=""
            )
            if campaigns_success:
                logger.info("✅ Step 4 completed: Pinterest campaigns created (10 products, 10 euro budget)")
            else:
                logger.warning("⚠️ Step 4: Campaign creation failed")
        except Exception as e:
            logger.error(f"❌ Step 4 failed: {e}")
        
        logger.info("🎉 Automation workflow completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Automation workflow failed with error: {str(e)}")
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")
        return False

def main():
    """
    Main scheduler function
    """
    logger.info("🔄 Starting Pinterest Automation Scheduler")
    logger.info(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if required environment variables are set
    required_vars = [
        'SHOPIFY_API_KEY',
        'SHOPIFY_STORE_URL', 
        'SHOPIFY_COLLECTION_ID',
        'PINTEREST_ACCESS_TOKEN',
        'PINTEREST_APP_ID',
        'PINTEREST_APP_SECRET',
        'OPENAI_API_KEY',
        'SHEET_ID',
        'SECOND_SHEET_ID'  # For multi-product campaigns
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    logger.info("✅ All required environment variables are set")
    
    # Run the automation workflow
    success = run_automation_workflow()
    
    if success:
        logger.info("🎉 Scheduler execution completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Scheduler execution failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
