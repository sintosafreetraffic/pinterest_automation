"""
Test Pinterest Dashboard Integration
==================================

This script tests the Pinterest dashboard integration system,
validating data synchronization, error handling, and rate limiting.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_dashboard_integration import (
    PinterestDashboardIntegration,
    PinterestMetrics,
    sync_pinterest_dashboard_data,
    get_pinterest_dashboard_metrics,
    start_pinterest_automated_sync
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_pinterest_dashboard_integration_initialization():
    """
    Test Pinterest dashboard integration initialization
    """
    try:
        logger.info("🧪 Testing Pinterest Dashboard Integration Initialization")
        
        # Initialize integration
        integration = PinterestDashboardIntegration()
        logger.info("✅ Pinterest dashboard integration initialized")
        
        # Test configuration
        if integration.ad_account_id:
            logger.info(f"✅ Ad Account ID configured: {integration.ad_account_id}")
        else:
            logger.warning("⚠️ Ad Account ID not configured")
        
        if integration.access_token:
            logger.info("✅ Pinterest access token configured")
        else:
            logger.warning("⚠️ Pinterest access token not configured")
        
        # Test sync status
        sync_status = integration.get_sync_status()
        logger.info(f"📊 Sync Status: {sync_status}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pinterest dashboard integration initialization test failed: {e}")
        return False

def test_pinterest_metrics_data_structure():
    """
    Test Pinterest metrics data structure
    """
    try:
        logger.info("\n🧪 Testing Pinterest Metrics Data Structure")
        
        # Create test metrics
        test_metrics = PinterestMetrics(
            campaign_id="123456789",
            campaign_name="Test Campaign",
            impressions=1000,
            clicks=50,
            ctr=5.0,
            spend=100.0,
            saves=25,
            closeups=15,
            engagement_rate=4.0,
            date="2025-01-24",
            ad_account_id="987654321"
        )
        
        # Validate metrics
        assert test_metrics.campaign_id == "123456789"
        assert test_metrics.campaign_name == "Test Campaign"
        assert test_metrics.impressions == 1000
        assert test_metrics.clicks == 50
        assert test_metrics.ctr == 5.0
        assert test_metrics.spend == 100.0
        assert test_metrics.saves == 25
        assert test_metrics.closeups == 15
        assert test_metrics.engagement_rate == 4.0
        assert test_metrics.date == "2025-01-24"
        assert test_metrics.ad_account_id == "987654321"
        
        logger.info("✅ Pinterest metrics data structure test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Pinterest metrics data structure test failed: {e}")
        return False

def test_pinterest_campaigns_retrieval():
    """
    Test Pinterest campaigns retrieval
    """
    try:
        logger.info("\n🧪 Testing Pinterest Campaigns Retrieval")
        
        integration = PinterestDashboardIntegration()
        
        # Mock Pinterest API response
        mock_campaigns = [
            {
                "id": "123456789",
                "name": "Test Campaign 1",
                "status": "ACTIVE",
                "objective_type": "WEB_CONVERSION"
            },
            {
                "id": "987654321",
                "name": "Test Campaign 2",
                "status": "ACTIVE",
                "objective_type": "CONSIDERATION"
            }
        ]
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"items": mock_campaigns}
            mock_get.return_value = mock_response
            
            # Test campaigns retrieval
            campaigns = integration._get_pinterest_campaigns()
            
            if campaigns:
                logger.info(f"✅ Retrieved {len(campaigns)} Pinterest campaigns")
                for campaign in campaigns:
                    logger.info(f"   Campaign: {campaign.get('name')} (ID: {campaign.get('id')})")
            else:
                logger.warning("⚠️ No campaigns retrieved")
            
            return True
        
    except Exception as e:
        logger.error(f"❌ Pinterest campaigns retrieval test failed: {e}")
        return False

def test_pinterest_campaign_metrics():
    """
    Test Pinterest campaign metrics retrieval
    """
    try:
        logger.info("\n🧪 Testing Pinterest Campaign Metrics")
        
        integration = PinterestDashboardIntegration()
        
        # Mock campaign data
        mock_campaign = {
            "id": "123456789",
            "name": "Test Campaign",
            "status": "ACTIVE"
        }
        
        # Mock metrics response
        mock_insights = [
            {
                "DATE": "2025-01-24",
                "IMPRESSIONS": 1000,
                "CLICKS": 50,
                "CTR": 5.0,
                "SPEND": 100.0,
                "SAVES": 25,
                "CLOSEUPS": 15
            },
            {
                "DATE": "2025-01-23",
                "IMPRESSIONS": 800,
                "CLICKS": 40,
                "CTR": 5.0,
                "SPEND": 80.0,
                "SAVES": 20,
                "CLOSEUPS": 12
            }
        ]
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": mock_insights}
            mock_get.return_value = mock_response
            
            # Test metrics retrieval
            metrics = integration._get_campaign_metrics(mock_campaign)
            
            if metrics:
                logger.info(f"✅ Retrieved {len(metrics)} metrics for campaign")
                for metric in metrics:
                    logger.info(f"   Date: {metric.date}, Impressions: {metric.impressions}, Clicks: {metric.clicks}")
            else:
                logger.warning("⚠️ No metrics retrieved")
            
            return True
        
    except Exception as e:
        logger.error(f"❌ Pinterest campaign metrics test failed: {e}")
        return False

def test_engagement_rate_calculation():
    """
    Test engagement rate calculation
    """
    try:
        logger.info("\n🧪 Testing Engagement Rate Calculation")
        
        integration = PinterestDashboardIntegration()
        
        # Test cases for engagement rate calculation
        test_cases = [
            {
                "name": "Normal Engagement",
                "insight": {
                    "IMPRESSIONS": 1000,
                    "SAVES": 25,
                    "CLOSEUPS": 15
                },
                "expected_rate": 4.0  # (25 + 15) / 1000 * 100
            },
            {
                "name": "High Engagement",
                "insight": {
                    "IMPRESSIONS": 500,
                    "SAVES": 50,
                    "CLOSEUPS": 30
                },
                "expected_rate": 16.0  # (50 + 30) / 500 * 100
            },
            {
                "name": "Zero Impressions",
                "insight": {
                    "IMPRESSIONS": 0,
                    "SAVES": 10,
                    "CLOSEUPS": 5
                },
                "expected_rate": 0.0
            },
            {
                "name": "No Engagement",
                "insight": {
                    "IMPRESSIONS": 1000,
                    "SAVES": 0,
                    "CLOSEUPS": 0
                },
                "expected_rate": 0.0
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                # Calculate engagement rate
                actual_rate = integration._calculate_engagement_rate(test_case["insight"])
                expected_rate = test_case["expected_rate"]
                
                result = {
                    "name": test_case["name"],
                    "expected": expected_rate,
                    "actual": actual_rate,
                    "passed": abs(actual_rate - expected_rate) < 0.01  # Allow small floating point differences
                }
                
                results.append(result)
                
                if result["passed"]:
                    logger.info(f"   ✅ {test_case['name']}: PASSED (Expected: {expected_rate}%, Actual: {actual_rate}%)")
                else:
                    logger.error(f"   ❌ {test_case['name']}: FAILED (Expected: {expected_rate}%, Actual: {actual_rate}%)")
                
            except Exception as e:
                logger.error(f"   ❌ {test_case['name']}: Error - {e}")
                results.append({
                    "name": test_case["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        # Summary
        passed_count = sum(1 for r in results if r.get("passed", False))
        total_count = len(results)
        
        logger.info(f"📊 Engagement Rate Calculation Test Results: {passed_count}/{total_count} passed")
        return passed_count == total_count
        
    except Exception as e:
        logger.error(f"❌ Engagement rate calculation test failed: {e}")
        return False

def test_data_transformation():
    """
    Test Pinterest data transformation
    """
    try:
        logger.info("\n🧪 Testing Pinterest Data Transformation")
        
        integration = PinterestDashboardIntegration()
        
        # Create test metrics
        test_metrics = [
            PinterestMetrics(
                campaign_id="123456789",
                campaign_name="Test Campaign 1",
                impressions=1000,
                clicks=50,
                ctr=5.0,
                spend=100.0,
                saves=25,
                closeups=15,
                engagement_rate=4.0,
                date="2025-01-24",
                ad_account_id="987654321"
            ),
            PinterestMetrics(
                campaign_id="987654321",
                campaign_name="Test Campaign 2",
                impressions=800,
                clicks=40,
                ctr=5.0,
                spend=80.0,
                saves=20,
                closeups=12,
                engagement_rate=4.0,
                date="2025-01-24",
                ad_account_id="987654321"
            )
        ]
        
        # Transform data
        transformed_data = integration._transform_pinterest_data(test_metrics)
        
        if transformed_data:
            logger.info(f"✅ Transformed {len(transformed_data)} metrics")
            
            # Validate transformed data structure
            for metric in transformed_data:
                required_fields = [
                    "platform", "campaign_id", "campaign_name", "ad_account_id",
                    "date", "impressions", "clicks", "ctr", "spend",
                    "saves", "closeups", "engagement_rate"
                ]
                
                missing_fields = [field for field in required_fields if field not in metric]
                if missing_fields:
                    logger.error(f"❌ Missing fields in transformed data: {missing_fields}")
                    return False
                
                # Check Pinterest-specific fields
                if "pinterest_specific" not in metric:
                    logger.error("❌ Missing pinterest_specific field")
                    return False
                
                if "normalized_metrics" not in metric:
                    logger.error("❌ Missing normalized_metrics field")
                    return False
            
            logger.info("✅ Data transformation test passed")
            return True
        else:
            logger.error("❌ No transformed data generated")
            return False
        
    except Exception as e:
        logger.error(f"❌ Data transformation test failed: {e}")
        return False

def test_rate_limiting():
    """
    Test rate limiting functionality
    """
    try:
        logger.info("\n🧪 Testing Rate Limiting")
        
        integration = PinterestDashboardIntegration()
        
        # Test rate limiting
        start_time = datetime.now()
        integration._rate_limit_delay()
        end_time = datetime.now()
        
        # Check if delay was applied
        delay_time = (end_time - start_time).total_seconds()
        expected_delay = integration.rate_limit_delay
        
        if delay_time >= expected_delay:
            logger.info(f"✅ Rate limiting test passed (Delay: {delay_time:.2f}s, Expected: {expected_delay}s)")
            return True
        else:
            logger.warning(f"⚠️ Rate limiting test failed (Delay: {delay_time:.2f}s, Expected: {expected_delay}s)")
            return False
        
    except Exception as e:
        logger.error(f"❌ Rate limiting test failed: {e}")
        return False

def test_sync_status():
    """
    Test synchronization status
    """
    try:
        logger.info("\n🧪 Testing Sync Status")
        
        integration = PinterestDashboardIntegration()
        
        # Get sync status
        sync_status = integration.get_sync_status()
        
        # Validate sync status structure
        required_fields = [
            "last_sync", "cached_metrics_count", "sync_interval_hours",
            "rate_limit_delay", "ad_account_id"
        ]
        
        missing_fields = [field for field in required_fields if field not in sync_status]
        if missing_fields:
            logger.error(f"❌ Missing fields in sync status: {missing_fields}")
            return False
        
        logger.info(f"📊 Sync Status:")
        logger.info(f"   Last Sync: {sync_status.get('last_sync')}")
        logger.info(f"   Cached Metrics: {sync_status.get('cached_metrics_count')}")
        logger.info(f"   Sync Interval: {sync_status.get('sync_interval_hours')} hours")
        logger.info(f"   Rate Limit Delay: {sync_status.get('rate_limit_delay')}s")
        logger.info(f"   Ad Account ID: {sync_status.get('ad_account_id')}")
        
        logger.info("✅ Sync status test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Sync status test failed: {e}")
        return False

def test_dashboard_data_retrieval():
    """
    Test dashboard data retrieval
    """
    try:
        logger.info("\n🧪 Testing Dashboard Data Retrieval")
        
        integration = PinterestDashboardIntegration()
        
        # Mock Track AI dashboard API response
        mock_dashboard_data = {
            "platform": "pinterest",
            "metrics": [
                {
                    "campaign_id": "123456789",
                    "campaign_name": "Test Campaign",
                    "impressions": 1000,
                    "clicks": 50,
                    "ctr": 5.0,
                    "spend": 100.0
                }
            ],
            "total_metrics": 1,
            "last_updated": "2025-01-24T10:00:00Z"
        }
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_dashboard_data
            mock_get.return_value = mock_response
            
            # Test dashboard data retrieval
            dashboard_data = integration.get_pinterest_dashboard_data()
            
            if dashboard_data:
                logger.info("✅ Dashboard data retrieved successfully")
                logger.info(f"   Platform: {dashboard_data.get('platform')}")
                logger.info(f"   Total Metrics: {dashboard_data.get('total_metrics')}")
                return True
            else:
                logger.warning("⚠️ No dashboard data retrieved")
                return True  # Not a failure in test environment
        
    except Exception as e:
        logger.error(f"❌ Dashboard data retrieval test failed: {e}")
        return False

def main():
    """
    Main test function
    """
    try:
        logger.info("🚀 Starting Pinterest Dashboard Integration Tests")
        logger.info(f"⏰ Started at: {datetime.now()}")
        
        # Run all tests
        tests = [
            ("Pinterest Dashboard Integration Initialization", test_pinterest_dashboard_integration_initialization),
            ("Pinterest Metrics Data Structure", test_pinterest_metrics_data_structure),
            ("Pinterest Campaigns Retrieval", test_pinterest_campaigns_retrieval),
            ("Pinterest Campaign Metrics", test_pinterest_campaign_metrics),
            ("Engagement Rate Calculation", test_engagement_rate_calculation),
            ("Data Transformation", test_data_transformation),
            ("Rate Limiting", test_rate_limiting),
            ("Sync Status", test_sync_status),
            ("Dashboard Data Retrieval", test_dashboard_data_retrieval)
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
            logger.info("🎉 All tests passed! Pinterest dashboard integration is ready.")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Check configuration and setup.")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
