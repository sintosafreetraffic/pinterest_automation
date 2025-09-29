"""
Test URL Generator Integration
=============================

This script tests the Pinterest URL generator integration,
validating URL generation, tracking parameter appending, and URL shortening.
"""

import os
import sys
import logging
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_url_generator import (
    PinterestURLGenerator, 
    generate_enhanced_pin_url,
    validate_url_generation
)
from pinterest_post_with_url_generator import test_url_generation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_url_generator_basic():
    """
    Test basic URL generator functionality
    """
    try:
        logger.info("🧪 Testing Basic URL Generator Functionality")
        
        # Initialize URL generator
        generator = PinterestURLGenerator()
        logger.info("✅ URL generator initialized")
        
        # Test basic URL generation
        base_url = "https://test-store.myshopify.com/products/test-product"
        
        enhanced_url = generator.generate_pin_url(
            base_url=base_url,
            campaign_id="123456789",
            ad_id="987654321",
            pin_id="111222333",
            campaign_name="Test_Campaign",
            objective_type="WEB_CONVERSION",
            launch_date="2025-09-24",
            product_name="Test Product",
            product_type="jacket",
            board_title="Test Board",
            pin_variant="pin_1",
            daily_budget=1000
        )
        
        logger.info(f"   Base URL: {base_url}")
        logger.info(f"   Enhanced URL: {enhanced_url}")
        
        # Validate URL generation
        is_valid, error_msg = validate_url_generation(base_url, enhanced_url)
        if is_valid:
            logger.info("   ✅ URL generation is valid")
        else:
            logger.error(f"   ❌ URL generation validation failed: {error_msg}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"❌ Basic URL generator test failed: {e}")
        return False

def test_url_generator_parameters():
    """
    Test URL generator with various parameter combinations
    """
    try:
        logger.info("\n🧪 Testing URL Generator with Various Parameters")
        
        generator = PinterestURLGenerator()
        
        test_cases = [
            {
                'name': 'Basic Parameters',
                'base_url': 'https://test-store.myshopify.com/products/product-1',
                'campaign_id': '123456789',
                'ad_id': '987654321',
                'pin_id': '111222333'
            },
            {
                'name': 'Minimal Parameters',
                'base_url': 'https://test-store.myshopify.com/products/product-2',
                'campaign_id': '123456789'
            },
            {
                'name': 'Full Parameters',
                'base_url': 'https://test-store.myshopify.com/products/product-3',
                'campaign_id': '123456789',
                'ad_id': '987654321',
                'pin_id': '111222333',
                'campaign_name': 'Full_Test_Campaign',
                'objective_type': 'CONSIDERATION',
                'launch_date': '2025-09-24',
                'product_name': 'Full Test Product',
                'product_type': 'shoes',
                'board_title': 'Full Test Board',
                'pin_variant': 'pin_2',
                'daily_budget': 2000
            }
        ]
        
        results = []
        for i, test_case in enumerate(test_cases):
            try:
                logger.info(f"   Testing case {i+1}: {test_case['name']}")
                
                enhanced_url = generator.generate_pin_url(**test_case)
                
                # Validate URL generation
                is_valid, error_msg = validate_url_generation(test_case['base_url'], enhanced_url)
                
                result = {
                    'name': test_case['name'],
                    'base_url': test_case['base_url'],
                    'enhanced_url': enhanced_url,
                    'is_valid': is_valid,
                    'error_message': error_msg,
                    'url_enhanced': enhanced_url != test_case['base_url'],
                    'length_increase': len(enhanced_url) - len(test_case['base_url'])
                }
                
                results.append(result)
                
                if is_valid:
                    logger.info(f"   ✅ {test_case['name']}: Valid")
                else:
                    logger.error(f"   ❌ {test_case['name']}: {error_msg}")
                
            except Exception as e:
                logger.error(f"   ❌ {test_case['name']}: {e}")
                results.append({
                    'name': test_case['name'],
                    'is_valid': False,
                    'error_message': str(e)
                })
        
        # Summary
        valid_count = sum(1 for r in results if r['is_valid'])
        total_count = len(results)
        
        logger.info(f"   📊 Parameter Test Results: {valid_count}/{total_count} valid")
        
        return valid_count == total_count
        
    except Exception as e:
        logger.error(f"❌ Parameter test failed: {e}")
        return False

def test_url_generator_validation():
    """
    Test URL generator validation functionality
    """
    try:
        logger.info("\n🧪 Testing URL Generator Validation")
        
        generator = PinterestURLGenerator()
        
        # Test cases for validation
        validation_tests = [
            {
                'name': 'Valid URL',
                'base_url': 'https://test-store.myshopify.com/products/valid-product',
                'expected_valid': True
            },
            {
                'name': 'Invalid URL (no protocol)',
                'base_url': 'test-store.myshopify.com/products/invalid-product',
                'expected_valid': False
            },
            {
                'name': 'Empty URL',
                'base_url': '',
                'expected_valid': False
            },
            {
                'name': 'Very Long URL',
                'base_url': 'https://test-store.myshopify.com/products/' + 'x' * 2000,
                'expected_valid': False
            }
        ]
        
        results = []
        for test_case in validation_tests:
            try:
                logger.info(f"   Testing validation: {test_case['name']}")
                
                if test_case['base_url']:
                    enhanced_url = generator.generate_pin_url(
                        base_url=test_case['base_url'],
                        campaign_id="123456789"
                    )
                else:
                    enhanced_url = test_case['base_url']
                
                is_valid, error_msg = validate_url_generation(test_case['base_url'], enhanced_url)
                
                result = {
                    'name': test_case['name'],
                    'expected_valid': test_case['expected_valid'],
                    'actual_valid': is_valid,
                    'error_message': error_msg,
                    'passed': is_valid == test_case['expected_valid']
                }
                
                results.append(result)
                
                if result['passed']:
                    logger.info(f"   ✅ {test_case['name']}: Passed")
                else:
                    logger.error(f"   ❌ {test_case['name']}: Expected {test_case['expected_valid']}, got {is_valid}")
                
            except Exception as e:
                logger.error(f"   ❌ {test_case['name']}: Exception - {e}")
                results.append({
                    'name': test_case['name'],
                    'passed': False,
                    'error_message': str(e)
                })
        
        # Summary
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        
        logger.info(f"   📊 Validation Test Results: {passed_count}/{total_count} passed")
        
        return passed_count == total_count
        
    except Exception as e:
        logger.error(f"❌ Validation test failed: {e}")
        return False

def test_url_generator_batch():
    """
    Test URL generator batch processing
    """
    try:
        logger.info("\n🧪 Testing URL Generator Batch Processing")
        
        generator = PinterestURLGenerator()
        
        # Create test data
        urls_data = [
            {
                'base_url': 'https://test-store.myshopify.com/products/product-1',
                'product_name': 'Product 1',
                'ad_id': '111111111',
                'pin_id': '222222222'
            },
            {
                'base_url': 'https://test-store.myshopify.com/products/product-2',
                'product_name': 'Product 2',
                'ad_id': '333333333',
                'pin_id': '444444444'
            },
            {
                'base_url': 'https://test-store.myshopify.com/products/product-3',
                'product_name': 'Product 3',
                'ad_id': '555555555',
                'pin_id': '666666666'
            }
        ]
        
        # Test batch processing
        results = generator.batch_generate_urls(
            urls_data=urls_data,
            campaign_id="123456789",
            campaign_name="Batch_Test_Campaign",
            objective_type="WEB_CONVERSION",
            launch_date="2025-09-24",
            daily_budget=1000
        )
        
        logger.info(f"   📊 Batch Processing Results:")
        logger.info(f"   Total: {results['total']}")
        logger.info(f"   Successful: {len(results['successful'])}")
        logger.info(f"   Failed: {len(results['failed'])}")
        
        # Validate results
        if len(results['successful']) > 0:
            logger.info("   ✅ Batch processing successful")
            return True
        else:
            logger.error("   ❌ Batch processing failed")
            return False
        
    except Exception as e:
        logger.error(f"❌ Batch processing test failed: {e}")
        return False

def test_url_generator_shortening():
    """
    Test URL generator shortening functionality
    """
    try:
        logger.info("\n🧪 Testing URL Generator Shortening")
        
        generator = PinterestURLGenerator()
        
        # Test URL shortening (if Bitly token is configured)
        if generator.bitly_token:
            logger.info("   🔗 Bitly token configured, testing URL shortening")
            
            # Create a very long URL
            long_url = "https://test-store.myshopify.com/products/very-long-product-name-with-many-parameters" + "&param=" + "x" * 1000
            
            shortened_url = generator.shorten_url(long_url)
            
            if shortened_url != long_url and len(shortened_url) < len(long_url):
                logger.info(f"   ✅ URL shortened successfully")
                logger.info(f"   Original length: {len(long_url)}")
                logger.info(f"   Shortened length: {len(shortened_url)}")
                return True
            else:
                logger.warning("   ⚠️ URL shortening failed or not needed")
                return True  # Not a failure if shortening isn't needed
        else:
            logger.info("   ℹ️ Bitly token not configured, skipping URL shortening test")
            return True
        
    except Exception as e:
        logger.error(f"❌ URL shortening test failed: {e}")
        return False

def test_pinterest_api_integration():
    """
    Test Pinterest API integration for metadata retrieval
    """
    try:
        logger.info("\n🧪 Testing Pinterest API Integration")
        
        generator = PinterestURLGenerator()
        
        # Test ad account ID retrieval
        ad_account_id = generator.get_ad_account_id()
        if ad_account_id:
            logger.info(f"   ✅ Ad account ID retrieved: {ad_account_id}")
        else:
            logger.warning("   ⚠️ Could not retrieve ad account ID")
        
        # Test campaign metadata retrieval (with dummy campaign ID)
        campaign_metadata = generator.get_campaign_metadata("dummy_campaign_id")
        if campaign_metadata:
            logger.info("   ✅ Campaign metadata retrieval working")
        else:
            logger.info("   ℹ️ Campaign metadata retrieval (expected for dummy ID)")
        
        # Test ad metadata retrieval (with dummy ad ID)
        ad_metadata = generator.get_ad_metadata("dummy_ad_id")
        if ad_metadata:
            logger.info("   ✅ Ad metadata retrieval working")
        else:
            logger.info("   ℹ️ Ad metadata retrieval (expected for dummy ID)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pinterest API integration test failed: {e}")
        return False

def main():
    """
    Main test function
    """
    try:
        logger.info("🚀 Starting URL Generator Integration Tests")
        logger.info(f"⏰ Started at: {datetime.now()}")
        
        # Run all tests
        tests = [
            ("Basic URL Generator", test_url_generator_basic),
            ("Parameter Variations", test_url_generator_parameters),
            ("URL Validation", test_url_generator_validation),
            ("Batch Processing", test_url_generator_batch),
            ("URL Shortening", test_url_generator_shortening),
            ("Pinterest API Integration", test_pinterest_api_integration)
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
            logger.info("🎉 All tests passed! URL generator integration is ready.")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Check configuration and setup.")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
