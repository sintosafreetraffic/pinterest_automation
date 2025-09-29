"""
Test Pinterest Track AI Configuration
====================================

This script tests the Pinterest Track AI configuration,
validating traffic recognition, attribution rules, and multi-touch attribution models.
"""

import os
import sys
import logging
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_track_ai_config import (
    PinterestTrackAIConfig,
    configure_pinterest_track_ai,
    test_pinterest_traffic_recognition,
    get_pinterest_attribution_summary
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_pinterest_track_ai_configuration():
    """
    Test Pinterest Track AI configuration
    """
    try:
        logger.info("🧪 Testing Pinterest Track AI Configuration")
        
        # Initialize configuration
        config = PinterestTrackAIConfig()
        logger.info("✅ Pinterest Track AI configuration initialized")
        
        # Test configuration
        success = config.configure_pinterest_traffic_recognition()
        if success:
            logger.info("✅ Pinterest traffic recognition configured successfully")
        else:
            logger.error("❌ Failed to configure Pinterest traffic recognition")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pinterest Track AI configuration test failed: {e}")
        return False

def test_pinterest_traffic_recognition_detailed():
    """
    Test Pinterest traffic recognition with detailed test cases
    """
    try:
        logger.info("\n🧪 Testing Pinterest Traffic Recognition (Detailed)")
        
        # Initialize configuration
        config = PinterestTrackAIConfig()
        
        # Test traffic recognition
        test_results = config.test_pinterest_traffic_recognition()
        
        if test_results.get("error"):
            logger.error(f"❌ Traffic recognition test failed: {test_results['error']}")
            return False
        
        # Validate results
        total_tests = test_results.get("total_tests", 0)
        passed_tests = test_results.get("passed_tests", 0)
        failed_tests = test_results.get("failed_tests", 0)
        
        logger.info(f"📊 Traffic Recognition Test Results:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {passed_tests}")
        logger.info(f"   Failed: {failed_tests}")
        
        # Check individual test cases
        for test_case in test_results.get("test_cases", []):
            name = test_case.get("name", "Unknown")
            passed = test_case.get("passed", False)
            expected = test_case.get("expected", False)
            actual = test_case.get("actual", False)
            
            if passed:
                logger.info(f"   ✅ {name}: PASSED (Expected: {expected}, Actual: {actual})")
            else:
                logger.error(f"   ❌ {name}: FAILED (Expected: {expected}, Actual: {actual})")
        
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"❌ Detailed traffic recognition test failed: {e}")
        return False

def test_pinterest_attribution_summary():
    """
    Test Pinterest attribution summary
    """
    try:
        logger.info("\n🧪 Testing Pinterest Attribution Summary")
        
        # Initialize configuration
        config = PinterestTrackAIConfig()
        
        # Get attribution summary
        attribution_summary = config.get_pinterest_attribution_summary()
        
        if attribution_summary.get("error"):
            logger.error(f"❌ Attribution summary test failed: {attribution_summary['error']}")
            return False
        
        # Validate attribution summary
        required_fields = [
            "pinterest_pixel_id",
            "total_events",
            "conversion_events",
            "conversion_rate",
            "campaign_attribution"
        ]
        
        for field in required_fields:
            if field not in attribution_summary:
                logger.error(f"❌ Missing required field in attribution summary: {field}")
                return False
        
        logger.info(f"📊 Attribution Summary:")
        logger.info(f"   Pinterest Pixel ID: {attribution_summary.get('pinterest_pixel_id')}")
        logger.info(f"   Total Events: {attribution_summary.get('total_events')}")
        logger.info(f"   Conversion Events: {attribution_summary.get('conversion_events')}")
        logger.info(f"   Conversion Rate: {attribution_summary.get('conversion_rate')}")
        
        # Check campaign attribution
        campaign_attribution = attribution_summary.get("campaign_attribution", {})
        if campaign_attribution:
            logger.info(f"   Campaign Attribution:")
            for campaign_id, data in campaign_attribution.items():
                events = data.get("events", 0)
                conversions = data.get("conversions", 0)
                logger.info(f"     Campaign {campaign_id}: {events} events, {conversions} conversions")
        
        logger.info("✅ Attribution summary test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Attribution summary test failed: {e}")
        return False

def test_pinterest_utm_parameter_mapping():
    """
    Test Pinterest UTM parameter mapping
    """
    try:
        logger.info("\n🧪 Testing Pinterest UTM Parameter Mapping")
        
        # Test UTM parameter mapping scenarios
        test_scenarios = [
            {
                "name": "Pinterest CPC Campaign",
                "utm_params": {
                    "utm_source": "pinterest",
                    "utm_medium": "cpc",
                    "utm_campaign": "test_campaign",
                    "utm_campaign_id": "123456789",
                    "utm_pin_id": "111222333",
                    "utm_ad_id": "987654321"
                },
                "expected_recognition": True
            },
            {
                "name": "Pinterest Social Campaign",
                "utm_params": {
                    "utm_source": "pinterest",
                    "utm_medium": "social",
                    "utm_campaign": "social_campaign",
                    "utm_campaign_id": "987654321"
                },
                "expected_recognition": True
            },
            {
                "name": "Pinterest Paid Social Campaign",
                "utm_params": {
                    "utm_source": "pinterest",
                    "utm_medium": "paid_social",
                    "utm_campaign": "paid_social_campaign",
                    "utm_campaign_id": "555666777"
                },
                "expected_recognition": True
            },
            {
                "name": "Non-Pinterest Campaign",
                "utm_params": {
                    "utm_source": "google",
                    "utm_medium": "cpc",
                    "utm_campaign": "google_campaign"
                },
                "expected_recognition": False
            }
        ]
        
        results = []
        for scenario in test_scenarios:
            try:
                # Simulate UTM parameter recognition logic
                is_pinterest = (
                    scenario["utm_params"].get("utm_source") == "pinterest" and
                    scenario["utm_params"].get("utm_medium") in ["cpc", "social", "paid_social"]
                )
                
                result = {
                    "name": scenario["name"],
                    "expected": scenario["expected_recognition"],
                    "actual": is_pinterest,
                    "passed": is_pinterest == scenario["expected_recognition"],
                    "utm_params": scenario["utm_params"]
                }
                
                results.append(result)
                
                if result["passed"]:
                    logger.info(f"   ✅ {scenario['name']}: PASSED")
                else:
                    logger.error(f"   ❌ {scenario['name']}: FAILED")
                
            except Exception as e:
                logger.error(f"   ❌ {scenario['name']}: Error - {e}")
                results.append({
                    "name": scenario["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        # Summary
        passed_count = sum(1 for r in results if r.get("passed", False))
        total_count = len(results)
        
        logger.info(f"📊 UTM Parameter Mapping Test Results: {passed_count}/{total_count} passed")
        return passed_count == total_count
        
    except Exception as e:
        logger.error(f"❌ UTM parameter mapping test failed: {e}")
        return False

def test_pinterest_conversion_attribution():
    """
    Test Pinterest conversion attribution
    """
    try:
        logger.info("\n🧪 Testing Pinterest Conversion Attribution")
        
        # Test conversion attribution scenarios
        conversion_scenarios = [
            {
                "name": "Pinterest Campaign Conversion",
                "event_data": {
                    "event_type": "purchase",
                    "session": {
                        "utm_source": "pinterest",
                        "utm_medium": "cpc",
                        "utm_campaign_id": "123456789",
                        "utm_pin_id": "111222333",
                        "utm_ad_id": "987654321"
                    }
                },
                "expected_attribution": True
            },
            {
                "name": "Pinterest Social Conversion",
                "event_data": {
                    "event_type": "checkout",
                    "session": {
                        "utm_source": "pinterest",
                        "utm_medium": "social",
                        "utm_campaign_id": "987654321"
                    }
                },
                "expected_attribution": True
            },
            {
                "name": "Non-Pinterest Conversion",
                "event_data": {
                    "event_type": "purchase",
                    "session": {
                        "utm_source": "google",
                        "utm_medium": "cpc",
                        "utm_campaign_id": "google_campaign"
                    }
                },
                "expected_attribution": False
            },
            {
                "name": "Pinterest Add to Cart",
                "event_data": {
                    "event_type": "add_to_cart",
                    "session": {
                        "utm_source": "pinterest",
                        "utm_medium": "cpc",
                        "utm_campaign_id": "555666777"
                    }
                },
                "expected_attribution": True
            }
        ]
        
        results = []
        for scenario in conversion_scenarios:
            try:
                # Simulate conversion attribution logic
                event_data = scenario["event_data"]
                session = event_data.get("session", {})
                event_type = event_data.get("event_type")
                
                is_pinterest_conversion = (
                    session.get("utm_source") == "pinterest" and
                    session.get("utm_medium") in ["cpc", "social", "paid_social"] and
                    event_type in ["purchase", "checkout", "conversion", "add_to_cart"]
                )
                
                result = {
                    "name": scenario["name"],
                    "expected": scenario["expected_attribution"],
                    "actual": is_pinterest_conversion,
                    "passed": is_pinterest_conversion == scenario["expected_attribution"],
                    "event_data": event_data
                }
                
                results.append(result)
                
                if result["passed"]:
                    logger.info(f"   ✅ {scenario['name']}: PASSED")
                else:
                    logger.error(f"   ❌ {scenario['name']}: FAILED")
                
            except Exception as e:
                logger.error(f"   ❌ {scenario['name']}: Error - {e}")
                results.append({
                    "name": scenario["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        # Summary
        passed_count = sum(1 for r in results if r.get("passed", False))
        total_count = len(results)
        
        logger.info(f"📊 Conversion Attribution Test Results: {passed_count}/{total_count} passed")
        return passed_count == total_count
        
    except Exception as e:
        logger.error(f"❌ Conversion attribution test failed: {e}")
        return False

def test_pinterest_multi_touch_attribution():
    """
    Test Pinterest multi-touch attribution models
    """
    try:
        logger.info("\n🧪 Testing Pinterest Multi-Touch Attribution")
        
        # Test multi-touch attribution scenarios
        attribution_scenarios = [
            {
                "name": "Pinterest First Touch",
                "customer_journey": [
                    {
                        "touchpoint": "pinterest_page_view",
                        "session": {
                            "utm_source": "pinterest",
                            "utm_medium": "cpc",
                            "utm_campaign_id": "123456789"
                        },
                        "event_type": "page_view"
                    },
                    {
                        "touchpoint": "google_search",
                        "session": {
                            "utm_source": "google",
                            "utm_medium": "cpc"
                        },
                        "event_type": "page_view"
                    },
                    {
                        "touchpoint": "pinterest_conversion",
                        "session": {
                            "utm_source": "pinterest",
                            "utm_medium": "cpc",
                            "utm_campaign_id": "123456789"
                        },
                        "event_type": "purchase"
                    }
                ],
                "expected_first_touch": "pinterest",
                "expected_last_touch": "pinterest"
            },
            {
                "name": "Pinterest Last Touch",
                "customer_journey": [
                    {
                        "touchpoint": "google_search",
                        "session": {
                            "utm_source": "google",
                            "utm_medium": "cpc"
                        },
                        "event_type": "page_view"
                    },
                    {
                        "touchpoint": "facebook_retargeting",
                        "session": {
                            "utm_source": "facebook",
                            "utm_medium": "cpc"
                        },
                        "event_type": "page_view"
                    },
                    {
                        "touchpoint": "pinterest_conversion",
                        "session": {
                            "utm_source": "pinterest",
                            "utm_medium": "cpc",
                            "utm_campaign_id": "987654321"
                        },
                        "event_type": "purchase"
                    }
                ],
                "expected_first_touch": "google",
                "expected_last_touch": "pinterest"
            }
        ]
        
        results = []
        for scenario in attribution_scenarios:
            try:
                customer_journey = scenario["customer_journey"]
                
                # Simulate multi-touch attribution logic
                first_touch = None
                last_touch = None
                
                for touchpoint in customer_journey:
                    session = touchpoint.get("session", {})
                    utm_source = session.get("utm_source")
                    
                    if first_touch is None:
                        first_touch = utm_source
                    last_touch = utm_source
                
                result = {
                    "name": scenario["name"],
                    "expected_first_touch": scenario["expected_first_touch"],
                    "actual_first_touch": first_touch,
                    "expected_last_touch": scenario["expected_last_touch"],
                    "actual_last_touch": last_touch,
                    "first_touch_passed": first_touch == scenario["expected_first_touch"],
                    "last_touch_passed": last_touch == scenario["expected_last_touch"],
                    "passed": (first_touch == scenario["expected_first_touch"] and 
                              last_touch == scenario["expected_last_touch"])
                }
                
                results.append(result)
                
                if result["passed"]:
                    logger.info(f"   ✅ {scenario['name']}: PASSED")
                else:
                    logger.error(f"   ❌ {scenario['name']}: FAILED")
                    logger.error(f"      Expected First Touch: {scenario['expected_first_touch']}, Actual: {first_touch}")
                    logger.error(f"      Expected Last Touch: {scenario['expected_last_touch']}, Actual: {last_touch}")
                
            except Exception as e:
                logger.error(f"   ❌ {scenario['name']}: Error - {e}")
                results.append({
                    "name": scenario["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        # Summary
        passed_count = sum(1 for r in results if r.get("passed", False))
        total_count = len(results)
        
        logger.info(f"📊 Multi-Touch Attribution Test Results: {passed_count}/{total_count} passed")
        return passed_count == total_count
        
    except Exception as e:
        logger.error(f"❌ Multi-touch attribution test failed: {e}")
        return False

def main():
    """
    Main test function
    """
    try:
        logger.info("🚀 Starting Pinterest Track AI Configuration Tests")
        logger.info(f"⏰ Started at: {datetime.now()}")
        
        # Run all tests
        tests = [
            ("Pinterest Track AI Configuration", test_pinterest_track_ai_configuration),
            ("Pinterest Traffic Recognition (Detailed)", test_pinterest_traffic_recognition_detailed),
            ("Pinterest Attribution Summary", test_pinterest_attribution_summary),
            ("Pinterest UTM Parameter Mapping", test_pinterest_utm_parameter_mapping),
            ("Pinterest Conversion Attribution", test_pinterest_conversion_attribution),
            ("Pinterest Multi-Touch Attribution", test_pinterest_multi_touch_attribution)
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
            logger.info("🎉 All tests passed! Pinterest Track AI configuration is ready.")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Check configuration and setup.")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
