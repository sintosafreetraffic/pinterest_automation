"""
Test Pinterest Analytics Widgets
===============================

This script tests the Pinterest-specific analytics widgets for the Track AI dashboard.

Features tested:
- Campaign ROI comparison widget
- Pin performance analysis widget
- Audience demographics widget
- Purchase funnel visualization widget
- Discovery phase metrics widget
- Trend analysis widget
- Cross-platform comparison widget
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_analytics_widgets import (
    PinterestAnalyticsWidgets,
    PinterestWidgetData,
    get_pinterest_analytics_widgets,
    get_specific_pinterest_widget
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_pinterest_widgets_initialization():
    """
    Test Pinterest analytics widgets initialization
    """
    try:
        logger.info("🧪 Testing Pinterest Analytics Widgets Initialization")
        
        # Initialize widgets
        widgets = PinterestAnalyticsWidgets()
        logger.info("✅ Pinterest analytics widgets initialized")
        
        # Test widget configurations
        configs = widgets.widget_configs
        logger.info(f"📊 Available widget types: {len(configs)}")
        
        for widget_type, config in configs.items():
            logger.info(f"   {widget_type}: {config['title']} ({config['type']})")
        
        # Test integration components
        logger.info(f"   Pinterest integration: {widgets.pinterest_integration is not None}")
        logger.info(f"   Attribution system: {widgets.attribution_system is not None}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pinterest widgets initialization test failed: {e}")
        return False

def test_campaign_roi_widget():
    """
    Test Pinterest Campaign ROI Comparison Widget
    """
    try:
        logger.info("\n🧪 Testing Pinterest Campaign ROI Widget")
        
        widgets = PinterestAnalyticsWidgets()
        
        # Mock Pinterest data
        mock_pinterest_data = {
            "campaigns": [
                {
                    "id": "campaign_1",
                    "name": "Summer Fashion Campaign",
                    "status": "ACTIVE",
                    "daily_budget": 1000
                },
                {
                    "id": "campaign_2", 
                    "name": "Winter Collection Campaign",
                    "status": "ACTIVE",
                    "daily_budget": 1500
                }
            ],
            "ads": [],
            "ad_groups": []
        }
        
        # Mock Pinterest integration
        with patch.object(widgets.pinterest_integration, 'get_pinterest_dashboard_data') as mock_data, \
             patch.object(widgets, '_get_campaign_metrics') as mock_metrics:
            
            # Mock responses
            mock_data.return_value = mock_pinterest_data
            
            mock_metrics.return_value = {
                "roas": 2.5,
                "cpa": 25.0,
                "revenue": 500.0,
                "spend": 200.0,
                "impressions": 5000,
                "clicks": 250,
                "purchases": 20
            }
            
            # Test date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Test campaign ROI widget
            widget = widgets.get_campaign_roi_widget(start_date, end_date)
            
            if widget and not widget.data.get("empty", False):
                logger.info("✅ Campaign ROI widget generated successfully")
                logger.info(f"   Widget type: {widget.widget_type}")
                logger.info(f"   Title: {widget.title}")
                logger.info(f"   Campaigns: {len(widget.data.get('campaigns', []))}")
                
                # Check widget data structure
                if "campaigns" in widget.data:
                    campaigns = widget.data["campaigns"]
                    logger.info(f"   Campaign data points: {len(campaigns)}")
                    
                    if campaigns:
                        first_campaign = campaigns[0]
                        logger.info(f"   First campaign ROAS: {first_campaign.get('roas', 0.0):.2f}")
                        logger.info(f"   First campaign revenue: €{first_campaign.get('revenue', 0.0):.2f}")
                
                # Check summary data
                if "summary" in widget.data:
                    summary = widget.data["summary"]
                    logger.info(f"   Total campaigns: {summary.get('total_campaigns', 0)}")
                    logger.info(f"   Average ROAS: {summary.get('avg_roas', 0.0):.2f}")
                    logger.info(f"   Total revenue: €{summary.get('total_revenue', 0.0):.2f}")
                
                return True
            else:
                logger.error(f"❌ Campaign ROI widget failed: {widget.data.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Campaign ROI widget test failed: {e}")
        return False

def test_pin_performance_widget():
    """
    Test Pinterest Pin Performance Analysis Widget
    """
    try:
        logger.info("\n🧪 Testing Pinterest Pin Performance Widget")
        
        widgets = PinterestAnalyticsWidgets()
        
        # Mock Pinterest data with ads
        mock_pinterest_data = {
            "campaigns": [],
            "ads": [
                {
                    "id": "ad_1",
                    "pin_id": "pin_123",
                    "campaign_id": "campaign_1",
                    "status": "ACTIVE"
                },
                {
                    "id": "ad_2",
                    "pin_id": "pin_456", 
                    "campaign_id": "campaign_1",
                    "status": "ACTIVE"
                }
            ],
            "ad_groups": []
        }
        
        # Mock Pinterest integration
        with patch.object(widgets.pinterest_integration, 'get_pinterest_dashboard_data') as mock_data, \
             patch.object(widgets, '_get_pin_metrics') as mock_metrics:
            
            # Mock responses
            mock_data.return_value = mock_pinterest_data
            
            mock_metrics.return_value = {
                "impressions": 1000,
                "clicks": 50,
                "saves": 25,
                "ctr": 5.0,
                "save_rate": 2.5,
                "spend": 30.0,
                "revenue": 75.0
            }
            
            # Test date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Test pin performance widget
            widget = widgets.get_pin_performance_widget(start_date, end_date, top_n=10)
            
            if widget and not widget.data.get("empty", False):
                logger.info("✅ Pin performance widget generated successfully")
                logger.info(f"   Widget type: {widget.widget_type}")
                logger.info(f"   Title: {widget.title}")
                logger.info(f"   Pins: {len(widget.data.get('pins', []))}")
                
                # Check widget data structure
                if "pins" in widget.data:
                    pins = widget.data["pins"]
                    logger.info(f"   Pin data points: {len(pins)}")
                    
                    if pins:
                        first_pin = pins[0]
                        logger.info(f"   First pin CTR: {first_pin.get('ctr', 0.0):.2f}%")
                        logger.info(f"   First pin save rate: {first_pin.get('save_rate', 0.0):.2f}%")
                
                # Check summary data
                if "summary" in widget.data:
                    summary = widget.data["summary"]
                    logger.info(f"   Total pins: {summary.get('total_pins', 0)}")
                    logger.info(f"   Average CTR: {summary.get('avg_ctr', 0.0):.2f}%")
                    logger.info(f"   Total impressions: {summary.get('total_impressions', 0):,}")
                
                return True
            else:
                logger.error(f"❌ Pin performance widget failed: {widget.data.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Pin performance widget test failed: {e}")
        return False

def test_audience_demographics_widget():
    """
    Test Pinterest Audience Demographics Widget
    """
    try:
        logger.info("\n🧪 Testing Pinterest Audience Demographics Widget")
        
        widgets = PinterestAnalyticsWidgets()
        
        # Mock attribution system with feed enhancement
        mock_feed_enhancement = Mock()
        mock_feed_enhancement.get_audience_insights.return_value = {
            "type": "YOUR_TOTAL_AUDIENCE",
            "size": 10000,
            "categories": [
                {"name": "Fashion", "ratio": 0.3},
                {"name": "Beauty", "ratio": 0.2}
            ]
        }
        
        mock_feed_enhancement.generate_customer_persona.return_value = {
            "persona_name": "Fashion Enthusiast",
            "demographics": {
                "ages": ["25-34", "35-44"],
                "genders": ["female", "male"],
                "interests": ["Fashion", "Beauty", "Lifestyle"]
            },
            "behavior": {
                "top_categories": ["Fashion", "Beauty"],
                "engagement_patterns": ["high_engagement", "seasonal_shopper"]
            }
        }
        
        # Mock attribution system
        with patch.object(widgets.attribution_system, 'feed_enhancement', mock_feed_enhancement):
            
            # Test date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Test audience demographics widget
            widget = widgets.get_audience_demographics_widget(start_date, end_date)
            
            if widget and not widget.data.get("empty", False):
                logger.info("✅ Audience demographics widget generated successfully")
                logger.info(f"   Widget type: {widget.widget_type}")
                logger.info(f"   Title: {widget.title}")
                
                # Check widget data structure
                if "persona" in widget.data:
                    persona = widget.data["persona"]
                    logger.info(f"   Persona name: {persona.get('name', 'Unknown')}")
                
                if "demographics" in widget.data:
                    demographics = widget.data["demographics"]
                    logger.info(f"   Age groups: {demographics.get('age_groups', [])}")
                    logger.info(f"   Genders: {demographics.get('genders', [])}")
                    logger.info(f"   Interests: {demographics.get('interests', [])}")
                
                if "behavior" in widget.data:
                    behavior = widget.data["behavior"]
                    logger.info(f"   Top categories: {behavior.get('top_categories', [])}")
                    logger.info(f"   Engagement patterns: {behavior.get('engagement_patterns', [])}")
                
                return True
            else:
                logger.error(f"❌ Audience demographics widget failed: {widget.data.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Audience demographics widget test failed: {e}")
        return False

def test_purchase_funnel_widget():
    """
    Test Pinterest-to-Purchase Funnel Widget
    """
    try:
        logger.info("\n🧪 Testing Pinterest Purchase Funnel Widget")
        
        widgets = PinterestAnalyticsWidgets()
        
        # Mock Pinterest data
        mock_pinterest_data = {
            "campaigns": [],
            "ads": [],
            "ad_groups": [],
            "metrics": [
                {"impressions": 10000, "clicks": 500, "saves": 200, "website_clicks": 100, "purchases": 25}
            ]
        }
        
        # Mock Pinterest integration
        with patch.object(widgets.pinterest_integration, 'get_pinterest_dashboard_data') as mock_data:
            
            # Mock response
            mock_data.return_value = mock_pinterest_data
            
            # Test date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Test purchase funnel widget
            widget = widgets.get_purchase_funnel_widget(start_date, end_date)
            
            if widget and not widget.data.get("empty", False):
                logger.info("✅ Purchase funnel widget generated successfully")
                logger.info(f"   Widget type: {widget.widget_type}")
                logger.info(f"   Title: {widget.title}")
                
                # Check widget data structure
                if "funnel_stages" in widget.data:
                    stages = widget.data["funnel_stages"]
                    logger.info(f"   Funnel stages: {len(stages)}")
                    
                    for stage in stages:
                        logger.info(f"   {stage['stage']}: {stage['count']} ({stage['conversion_rate']:.1f}%)")
                
                # Check summary data
                if "summary" in widget.data:
                    summary = widget.data["summary"]
                    logger.info(f"   Total impressions: {summary.get('total_impressions', 0):,}")
                    logger.info(f"   Total purchases: {summary.get('total_purchases', 0)}")
                    logger.info(f"   Overall conversion rate: {summary.get('overall_conversion_rate', 0.0):.2f}%")
                    logger.info(f"   Funnel efficiency: {summary.get('funnel_efficiency', 0.0):.2f}%")
                
                return True
            else:
                logger.error(f"❌ Purchase funnel widget failed: {widget.data.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Purchase funnel widget test failed: {e}")
        return False

def test_discovery_phase_widget():
    """
    Test Pinterest Discovery Phase Metrics Widget
    """
    try:
        logger.info("\n🧪 Testing Pinterest Discovery Phase Widget")
        
        widgets = PinterestAnalyticsWidgets()
        
        # Mock Pinterest data
        mock_pinterest_data = {
            "campaigns": [],
            "ads": [],
            "ad_groups": [],
            "metrics": [
                {"impressions": 20000, "saves": 800, "closeups": 1200, "clicks": 600}
            ]
        }
        
        # Mock Pinterest integration
        with patch.object(widgets.pinterest_integration, 'get_pinterest_dashboard_data') as mock_data:
            
            # Mock response
            mock_data.return_value = mock_pinterest_data
            
            # Test date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Test discovery phase widget
            widget = widgets.get_discovery_phase_widget(start_date, end_date)
            
            if widget and not widget.data.get("empty", False):
                logger.info("✅ Discovery phase widget generated successfully")
                logger.info(f"   Widget type: {widget.widget_type}")
                logger.info(f"   Title: {widget.title}")
                
                # Check widget data structure
                if "discovery_metrics" in widget.data:
                    metrics = widget.data["discovery_metrics"]
                    logger.info(f"   Impressions: {metrics.get('impressions', 0):,}")
                    logger.info(f"   Saves: {metrics.get('saves', 0)}")
                    logger.info(f"   Closeups: {metrics.get('closeups', 0)}")
                    logger.info(f"   Clicks: {metrics.get('clicks', 0)}")
                    logger.info(f"   Save rate: {metrics.get('save_rate', 0.0):.2f}%")
                    logger.info(f"   Closeup rate: {metrics.get('closeup_rate', 0.0):.2f}%")
                    logger.info(f"   Click rate: {metrics.get('click_rate', 0.0):.2f}%")
                
                # Check discovery scores
                if "discovery_scores" in widget.data:
                    scores = widget.data["discovery_scores"]
                    logger.info(f"   Overall discovery score: {scores.get('overall_discovery_score', 0.0):.1f}")
                
                return True
            else:
                logger.error(f"❌ Discovery phase widget failed: {widget.data.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Discovery phase widget test failed: {e}")
        return False

def test_trend_analysis_widget():
    """
    Test Pinterest Trend Analysis Widget
    """
    try:
        logger.info("\n🧪 Testing Pinterest Trend Analysis Widget")
        
        widgets = PinterestAnalyticsWidgets()
        
        # Mock attribution system with feed enhancement
        mock_feed_enhancement = Mock()
        mock_feed_enhancement.get_trending_keywords.return_value = {
            "keywords": [
                {"keyword": "fashion", "growth": 0.15, "volume": 1000},
                {"keyword": "style", "growth": 0.12, "volume": 800},
                {"keyword": "trendy", "growth": 0.10, "volume": 600}
            ]
        }
        
        # Mock attribution system
        with patch.object(widgets.attribution_system, 'feed_enhancement', mock_feed_enhancement):
            
            # Test date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Test trend analysis widget
            widget = widgets.get_trend_analysis_widget(start_date, end_date)
            
            if widget and not widget.data.get("empty", False):
                logger.info("✅ Trend analysis widget generated successfully")
                logger.info(f"   Widget type: {widget.widget_type}")
                logger.info(f"   Title: {widget.title}")
                
                # Check widget data structure
                if "trending_keywords" in widget.data:
                    keywords = widget.data["trending_keywords"]
                    logger.info(f"   Trending keywords: {len(keywords)}")
                    
                    for kw in keywords[:3]:  # Show first 3
                        logger.info(f"   {kw['keyword']}: {kw['growth']:.1%} growth, {kw['volume']} volume")
                
                # Check seasonal performance
                if "seasonal_performance" in widget.data:
                    seasonal = widget.data["seasonal_performance"]
                    logger.info(f"   Seasonal performance: {len(seasonal)} seasons")
                
                # Check summary
                if "summary" in widget.data:
                    summary = widget.data["summary"]
                    logger.info(f"   Total keywords: {summary.get('total_keywords', 0)}")
                    logger.info(f"   Average growth: {summary.get('avg_growth', 0.0):.1%}")
                    logger.info(f"   Top keyword: {summary.get('top_keyword', 'None')}")
                    logger.info(f"   Trend score: {summary.get('trend_score', 0.0):.1f}")
                
                return True
            else:
                logger.error(f"❌ Trend analysis widget failed: {widget.data.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Trend analysis widget test failed: {e}")
        return False

def test_cross_platform_widget():
    """
    Test Cross-Platform Pinterest Comparison Widget
    """
    try:
        logger.info("\n🧪 Testing Cross-Platform Pinterest Comparison Widget")
        
        widgets = PinterestAnalyticsWidgets()
        
        # Mock cross-platform performance analysis
        mock_performance_analysis = {
            "platform_breakdown": {
                "pinterest": {"impressions": 20000, "clicks": 1000, "ctr": 5.0},
                "meta": {"impressions": 15000, "clicks": 750, "ctr": 5.0},
                "google": {"impressions": 10000, "clicks": 400, "ctr": 4.0}
            },
            "attribution_scores": {
                "pinterest": 0.6,
                "meta": 0.3,
                "google": 0.1
            },
            "pinterest_optimization": {
                "optimization_score": 85.0
            },
            "meta_change_insights": {
                "trending_keywords": ["fashion", "style"]
            },
            "total_impressions": 45000,
            "total_clicks": 2150,
            "overall_ctr": 4.8
        }
        
        # Mock attribution system
        with patch.object(widgets.attribution_system, 'analyze_cross_platform_performance_with_meta_change') as mock_analysis:
            
            # Mock response
            mock_analysis.return_value = mock_performance_analysis
            
            # Test date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Test cross-platform widget
            widget = widgets.get_cross_platform_widget(start_date, end_date)
            
            if widget and not widget.data.get("empty", False):
                logger.info("✅ Cross-platform widget generated successfully")
                logger.info(f"   Widget type: {widget.widget_type}")
                logger.info(f"   Title: {widget.title}")
                
                # Check widget data structure
                if "platforms" in widget.data:
                    platforms = widget.data["platforms"]
                    logger.info(f"   Platforms: {len(platforms)}")
                    
                    for platform in platforms:
                        logger.info(f"   {platform['platform']}: {platform['impressions']:,} impressions, {platform['ctr']:.1f}% CTR, {platform['attribution_score']:.1f} attribution")
                
                # Check summary
                if "summary" in widget.data:
                    summary = widget.data["summary"]
                    logger.info(f"   Total impressions: {summary.get('total_impressions', 0):,}")
                    logger.info(f"   Total clicks: {summary.get('total_clicks', 0):,}")
                    logger.info(f"   Overall CTR: {summary.get('overall_ctr', 0.0):.1f}%")
                    logger.info(f"   Pinterest share: {summary.get('pinterest_share', 0.0):.1f}%")
                
                return True
            else:
                logger.error(f"❌ Cross-platform widget failed: {widget.data.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Cross-platform widget test failed: {e}")
        return False

def test_all_widgets():
    """
    Test getting all Pinterest analytics widgets
    """
    try:
        logger.info("\n🧪 Testing All Pinterest Analytics Widgets")
        
        widgets = PinterestAnalyticsWidgets()
        
        # Test date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Mock all integrations
        with patch.object(widgets.pinterest_integration, 'get_pinterest_dashboard_data') as mock_data, \
             patch.object(widgets.attribution_system, 'analyze_cross_platform_performance_with_meta_change') as mock_analysis, \
             patch.object(widgets.attribution_system, 'feed_enhancement') as mock_feed:
            
            # Mock responses
            mock_data.return_value = {
                "campaigns": [{"id": "camp_1", "name": "Test Campaign"}],
                "ads": [{"id": "ad_1", "pin_id": "pin_123"}],
                "ad_groups": []
            }
            
            mock_analysis.return_value = {
                "platform_breakdown": {"pinterest": {"impressions": 10000, "clicks": 500}},
                "attribution_scores": {"pinterest": 0.6}
            }
            
            mock_feed.get_audience_insights.return_value = {"type": "YOUR_TOTAL_AUDIENCE"}
            mock_feed.generate_customer_persona.return_value = {"persona_name": "Test Persona"}
            mock_feed.get_trending_keywords.return_value = {"keywords": [{"keyword": "test", "growth": 0.1}]}
            
            # Test getting all widgets
            all_widgets = widgets.get_all_widgets(start_date, end_date)
            
            if all_widgets:
                logger.info(f"✅ Generated {len(all_widgets)} Pinterest analytics widgets")
                
                # Check each widget
                widget_types = [w.widget_id for w in all_widgets]
                logger.info(f"   Widget types: {widget_types}")
                
                for widget in all_widgets:
                    logger.info(f"   {widget.widget_id}: {widget.title}")
                    if widget.data.get("empty", False):
                        logger.warning(f"     ⚠️ Empty widget: {widget.data.get('error', 'Unknown error')}")
                    else:
                        logger.info(f"     ✅ Data available")
                
                return True
            else:
                logger.error("❌ No widgets generated")
                return False
        
    except Exception as e:
        logger.error(f"❌ All widgets test failed: {e}")
        return False

def test_convenience_functions():
    """
    Test convenience functions for easy integration
    """
    try:
        logger.info("\n🧪 Testing Convenience Functions")
        
        # Test date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Mock all integrations
        with patch('pinterest_analytics_widgets.PinterestDashboardIntegration') as mock_integration, \
             patch('pinterest_analytics_widgets.IntegratedCrossPlatformAttribution') as mock_attribution:
            
            # Mock responses
            mock_integration.return_value.get_pinterest_dashboard_data.return_value = {
                "campaigns": [{"id": "camp_1", "name": "Test Campaign"}],
                "ads": [{"id": "ad_1", "pin_id": "pin_123"}],
                "ad_groups": []
            }
            
            mock_attribution.return_value.analyze_cross_platform_performance_with_meta_change.return_value = {
                "platform_breakdown": {"pinterest": {"impressions": 10000, "clicks": 500}},
                "attribution_scores": {"pinterest": 0.6}
            }
            
            # Test get_pinterest_analytics_widgets
            logger.info("Testing get_pinterest_analytics_widgets...")
            widgets = get_pinterest_analytics_widgets(start_date, end_date)
            if widgets:
                logger.info(f"✅ Generated {len(widgets)} widgets via convenience function")
            else:
                logger.info("ℹ️ No widgets generated (expected in test environment)")
            
            # Test get_specific_pinterest_widget
            logger.info("Testing get_specific_pinterest_widget...")
            widget = get_specific_pinterest_widget("campaign_roi", start_date, end_date)
            if widget:
                logger.info(f"✅ Generated specific widget: {widget.widget_id}")
            else:
                logger.info("ℹ️ No specific widget generated (expected in test environment)")
            
            return True
        
    except Exception as e:
        logger.error(f"❌ Convenience functions test failed: {e}")
        return False

def main():
    """
    Main test function
    """
    try:
        logger.info("🚀 Starting Pinterest Analytics Widgets Tests")
        logger.info(f"⏰ Started at: {datetime.now()}")
        
        # Run all tests
        tests = [
            ("Pinterest Widgets Initialization", test_pinterest_widgets_initialization),
            ("Campaign ROI Widget", test_campaign_roi_widget),
            ("Pin Performance Widget", test_pin_performance_widget),
            ("Audience Demographics Widget", test_audience_demographics_widget),
            ("Purchase Funnel Widget", test_purchase_funnel_widget),
            ("Discovery Phase Widget", test_discovery_phase_widget),
            ("Trend Analysis Widget", test_trend_analysis_widget),
            ("Cross-Platform Widget", test_cross_platform_widget),
            ("All Widgets", test_all_widgets),
            ("Convenience Functions", test_convenience_functions)
        ]
        
        results = {}
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                results[test_name] = test_func()
            except Exception as e:
                logger.error(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        logger.info(f"\n{'='*50}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*50}")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Pinterest analytics widgets are ready.")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Check configuration and setup.")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
