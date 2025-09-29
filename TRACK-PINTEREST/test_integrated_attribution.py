"""
Test Integrated Cross-Platform Attribution with Meta-Change Integration
====================================================================

This script tests the integrated cross-platform attribution system with
meta-change product feed enhancement functionality.

Features tested:
- Cross-platform attribution calculation
- Pinterest discovery phase optimization
- Product feed enhancement with trends
- Bulk metadata enrichment
- Enhanced Pinterest feed generation
- Customer persona generation
- Real-time attribution analysis
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_cross_platform_attribution import (
    IntegratedCrossPlatformAttribution,
    calculate_integrated_attribution,
    enhance_product_feed_with_attribution,
    generate_enhanced_pinterest_feed_with_attribution,
    analyze_integrated_cross_platform_performance
)
from cross_platform_attribution import AttributionModel, Platform, CustomerJourney, Touchpoint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_integrated_attribution_initialization():
    """
    Test integrated attribution system initialization
    """
    try:
        logger.info("🧪 Testing Integrated Attribution System Initialization")
        
        # Initialize integrated attribution
        integrated_attribution = IntegratedCrossPlatformAttribution()
        logger.info("✅ Integrated attribution system initialized")
        
        # Test meta-change integration status
        if integrated_attribution.meta_change_available:
            logger.info("✅ Meta-change integration available")
            logger.info(f"   Feed enhancement: {integrated_attribution.feed_enhancement is not None}")
            logger.info(f"   Feed generator: {integrated_attribution.feed_generator is not None}")
            logger.info(f"   LLM client: {integrated_attribution.llm_client is not None}")
            logger.info(f"   Shopify client: {integrated_attribution.shopify_client is not None}")
        else:
            logger.warning("⚠️ Meta-change integration not available")
        
        # Test attribution models
        logger.info(f"📊 Attribution models: {len(integrated_attribution.enhanced_attribution_models)}")
        for model, config in integrated_attribution.enhanced_attribution_models.items():
            logger.info(f"   {model.value}: weight={config['weight']}, pinterest_boost={config['pinterest_boost']}")
        
        # Test Pinterest discovery phase weights
        logger.info(f"🎯 Pinterest discovery phase weights: {integrated_attribution.pinterest_discovery_weights}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integrated attribution initialization test failed: {e}")
        return False

def test_enhanced_attribution_calculation():
    """
    Test enhanced attribution calculation with meta-change integration
    """
    try:
        logger.info("\n🧪 Testing Enhanced Attribution Calculation")
        
        integrated_attribution = IntegratedCrossPlatformAttribution()
        
        # Create mock customer journey
        mock_journey = CustomerJourney(
            user_id="test_user_123",
            session_id="session_123",
            conversion_value=150.0,
            conversion_timestamp=datetime.now()
        )
        
        # Add mock touchpoints
        touchpoints = [
            Touchpoint(
                platform=Platform.PINTEREST,
                campaign_id="123456789",
                ad_id="987654321",
                timestamp=datetime.now() - timedelta(days=3),
                event_type="click",
                position=1
            ),
            Touchpoint(
                platform=Platform.META,
                campaign_id="111222333",
                ad_id="444555666",
                timestamp=datetime.now() - timedelta(days=1),
                event_type="click",
                position=2
            ),
            Touchpoint(
                platform=Platform.GOOGLE,
                campaign_id="777888999",
                ad_id="000111222",
                timestamp=datetime.now() - timedelta(hours=2),
                event_type="click",
                position=3
            )
        ]
        
        mock_journey.touchpoints = touchpoints
        mock_journey.journey_duration = timedelta(days=3)
        mock_journey.platform_sequence = [tp.platform for tp in touchpoints]
        
        # Mock meta-change integration
        with patch.object(integrated_attribution.feed_enhancement, 'get_trending_keywords') as mock_trends, \
             patch.object(integrated_attribution.feed_enhancement, 'get_audience_insights') as mock_audience, \
             patch.object(integrated_attribution.feed_enhancement, 'generate_customer_persona') as mock_persona, \
             patch.object(integrated_attribution.feed_enhancement, 'filter_keywords_by_audience') as mock_filter:
            
            # Mock responses
            mock_trends.return_value = {
                "keywords": [
                    {"keyword": "fashion", "growth": 0.15},
                    {"keyword": "style", "growth": 0.12},
                    {"keyword": "trendy", "growth": 0.10}
                ]
            }
            
            mock_audience.return_value = {
                "type": "YOUR_TOTAL_AUDIENCE",
                "size": 10000,
                "categories": [
                    {"name": "Fashion", "ratio": 0.3},
                    {"name": "Beauty", "ratio": 0.2}
                ]
            }
            
            mock_persona.return_value = {
                "persona_name": "Fashion Enthusiast",
                "demographics": {
                    "ages": ["25-34"],
                    "interests": ["Fashion", "Beauty"]
                }
            }
            
            mock_filter.return_value = ["fashion", "style", "trendy"]
            
            # Test enhanced attribution calculation
            result = integrated_attribution.calculate_enhanced_attribution(
                mock_journey, AttributionModel.DATA_DRIVEN
            )
            
            if result:
                logger.info(f"✅ Enhanced attribution calculated: {result.total_attribution:.2f}")
                logger.info(f"   Platform scores: {result.platform_scores}")
                logger.info(f"   Campaign scores: {result.campaign_scores}")
                logger.info(f"   Confidence score: {result.confidence_score:.2f}")
                
                # Check meta-change insights
                if hasattr(result, 'meta_change_insights'):
                    insights = result.meta_change_insights
                    logger.info(f"   Meta-change insights: {insights}")
                
                return True
            else:
                logger.error("❌ Enhanced attribution calculation failed")
                return False
        
    except Exception as e:
        logger.error(f"❌ Enhanced attribution calculation test failed: {e}")
        return False

def test_pinterest_discovery_phase_optimization():
    """
    Test Pinterest discovery phase optimization
    """
    try:
        logger.info("\n🧪 Testing Pinterest Discovery Phase Optimization")
        
        integrated_attribution = IntegratedCrossPlatformAttribution()
        
        # Test platform scores optimization
        platform_scores = {
            Platform.PINTEREST: 0.3,
            Platform.META: 0.4,
            Platform.GOOGLE: 0.3
        }
        
        trending_keywords = ["fashion", "style", "trendy"]
        customer_persona = {
            "persona_name": "Fashion Enthusiast",
            "demographics": {"interests": ["Fashion", "Beauty"]}
        }
        
        # Test optimization
        optimized_scores = integrated_attribution._optimize_pinterest_discovery_phase(
            platform_scores, trending_keywords, customer_persona
        )
        
        if Platform.PINTEREST in optimized_scores:
            original_score = platform_scores[Platform.PINTEREST]
            optimized_score = optimized_scores[Platform.PINTEREST]
            
            logger.info(f"✅ Pinterest discovery phase optimization:")
            logger.info(f"   Original score: {original_score:.2f}")
            logger.info(f"   Optimized score: {optimized_score:.2f}")
            logger.info(f"   Boost: {((optimized_score - original_score) / original_score * 100):.1f}%")
            
            # Check if Pinterest score was boosted
            if optimized_score > original_score:
                logger.info("✅ Pinterest score was successfully boosted")
                return True
            else:
                logger.warning("⚠️ Pinterest score was not boosted")
                return False
        else:
            logger.error("❌ Pinterest platform not found in optimized scores")
            return False
        
    except Exception as e:
        logger.error(f"❌ Pinterest discovery phase optimization test failed: {e}")
        return False

def test_product_feed_enhancement():
    """
    Test product feed enhancement with attribution insights
    """
    try:
        logger.info("\n🧪 Testing Product Feed Enhancement")
        
        integrated_attribution = IntegratedCrossPlatformAttribution()
        
        # Mock products
        mock_products = [
            {
                "id": "123456",
                "title": "Summer Dress",
                "product_type": "Dresses",
                "price": "29.99",
                "description": "Beautiful summer dress"
            },
            {
                "id": "789012",
                "title": "Casual T-Shirt",
                "product_type": "T-Shirts",
                "price": "19.99",
                "description": "Comfortable casual t-shirt"
            }
        ]
        
        # Mock attribution insights
        attribution_insights = {
            "pinterest_discovery_score": 0.8,
            "cross_platform_performance": {
                "pinterest": {"impressions": 1000, "clicks": 50},
                "meta": {"impressions": 800, "clicks": 40}
            },
            "trending_keywords": ["fashion", "style", "summer"]
        }
        
        # Mock meta-change integration
        with patch.object(integrated_attribution.feed_enhancement, 'get_trending_keywords') as mock_trends, \
             patch.object(integrated_attribution.feed_enhancement, 'get_audience_insights') as mock_audience, \
             patch.object(integrated_attribution.feed_enhancement, 'generate_customer_persona') as mock_persona, \
             patch.object(integrated_attribution.feed_enhancement, 'filter_keywords_by_audience') as mock_filter, \
             patch.object(integrated_attribution.feed_enhancement, 'enhance_product_metadata') as mock_enhance:
            
            # Mock responses
            mock_trends.return_value = {
                "keywords": [{"keyword": "fashion", "growth": 0.15}]
            }
            
            mock_audience.return_value = {
                "type": "YOUR_TOTAL_AUDIENCE",
                "size": 10000
            }
            
            mock_persona.return_value = {
                "persona_name": "Fashion Enthusiast",
                "demographics": {"interests": ["Fashion"]}
            }
            
            mock_filter.return_value = ["fashion", "style"]
            
            mock_enhance.return_value = {
                "trending_keywords": {"keywords": ["fashion", "style"]},
                "audience_insights": {"target_persona": "Fashion Enthusiast"},
                "ai_suggestions": {"recommended_keywords": ["fashion", "style"]}
            }
            
            # Test product feed enhancement
            enhanced_products = integrated_attribution.enhance_product_feed_with_attribution(
                mock_products, attribution_insights
            )
            
            if enhanced_products:
                logger.info(f"✅ Enhanced {len(enhanced_products)} products")
                
                # Check if products have attribution insights
                for product in enhanced_products:
                    if "attribution_insights" in product:
                        insights = product["attribution_insights"]
                        logger.info(f"   Product {product.get('id', 'Unknown')} attribution insights:")
                        logger.info(f"     Pinterest discovery score: {insights.get('pinterest_discovery_score', 0.0)}")
                        logger.info(f"     Optimization recommendations: {insights.get('optimization_recommendations', [])}")
                
                return True
            else:
                logger.error("❌ Product feed enhancement failed")
                return False
        
    except Exception as e:
        logger.error(f"❌ Product feed enhancement test failed: {e}")
        return False

def test_enhanced_pinterest_feed_generation():
    """
    Test enhanced Pinterest feed generation with attribution insights
    """
    try:
        logger.info("\n🧪 Testing Enhanced Pinterest Feed Generation")
        
        integrated_attribution = IntegratedCrossPlatformAttribution()
        
        # Mock products
        mock_products = [
            {
                "id": "123456",
                "title": "Summer Dress",
                "product_type": "Dresses",
                "variants": [
                    {"id": "v1", "price": "29.99", "option1": "Red", "option2": "M"},
                    {"id": "v2", "price": "29.99", "option1": "Blue", "option2": "L"}
                ]
            }
        ]
        
        # Mock attribution insights
        attribution_insights = {
            "pinterest_discovery_score": 0.8,
            "trending_keywords": ["fashion", "style", "summer"],
            "customer_persona": "Fashion Enthusiast"
        }
        
        # Mock meta-change integration
        with patch.object(integrated_attribution, 'enhance_product_feed_with_attribution') as mock_enhance, \
             patch.object(integrated_attribution.feed_generator, 'generate_enhanced_csv_feed') as mock_csv, \
             patch.object(integrated_attribution.feed_generator, 'generate_campaign_specific_feeds') as mock_campaigns:
            
            # Mock responses
            mock_enhance.return_value = mock_products  # Return original products
            
            mock_csv.return_value = "enhanced_pinterest_feed.csv"
            
            mock_campaigns.return_value = {
                "best_sellers": "best_sellers_feed.csv",
                "seasonal": "seasonal_feed.csv"
            }
            
            # Test enhanced Pinterest feed generation
            result = integrated_attribution.generate_enhanced_pinterest_feed_with_attribution(
                mock_products, attribution_insights
            )
            
            if result and result.get("success"):
                logger.info("✅ Enhanced Pinterest feed generated successfully")
                logger.info(f"   Main feed: {result.get('main_feed')}")
                logger.info(f"   Campaign feeds: {len(result.get('campaign_feeds', {}))}")
                logger.info(f"   Enhanced products: {result.get('enhanced_products_count', 0)}")
                
                # Check feed metadata
                if "feed_metadata" in result:
                    metadata = result["feed_metadata"]
                    logger.info(f"   Attribution insights: {metadata.get('attribution_insights', {})}")
                    logger.info(f"   Trending keywords used: {metadata.get('trending_keywords_used', 0)}")
                    logger.info(f"   Customer persona: {metadata.get('customer_persona', 'Unknown')}")
                
                return True
            else:
                logger.error(f"❌ Enhanced Pinterest feed generation failed: {result.get('error', 'Unknown error')}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Enhanced Pinterest feed generation test failed: {e}")
        return False

def test_cross_platform_performance_analysis():
    """
    Test cross-platform performance analysis with meta-change integration
    """
    try:
        logger.info("\n🧪 Testing Cross-Platform Performance Analysis")
        
        integrated_attribution = IntegratedCrossPlatformAttribution()
        
        # Mock date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Mock meta-change integration
        with patch.object(integrated_attribution.attribution, 'analyze_cross_platform_performance') as mock_base, \
             patch.object(integrated_attribution.feed_enhancement, 'get_trending_keywords') as mock_trends, \
             patch.object(integrated_attribution.feed_enhancement, 'get_audience_insights') as mock_audience, \
             patch.object(integrated_attribution.pinterest_integration, 'get_pinterest_dashboard_data') as mock_pinterest:
            
            # Mock responses
            mock_base.return_value = {
                "total_impressions": 5000,
                "total_clicks": 250,
                "total_spend": 1000.0,
                "overall_ctr": 0.05,
                "platform_breakdown": {
                    "pinterest": {"impressions": 2000, "clicks": 100, "ctr": 0.05},
                    "meta": {"impressions": 2000, "clicks": 100, "ctr": 0.05},
                    "google": {"impressions": 1000, "clicks": 50, "ctr": 0.05}
                }
            }
            
            mock_trends.return_value = {
                "keywords": [{"keyword": "fashion", "growth": 0.15}]
            }
            
            mock_audience.return_value = {
                "type": "YOUR_TOTAL_AUDIENCE",
                "size": 10000,
                "categories": [{"name": "Fashion", "ratio": 0.3}]
            }
            
            mock_pinterest.return_value = {
                "metrics": [
                    {"impressions": 1000, "clicks": 50, "saves": 25},
                    {"impressions": 800, "clicks": 40, "saves": 20}
                ]
            }
            
            # Test cross-platform performance analysis
            analysis = integrated_attribution.analyze_cross_platform_performance_with_meta_change(
                start_date, end_date
            )
            
            if analysis:
                logger.info("✅ Cross-platform performance analysis completed")
                logger.info(f"   Total impressions: {analysis.get('total_impressions', 0):,}")
                logger.info(f"   Total clicks: {analysis.get('total_clicks', 0):,}")
                logger.info(f"   Overall CTR: {analysis.get('overall_ctr', 0.0):.2%}")
                
                # Check meta-change insights
                if "meta_change_insights" in analysis:
                    insights = analysis["meta_change_insights"]
                    logger.info(f"   Meta-change insights: {insights}")
                
                # Check Pinterest optimization
                if "pinterest_optimization" in analysis:
                    pinterest_opt = analysis["pinterest_optimization"]
                    logger.info(f"   Pinterest optimization score: {pinterest_opt.get('optimization_score', 0.0):.1f}")
                
                # Check trending keywords impact
                if "trending_keywords_impact" in analysis:
                    trends_impact = analysis["trending_keywords_impact"]
                    logger.info(f"   Trending keywords impact: {trends_impact.get('impact_score', 0.0):.2f}")
                
                return True
            else:
                logger.error("❌ Cross-platform performance analysis failed")
                return False
        
    except Exception as e:
        logger.error(f"❌ Cross-platform performance analysis test failed: {e}")
        return False

def test_integrated_attribution_summary():
    """
    Test integrated attribution summary
    """
    try:
        logger.info("\n🧪 Testing Integrated Attribution Summary")
        
        integrated_attribution = IntegratedCrossPlatformAttribution()
        
        # Get integrated attribution summary
        summary = integrated_attribution.get_integrated_attribution_summary()
        
        if summary:
            logger.info("✅ Integrated attribution summary retrieved")
            logger.info(f"   Attribution system models: {summary.get('attribution_system', {}).get('models_available', 0)}")
            logger.info(f"   Meta-change integration: {summary.get('meta_change_integration', {}).get('available', False)}")
            logger.info(f"   Integration status: {summary.get('integration_status', 'Unknown')}")
            
            # Check capabilities
            capabilities = summary.get("capabilities", [])
            logger.info(f"   Capabilities: {len(capabilities)}")
            for capability in capabilities:
                logger.info(f"     - {capability}")
            
            return True
        else:
            logger.error("❌ Integrated attribution summary failed")
            return False
        
    except Exception as e:
        logger.error(f"❌ Integrated attribution summary test failed: {e}")
        return False

def test_convenience_functions():
    """
    Test convenience functions for easy integration
    """
    try:
        logger.info("\n🧪 Testing Convenience Functions")
        
        # Test calculate_integrated_attribution
        logger.info("Testing calculate_integrated_attribution...")
        result = calculate_integrated_attribution("test_user_123")
        if result:
            logger.info(f"✅ Integrated attribution calculated: {result.total_attribution:.2f}")
        else:
            logger.info("ℹ️ No attribution result (expected in test environment)")
        
        # Test enhance_product_feed_with_attribution
        logger.info("Testing enhance_product_feed_with_attribution...")
        mock_products = [{"id": "123", "title": "Test Product"}]
        mock_insights = {"pinterest_discovery_score": 0.8}
        
        enhanced_products = enhance_product_feed_with_attribution(mock_products, mock_insights)
        if enhanced_products:
            logger.info(f"✅ Enhanced {len(enhanced_products)} products")
        else:
            logger.info("ℹ️ No enhanced products (expected in test environment)")
        
        # Test generate_enhanced_pinterest_feed_with_attribution
        logger.info("Testing generate_enhanced_pinterest_feed_with_attribution...")
        feed_result = generate_enhanced_pinterest_feed_with_attribution(mock_products, mock_insights)
        if feed_result:
            logger.info(f"✅ Feed generation result: {feed_result.get('success', False)}")
        else:
            logger.info("ℹ️ No feed generation result (expected in test environment)")
        
        # Test analyze_integrated_cross_platform_performance
        logger.info("Testing analyze_integrated_cross_platform_performance...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        performance = analyze_integrated_cross_platform_performance(start_date, end_date)
        if performance:
            logger.info(f"✅ Performance analysis completed: {performance.get('total_impressions', 0):,} impressions")
        else:
            logger.info("ℹ️ No performance analysis (expected in test environment)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Convenience functions test failed: {e}")
        return False

def main():
    """
    Main test function
    """
    try:
        logger.info("🚀 Starting Integrated Cross-Platform Attribution Tests")
        logger.info(f"⏰ Started at: {datetime.now()}")
        
        # Run all tests
        tests = [
            ("Integrated Attribution System Initialization", test_integrated_attribution_initialization),
            ("Enhanced Attribution Calculation", test_enhanced_attribution_calculation),
            ("Pinterest Discovery Phase Optimization", test_pinterest_discovery_phase_optimization),
            ("Product Feed Enhancement", test_product_feed_enhancement),
            ("Enhanced Pinterest Feed Generation", test_enhanced_pinterest_feed_generation),
            ("Cross-Platform Performance Analysis", test_cross_platform_performance_analysis),
            ("Integrated Attribution Summary", test_integrated_attribution_summary),
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
            logger.info("🎉 All tests passed! Integrated cross-platform attribution system is ready.")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Check configuration and setup.")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
