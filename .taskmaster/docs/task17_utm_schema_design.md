# Task 17: UTM Parameter Schema Design for Pinterest Integration

## 🎯 OBJECTIVE
Design a comprehensive UTM parameter schema for Pinterest campaigns that integrates with Track AI to enable cross-platform attribution and conversion tracking.

## 📊 RESEARCH FINDINGS

### **Pinterest API Capabilities:**
- Pinterest supports automatic UTM parameter addition at account, campaign, or ad group level
- Default parameters: `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`
- Pinterest-specific click tracking via `pclid` parameter
- Campaign metadata includes: campaign_name, objective_type, daily_budget, start_time

### **Current System Metadata Available:**
- **Campaign Level**: campaign_name, objective_type, daily_budget, launch_date
- **Product Level**: product_name, product_type, collection_id
- **Pin Level**: pin_id, board_id, board_title, pin_title, pin_description
- **Ad Level**: ad_id, ad_group_id, campaign_id

## 🏗️ UTM PARAMETER SCHEMA DESIGN

### **Core UTM Parameters:**

#### **1. utm_source**
- **Value**: `pinterest`
- **Purpose**: Identifies Pinterest as traffic source
- **Implementation**: Static value across all campaigns

#### **2. utm_medium**
- **Values**: 
  - `social` (for organic Pinterest content)
  - `cpc` (for paid Pinterest ads)
  - `social_cpc` (for Pinterest promoted pins)
- **Purpose**: Distinguishes between organic and paid Pinterest traffic
- **Implementation**: Dynamic based on campaign objective

#### **3. utm_campaign**
- **Format**: `{launch_date}_{campaign_name}_{objective_type}`
- **Examples**:
  - `2025-09-24_sheet1_multi_product_campaign_1_web_conversion`
  - `2025-09-24_summer_sale_consideration`
- **Purpose**: Unique campaign identification
- **Implementation**: Generated from existing campaign metadata

#### **4. utm_term**
- **Format**: `{product_name}_{product_type}`
- **Examples**:
  - `benita_trendige_jacke_jacket`
  - `rainer_fahrradschuhe_shoes`
- **Purpose**: Product-level keyword tracking
- **Implementation**: Generated from product metadata

#### **5. utm_content**
- **Format**: `{board_title}_{pin_variant}`
- **Examples**:
  - `outfit_inspirationen_pin_1`
  - `trend_produkte_pin_2`
- **Purpose**: Content differentiation for A/B testing
- **Implementation**: Generated from board and pin metadata

### **Extended Tracking Parameters:**

#### **6. utm_pin_id**
- **Format**: `{pin_id}`
- **Purpose**: Direct pin-level tracking
- **Implementation**: Pinterest pin ID

#### **7. utm_board_id**
- **Format**: `{board_id}`
- **Purpose**: Board-level performance tracking
- **Implementation**: Pinterest board ID

#### **8. utm_ad_id**
- **Format**: `{ad_id}`
- **Purpose**: Ad-level conversion tracking
- **Implementation**: Pinterest ad ID

#### **9. utm_campaign_id**
- **Format**: `{campaign_id}`
- **Purpose**: Campaign-level attribution
- **Implementation**: Pinterest campaign ID

#### **10. utm_budget_tier**
- **Format**: `{budget_tier}`
- **Values**: `10_euro`, `20_euro`
- **Purpose**: Budget-based performance analysis
- **Implementation**: Based on daily_budget value

## 🔧 IMPLEMENTATION STRATEGY

### **Phase 1: Basic UTM Integration**
1. **Modify `create_campaign` function** to include UTM parameters in campaign metadata
2. **Update `create_ad` function** to append UTM parameters to destination URLs
3. **Implement UTM parameter generation** based on campaign metadata

### **Phase 2: Advanced Tracking**
1. **Add Pinterest-specific parameters** (pclid, pin_id, board_id)
2. **Implement dynamic UTM generation** based on product and campaign data
3. **Create UTM parameter validation** to ensure URL integrity

### **Phase 3: Track AI Integration**
1. **Map UTM parameters to Track AI event schema**
2. **Implement cross-platform attribution** using UTM data
3. **Create conversion tracking** with UTM parameter correlation

## 📋 UTM PARAMETER GENERATION LOGIC

### **Campaign-Level UTM Generation:**
```python
def generate_campaign_utm_params(campaign_name, objective_type, launch_date, daily_budget):
    return {
        'utm_source': 'pinterest',
        'utm_medium': 'cpc' if objective_type == 'WEB_CONVERSION' else 'social',
        'utm_campaign': f"{launch_date}_{campaign_name}_{objective_type}".lower().replace(' ', '_'),
        'utm_budget_tier': f"{daily_budget/100:.0f}_euro"
    }
```

### **Product-Level UTM Generation:**
```python
def generate_product_utm_params(product_name, product_type, campaign_id):
    return {
        'utm_term': f"{product_name}_{product_type}".lower().replace(' ', '_'),
        'utm_campaign_id': campaign_id
    }
```

### **Pin-Level UTM Generation:**
```python
def generate_pin_utm_params(pin_id, board_id, board_title, pin_variant):
    return {
        'utm_content': f"{board_title}_{pin_variant}".lower().replace(' ', '_'),
        'utm_pin_id': pin_id,
        'utm_board_id': board_id
    }
```

## 🔗 TRACK AI INTEGRATION POINTS

### **Event Mapping:**
- **utm_campaign** → Track AI campaign_id
- **utm_term** → Track AI product_id
- **utm_content** → Track AI content_variant
- **utm_pin_id** → Track AI pin_id
- **utm_ad_id** → Track AI ad_id

### **Conversion Tracking:**
- **Pinterest Click Events** → Track AI click events
- **Shopify Purchase Events** → Track AI conversion events
- **Cross-Platform Attribution** → Track AI attribution analysis

## 📊 VALIDATION & TESTING

### **UTM Parameter Validation:**
1. **URL Length Limits**: Ensure UTM parameters don't exceed URL length limits
2. **Character Encoding**: Validate special characters are properly encoded
3. **Parameter Uniqueness**: Ensure UTM parameters are unique across campaigns

### **Testing Strategy:**
1. **Test Campaign Creation**: Verify UTM parameters are correctly generated
2. **Test URL Generation**: Ensure destination URLs include all UTM parameters
3. **Test Track AI Integration**: Verify UTM data flows to Track AI system
4. **Test Conversion Tracking**: Validate end-to-end conversion attribution

## 📈 EXPECTED OUTCOMES

### **Enhanced Tracking Capabilities:**
- **Campaign Attribution**: Track which campaigns drive conversions
- **Product Performance**: Analyze which products perform best
- **Content Optimization**: Identify high-performing pin content
- **Budget Optimization**: Optimize budget allocation based on performance

### **Cross-Platform Insights:**
- **Pinterest → Shopify**: Track Pinterest traffic to Shopify conversions
- **Multi-Campaign Analysis**: Compare performance across different campaigns
- **ROI Measurement**: Calculate return on investment for Pinterest campaigns

## 🚀 NEXT STEPS

1. **Implement UTM parameter generation** in campaign creation functions
2. **Modify destination URL generation** to include UTM parameters
3. **Create UTM parameter validation** functions
4. **Test UTM parameter implementation** with sample campaigns
5. **Integrate with Track AI** for comprehensive tracking

---

**Status**: ✅ **COMPLETED** - UTM Parameter Schema Designed
**Next Task**: Task 18 - Implement UTM Parameter Generation
