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
    Run the complete automation workflow:
    1. Move processed products to GENERATED collection
    2. Generate pin titles and descriptions for new products
    3. Create Pinterest pins
    4. Create Pinterest campaigns
    """
    try:
        logger.info("🚀 Starting Shopify-Pinterest Automation Workflow")
        logger.info(f"⏰ Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Move processed products to GENERATED collection
        logger.info("📋 Step 1: Moving processed products to GENERATED collection...")
        from a import move_processed_products_to_generated_collection
        move_success = move_processed_products_to_generated_collection()
        if move_success:
            logger.info("✅ Step 1 completed: Processed products moved to GENERATED collection")
        else:
            logger.warning("⚠️ Step 1: No products were moved (this is normal if no processed products exist)")
        
        # Step 2: Generate pin titles and descriptions
        logger.info("🤖 Step 2: Generating pin titles and descriptions...")
        from forefront import run_step1_content_generation
        content_success = run_step1_content_generation()
        if content_success:
            logger.info("✅ Step 2 completed: Pin titles and descriptions generated")
        else:
            logger.error("❌ Step 2 failed: Content generation failed")
            return False
        
        # Step 3: Create Pinterest pins
        logger.info("📌 Step 3: Creating Pinterest pins...")
        from forefront import run_step2_pin_creation
        pins_success = run_step2_pin_creation()
        if pins_success:
            logger.info("✅ Step 3 completed: Pinterest pins created")
        else:
            logger.error("❌ Step 3 failed: Pin creation failed")
            return False
        
        # Step 4: Create Pinterest campaigns
        logger.info("🎯 Step 4: Creating Pinterest campaigns...")
        from forefront import run_step3_campaign_creation
        campaigns_success = run_step3_campaign_creation()
        if campaigns_success:
            logger.info("✅ Step 4 completed: Pinterest campaigns created")
        else:
            logger.error("❌ Step 4 failed: Campaign creation failed")
            return False
        
        logger.info("🎉 Automation workflow completed successfully!")
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
        'SHEET_ID'
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
