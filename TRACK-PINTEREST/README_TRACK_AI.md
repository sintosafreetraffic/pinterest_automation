# Pinterest Track AI Integration
================================

This directory contains the enhanced Pinterest automation system with Track AI pixel integration for comprehensive conversion tracking and cross-platform attribution.

## 🎯 Features

### **Track AI Integration**
- **UTM Parameter Generation**: Automatic UTM parameter generation for Pinterest campaigns
- **Pixel Integration**: Track AI pixel integration for all destination URLs
- **Cross-Platform Attribution**: Track customer journey across Pinterest, Meta, TikTok
- **Conversion Tracking**: Comprehensive conversion tracking with Pinterest metadata
- **ROI Measurement**: Calculate return on investment for Pinterest campaigns

### **Enhanced Pinterest Features**
- **Trending Keywords**: Integration with Pinterest trending keywords API
- **Audience Insights**: Customer persona generation based on Pinterest audience data
- **Enhanced Pin Generation**: AI-driven pin titles and descriptions with trending keywords
- **Multi-Product Campaigns**: Dynamic campaign creation with 40-50 pins per campaign
- **Dynamic Budget Allocation**: €10.00 for 10-14 products, €20.00 for 15+ products

## 📁 File Structure

```
TRACK-PINTEREST/
├── track_ai_integration.py          # Core Track AI integration module
├── pinterest_post_enhanced.py         # Enhanced Pinterest posting with Track AI
├── scheduler_track_ai.py           # Track AI enhanced scheduler
├── track_ai_config.env             # Track AI configuration template
├── README_TRACK_AI.md              # This documentation
├── pinterest_post.py               # Original Pinterest posting (backup)
├── forefront.py                    # Original forefront (backup)
├── a.py                           # Original campaign creation (backup)
├── scheduler_sheet1.py            # Original scheduler (backup)
├── pinterest_auth.py              # Pinterest authentication
├── track-ai/                      # Track AI system directory
└── credentials.json               # Google Sheets credentials
```

## 🚀 Quick Start

### **1. Configuration Setup**

Copy the configuration template and update with your settings:

```bash
cp track_ai_config.env .env
```

Update the following settings in `.env`:

```env
# Track AI Settings
TRACK_AI_ENABLED=true
TRACK_AI_ENDPOINT=https://your-track-ai-domain.com/api/event/track
TRACK_AI_STORE_ID=pinterest_store
TRACK_AI_PIXEL_ID=pinterest_pixel

# Pinterest Settings
PINTEREST_APP_ID=your_pinterest_app_id
PINTEREST_APP_SECRET=your_pinterest_app_secret

# Shopify Settings
SHOPIFY_STORE_URL=https://your-store.myshopify.com
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_COLLECTION_ID=your_collection_id
```

### **2. Run Track AI Enhanced Scheduler**

```bash
python3 scheduler_track_ai.py
```

### **3. Monitor Track AI Integration**

Check the logs for Track AI integration status:

```bash
tail -f track_ai_scheduler.log
```

## 🔧 Track AI Integration Details

### **UTM Parameter Schema**

The system automatically generates comprehensive UTM parameters:

#### **Core UTM Parameters:**
- `utm_source=pinterest` - Identifies Pinterest as traffic source
- `utm_medium=cpc` - Distinguishes paid Pinterest ads
- `utm_campaign={launch_date}_{campaign_name}_{objective_type}` - Unique campaign identification
- `utm_term={product_name}_{product_type}` - Product-level keyword tracking
- `utm_content={board_title}_{pin_variant}` - Content differentiation for A/B testing

#### **Pinterest-Specific Parameters:**
- `utm_campaign_id={campaign_id}` - Pinterest campaign ID
- `utm_pin_id={pin_id}` - Pinterest pin ID
- `utm_ad_id={ad_id}` - Pinterest ad ID
- `utm_budget_tier={budget_tier}` - Budget-based performance analysis

#### **Track AI Parameters:**
- `utm_track_ai_store={store_id}` - Track AI store identifier
- `utm_track_ai_pixel={pixel_id}` - Track AI pixel identifier
- `track_ai_event=page_view` - Track AI event type
- `track_ai_timestamp={timestamp}` - Event timestamp

### **Enhanced Destination URLs**

Example of enhanced destination URL with Track AI integration:

```
https://your-store.myshopify.com/products/product-handle?
utm_source=pinterest&
utm_medium=cpc&
utm_campaign=2025-09-24_trackai_sheet1_campaign_1_web_conversion&
utm_term=benita_trendige_jacke_jacket&
utm_content=outfit_inspirationen_pin_1&
utm_campaign_id=626756549052&
utm_pin_id=1042935226223691768&
utm_ad_id=687294094128&
utm_budget_tier=10_euro&
utm_track_ai_store=pinterest_store&
utm_track_ai_pixel=pinterest_pixel&
track_ai_event=page_view&
track_ai_store_id=pinterest_store&
track_ai_pixel_id=pinterest_pixel&
track_ai_timestamp=1758740067
```

## 📊 Track AI Dashboard Integration

### **Event Mapping**
- **utm_campaign** → Track AI campaign_id
- **utm_term** → Track AI product_id
- **utm_content** → Track AI content_variant
- **utm_pin_id** → Track AI pin_id
- **utm_ad_id** → Track AI ad_id

### **Conversion Tracking**
- **Pinterest Click Events** → Track AI click events
- **Shopify Purchase Events** → Track AI conversion events
- **Cross-Platform Attribution** → Track AI attribution analysis

## 🎯 Campaign Features

### **Multi-Product Campaigns**
- **Target**: 40-50 pins per campaign
- **Dynamic Grouping**: Products grouped by pin count
- **Budget Allocation**: €10.00 (10-14 products) | €20.00 (15+ products)

### **Enhanced Pin Generation**
- **Trending Keywords**: Integration with Pinterest trending keywords API
- **Customer Persona**: AI-generated customer personas based on audience insights
- **Enhanced Descriptions**: AI-driven pin descriptions with trending keywords

### **Track AI Integration**
- **Automatic UTM Generation**: All campaigns include comprehensive UTM parameters
- **Pixel Integration**: Track AI pixels automatically added to all destination URLs
- **Cross-Platform Tracking**: Track customer journey across all platforms

## 🔍 Monitoring and Debugging

### **Log Files**
- `track_ai_scheduler.log` - Main scheduler logs
- `pinterest_post_enhanced.log` - Enhanced pin posting logs
- `track_ai_integration.log` - Track AI integration logs

### **Debug Mode**
Enable debug mode in `.env`:

```env
TRACK_AI_DEBUG=true
LOG_LEVEL=DEBUG
```

### **Validation**
Check Track AI integration status:

```python
from track_ai_integration import validate_track_ai_integration
validation_results = validate_track_ai_integration()
print(validation_results)
```

## 🚀 Deployment

### **Render Deployment**
Update `render.yaml` to use Track AI enhanced scheduler:

```yaml
- type: cron
  name: pinterest-track-ai-scheduler
  schedule: "0 5,17 * * *" # 5 AM and 5 PM UTC daily
  startCommand: python3 scheduler_track_ai.py
  envVars:
    - key: TRACK_AI_ENABLED
      value: "true"
    - key: TRACK_AI_ENDPOINT
      value: "https://your-track-ai-domain.com/api/event/track"
```

### **Environment Variables**
Required environment variables for Track AI integration:

```env
# Track AI Core
TRACK_AI_ENABLED=true
TRACK_AI_ENDPOINT=https://your-track-ai-domain.com/api/event/track
TRACK_AI_STORE_ID=pinterest_store
TRACK_AI_PIXEL_ID=pinterest_pixel

# Pinterest API
PINTEREST_APP_ID=your_pinterest_app_id
PINTEREST_APP_SECRET=your_pinterest_app_secret

# Shopify API
SHOPIFY_STORE_URL=https://your-store.myshopify.com
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_COLLECTION_ID=your_collection_id

# Google Sheets
GOOGLE_SHEETS_ID=your_google_sheets_id
```

## 📈 Expected Results

### **Enhanced Tracking Capabilities**
- **Campaign Attribution**: Track which campaigns drive conversions
- **Product Performance**: Analyze which products perform best
- **Content Optimization**: Identify high-performing pin content
- **Budget Optimization**: Optimize budget allocation based on performance

### **Cross-Platform Insights**
- **Pinterest → Shopify**: Track Pinterest traffic to Shopify conversions
- **Multi-Campaign Analysis**: Compare performance across different campaigns
- **ROI Measurement**: Calculate return on investment for Pinterest campaigns

## 🛠️ Troubleshooting

### **Common Issues**

1. **Track AI Not Configured**
   - Check environment variables
   - Verify Track AI endpoint is accessible
   - Ensure store ID and pixel ID are correct

2. **URL Length Issues**
   - System automatically creates fallback URLs
   - Check logs for URL length warnings
   - Essential parameters are preserved in fallback

3. **Enhanced Features Not Available**
   - Check if meta-change directory is accessible
   - Verify Pinterest trends API access
   - Check audience insights API permissions

### **Debug Commands**

```bash
# Check Track AI configuration
python3 -c "from track_ai_integration import validate_track_ai_integration; print(validate_track_ai_integration())"

# Test Pinterest authentication
python3 -c "from pinterest_auth import get_access_token; print(get_access_token())"

# Test enhanced features
python3 -c "from pin_generation_enhancement import PinGenerationEnhancement; print('Enhanced features available')"
```

## 📞 Support

For issues with Track AI integration:

1. Check the logs in `track_ai_scheduler.log`
2. Verify configuration in `.env`
3. Test individual components using debug commands
4. Check Track AI dashboard for event tracking

---

**Status**: ✅ **READY FOR DEPLOYMENT**
**Next Steps**: Configure Track AI settings and deploy enhanced scheduler
