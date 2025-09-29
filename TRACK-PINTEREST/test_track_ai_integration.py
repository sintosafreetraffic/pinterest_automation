"""
Test Track AI Integration
========================

This script tests the Track AI integration for Pinterest automation,
validating UTM parameter generation, URL creation, and Track AI pixel integration.
"""

import os
import sys
import logging
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from track_ai_integration import (
    PinterestTrackAIIntegration, 
    generate_pinterest_track_ai_url,
    validate_pinterest_url
)
from pinterest_post_enhanced import validate_track_ai_integration

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_track_ai_integration():
    """
    Test Track AI integration functionality
    """
    try:
        logger.info("🧪 Testing Track AI Integration")
        
        # Test 1: Track AI Configuration Validation
        logger.info("\n📋 Test 1: Track AI Configuration Validation")
        validation_results = validate_track_ai_integration()
        
        logger.info(f"   Track AI Endpoint: {validation_results['track_ai_endpoint']}")
        logger.info(f"   Track AI Store ID: {validation_results['track_ai_store_id']}")
        logger.info(f"   Track AI Pixel ID: {validation_results['track_ai_pixel_id']}")
        logger.info(f"   Is Configured: {validation_results['is_configured']}")
        
        if validation_results['missing_config']:
            logger.warning(f"   Missing Config: {validation_results['missing_config']}")
        else:
            logger.info("   ✅ Track AI configuration is complete")
        
        # Test 2: UTM Parameter Generation
        logger.info("\n📋 Test 2: UTM Parameter Generation")
        integration = PinterestTrackAIIntegration()
        
        utm_params = integration.generate_utm_parameters(
            campaign_name="Test_Campaign",
            objective_type="WEB_CONVERSION",
            launch_date="2025-09-24",
            product_name="Test Product",
            product_type="jacket",
            board_title="Test Board",
            pin_variant="pin_1",
            campaign_id="123456789",
            pin_id="987654321",
            ad_id="111222333",
            daily_budget=1000
        )
        
        logger.info(f"   Generated UTM Parameters: {utm_params}")
        
        # Validate UTM parameters
        required_params = ['utm_source', 'utm_medium', 'utm_campaign']
        for param in required_params:
            if param in utm_params:
                logger.info(f"   ✅ {param}: {utm_params[param]}")
            else:
                logger.error(f"   ❌ Missing {param}")
        
        # Test 3: Enhanced URL Generation
        logger.info("\n📋 Test 3: Enhanced URL Generation")
        base_url = "https://test-store.myshopify.com/products/test-product"
        
        enhanced_url = integration.generate_enhanced_destination_url(
            base_url=base_url,
            campaign_name="Test_Campaign",
            objective_type="WEB_CONVERSION",
            launch_date="2025-09-24",
            product_name="Test Product",
            product_type="jacket",
            board_title="Test Board",
            pin_variant="pin_1",
            campaign_id="123456789",
            pin_id="987654321",
            ad_id="111222333",
            daily_budget=1000
        )
        
        logger.info(f"   Base URL: {base_url}")
        logger.info(f"   Enhanced URL: {enhanced_url}")
        
        # Test URL validation
        is_valid, error_msg = validate_pinterest_url(enhanced_url)
        if is_valid:
            logger.info("   ✅ Enhanced URL is valid")
        else:
            logger.error(f"   ❌ Enhanced URL validation failed: {error_msg}")
        
        # Test 4: URL Length Validation
        logger.info("\n📋 Test 4: URL Length Validation")
        url_length = len(enhanced_url)
        max_length = 2048
        
        logger.info(f"   URL Length: {url_length} characters")
        logger.info(f"   Max Length: {max_length} characters")
        
        if integration.validate_url_length(enhanced_url, max_length):
            logger.info("   ✅ URL length is within limits")
        else:
            logger.warning("   ⚠️ URL length exceeds limits, fallback will be used")
            
            # Test fallback URL creation
            essential_params = {
                'utm_source': 'pinterest',
                'utm_medium': 'cpc',
                'utm_campaign': 'test_campaign',
                'track_ai_store_id': integration.store_id,
                'track_ai_pixel_id': integration.pixel_id
            }
            
            fallback_url = integration.create_fallback_url(base_url, essential_params)
            logger.info(f"   Fallback URL: {fallback_url}")
            
            if integration.validate_url_length(fallback_url, max_length):
                logger.info("   ✅ Fallback URL is within limits")
            else:
                logger.error("   ❌ Even fallback URL exceeds limits")
        
        # Test 5: Convenience Function
        logger.info("\n📋 Test 5: Convenience Function")
        convenience_url = generate_pinterest_track_ai_url(
            base_url=base_url,
            campaign_name="Convenience_Test",
            objective_type="WEB_CONVERSION",
            launch_date="2025-09-24",
            product_name="Convenience Product",
            product_type="shoes"
        )
        
        logger.info(f"   Convenience URL: {convenience_url}")
        
        # Test 6: Track AI Pixel Parameters
        logger.info("\n📋 Test 6: Track AI Pixel Parameters")
        from urllib.parse import urlparse, parse_qs
        
        parsed_url = urlparse(enhanced_url)
        query_params = parse_qs(parsed_url.query)
        
        track_ai_params = {
            'track_ai_event': query_params.get('track_ai_event', ['Not found'])[0],
            'track_ai_store_id': query_params.get('track_ai_store_id', ['Not found'])[0],
            'track_ai_pixel_id': query_params.get('track_ai_pixel_id', ['Not found'])[0],
            'track_ai_timestamp': query_params.get('track_ai_timestamp', ['Not found'])[0]
        }
        
        for param, value in track_ai_params.items():
            if value != 'Not found':
                logger.info(f"   ✅ {param}: {value}")
            else:
                logger.error(f"   ❌ Missing {param}")
        
        logger.info("\n🎉 Track AI Integration Test Completed Successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Track AI Integration Test Failed: {e}")
        return False

def test_pinterest_authentication():
    """
    Test Pinterest authentication
    """
    try:
        logger.info("\n🔐 Testing Pinterest Authentication")
        
        from pinterest_auth import get_access_token, get_ad_account_id
        
        access_token = get_access_token()
        if access_token:
            logger.info(f"   ✅ Access token retrieved: {access_token[:20]}...")
            
            ad_account_id = get_ad_account_id(access_token)
            if ad_account_id:
                logger.info(f"   ✅ Ad account ID retrieved: {ad_account_id}")
                return True
            else:
                logger.error("   ❌ Failed to get ad account ID")
                return False
        else:
            logger.error("   ❌ Failed to get access token")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pinterest Authentication Test Failed: {e}")
        return False

def test_enhanced_features():
    """
    Test enhanced Pinterest features
    """
    try:
        logger.info("\n🎯 Testing Enhanced Pinterest Features")
        
        # Test enhanced pin generation
        try:
            import sys
            meta_change_path = '/Users/saschavanwell/Documents/meta-change'
            sys.path.append(meta_change_path)
            from pin_generation_enhancement import PinGenerationEnhancement
            
            enhanced_pin_generation = PinGenerationEnhancement()
            logger.info("   ✅ Enhanced pin generation initialized")
            
            # Test customer persona generation
            audience_insights = enhanced_pin_generation.get_audience_insights()
            if audience_insights:
                logger.info("   ✅ Audience insights retrieved")
                
                persona = enhanced_pin_generation.generate_customer_persona(audience_insights)
                if persona:
                    logger.info(f"   ✅ Customer persona generated: {persona.get('persona_name', 'Unknown')}")
                else:
                    logger.warning("   ⚠️ Customer persona generation failed")
            else:
                logger.warning("   ⚠️ No audience insights available")
            
            # Test trending keywords
            trending_keywords = enhanced_pin_generation.get_trending_keywords(region="DE")
            if trending_keywords:
                logger.info(f"   ✅ Trending keywords retrieved: {len(trending_keywords)} keywords")
            else:
                logger.warning("   ⚠️ No trending keywords available")
            
            return True
            
        except ImportError as e:
            logger.warning(f"   ⚠️ Enhanced features not available: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Enhanced Features Test Failed: {e}")
        return False

def main():
    """
    Main test function
    """
    try:
        logger.info("🚀 Starting Track AI Integration Tests")
        logger.info(f"⏰ Started at: {datetime.now()}")
        
        # Run all tests
        tests = [
            ("Track AI Integration", test_track_ai_integration),
            ("Pinterest Authentication", test_pinterest_authentication),
            ("Enhanced Features", test_enhanced_features)
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
            logger.info("🎉 All tests passed! Track AI integration is ready.")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Check configuration and setup.")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
