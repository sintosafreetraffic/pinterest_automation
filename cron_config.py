# Cron Job Configuration
# These are the default settings that will be used when the cron job runs
# No user interface - all settings are pre-configured

# Step 1: Content Generation Settings
CONTENT_GENERATION_CONFIG = {
    "collection_id": "644749033796",  # READY FOR PINTEREST collection
    "image_limit": 3,  # Number of images per product to process
}

# Step 2: Pinterest Posting Settings  
PINTEREST_POSTING_CONFIG = {
    "enabled": True,  # Whether to post pins to Pinterest
}

# Step 3: Campaign Creation Settings
CAMPAIGN_CREATION_CONFIG = {
    "enabled": True,  # Whether to create campaigns
    "campaign_type": "WEB_CONVERSION",  # WEB_CONVERSION, CONSIDERATION, CATALOG_SALES
    "campaign_mode": "multi_product",  # single_product, multi_product
    "products_per_campaign": 10,  # For multi_product mode (10 products per campaign)
    "daily_budget": 1000,  # Daily budget in cents (1000 = 10 euro)
    "target_language": "de",  # en, de, fr, es, it, nl, pt
    "enable_second_sheet": False,  # Whether to use a second sheet
    "second_sheet_id": "",  # Second sheet ID if enabled
    "campaign_start_date": "next_tuesday",  # immediate, next_tuesday, custom
    "custom_start_date": "",  # Custom date if campaign_start_date is "custom"
}

# Collection Management Settings
COLLECTION_MANAGEMENT_CONFIG = {
    "source_collection_id": "644749033796",  # READY FOR PINTEREST
    "generated_collection_id": "651569889604",  # GENERATED
    "cleanup_enabled": True,  # Whether to move processed products
}

# AI Settings
AI_CONFIG = {
    "model": "deepseek-chat",  # AI model to use
    "max_tokens": 100,
    "temperature": 0.7,
}

# Rate Limiting Settings
RATE_LIMITING_CONFIG = {
    "shopify_delay": 0.6,  # Delay between Shopify API calls (seconds)
    "pinterest_delay": 1.0,  # Delay between Pinterest API calls (seconds)
}
