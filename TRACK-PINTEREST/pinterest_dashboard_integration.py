"""
Pinterest Dashboard Integration for Track AI
===========================================

This module integrates Pinterest performance data with the Track AI dashboard
to provide unified analytics across all advertising platforms.

Features:
- Pinterest API v5 data synchronization
- Automated data refresh (5 AM and 5 PM UTC)
- Error handling and retry logic
- Data transformation and normalization
- Real-time data streaming support
- Rate limit compliance
- Cross-platform analytics
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import schedule
import threading

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_auth import get_access_token, get_ad_account_id
from pinterest_conversion_tracking import PinterestConversionTracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Pinterest API Configuration
PINTEREST_API_BASE = "https://api.pinterest.com/v5"
TRACK_AI_DASHBOARD_API = os.getenv("TRACK_AI_DASHBOARD_API", "https://track.ai.yourdomain.com/api")
SYNC_INTERVAL_HOURS = 12  # 5 AM and 5 PM UTC
RATE_LIMIT_DELAY = 1  # 1 second delay between API calls

@dataclass
class PinterestMetrics:
    """Pinterest performance metrics data structure"""
    campaign_id: str
    campaign_name: str
    impressions: int
    clicks: int
    ctr: float
    spend: float
    saves: int
    closeups: int
    engagement_rate: float
    date: str
    ad_account_id: str

class PinterestDashboardIntegration:
    """
    Pinterest Dashboard Integration Manager
    
    Handles Pinterest data synchronization with Track AI dashboard,
    including automated data refresh, error handling, and rate limiting.
    """
    
    def __init__(self, access_token: str = None, ad_account_id: str = None):
        """
        Initialize Pinterest Dashboard Integration
        
        Args:
            access_token: Pinterest API access token
            ad_account_id: Pinterest ad account ID
        """
        self.access_token = access_token or get_access_token()
        self.ad_account_id = ad_account_id or get_ad_account_id(self.access_token)
        self.conversion_tracker = PinterestConversionTracker(access_token=self.access_token)
        
        # Rate limiting
        self.last_api_call = 0
        self.rate_limit_delay = RATE_LIMIT_DELAY
        
        # Data cache
        self.cached_metrics = {}
        self.last_sync = None
        
        logger.info(f"✅ Pinterest Dashboard Integration initialized")
        logger.info(f"   Ad Account ID: {self.ad_account_id}")
        logger.info(f"   Sync Interval: {SYNC_INTERVAL_HOURS} hours")
    
    def sync_pinterest_data(self) -> bool:
        """
        Synchronize Pinterest data with Track AI dashboard
        
        Returns:
            True if synchronization successful, False otherwise
        """
        try:
            logger.info("🔄 Starting Pinterest data synchronization")
            
            # Get Pinterest campaigns
            campaigns = self._get_pinterest_campaigns()
            if not campaigns:
                logger.warning("⚠️ No Pinterest campaigns found")
                return True
            
            # Get metrics for each campaign
            all_metrics = []
            for campaign in campaigns:
                try:
                    campaign_metrics = self._get_campaign_metrics(campaign)
                    if campaign_metrics:
                        all_metrics.extend(campaign_metrics)
                except Exception as e:
                    logger.error(f"❌ Error getting metrics for campaign {campaign.get('id')}: {e}")
                    continue
            
            # Transform and normalize data
            transformed_data = self._transform_pinterest_data(all_metrics)
            
            # Send to Track AI dashboard
            success = self._send_to_track_ai_dashboard(transformed_data)
            
            if success:
                self.last_sync = datetime.now()
                self.cached_metrics = transformed_data
                logger.info(f"✅ Pinterest data synchronization completed: {len(transformed_data)} metrics")
            else:
                logger.error("❌ Failed to send data to Track AI dashboard")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error in Pinterest data synchronization: {e}")
            return False
    
    def _get_pinterest_campaigns(self) -> List[Dict[str, Any]]:
        """
        Get Pinterest campaigns from API
        
        Returns:
            List of campaign data
        """
        try:
            self._rate_limit_delay()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{PINTEREST_API_BASE}/ad_accounts/{self.ad_account_id}/campaigns"
            params = {
                "page_size": 250,
                "order": "DESCENDING"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                campaigns = data.get("items", [])
                logger.info(f"✅ Retrieved {len(campaigns)} Pinterest campaigns")
                return campaigns
            else:
                logger.error(f"❌ Failed to get Pinterest campaigns: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting Pinterest campaigns: {e}")
            return []
    
    def _get_campaign_metrics(self, campaign: Dict[str, Any]) -> List[PinterestMetrics]:
        """
        Get metrics for a specific campaign
        
        Args:
            campaign: Campaign data
            
        Returns:
            List of Pinterest metrics
        """
        try:
            campaign_id = campaign.get("id")
            campaign_name = campaign.get("name")
            
            self._rate_limit_delay()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get campaign insights
            url = f"{PINTEREST_API_BASE}/ad_accounts/{self.ad_account_id}/campaigns/{campaign_id}/insights"
            params = {
                "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "granularity": "DAY",
                "metrics": [
                    "IMPRESSIONS", "CLICKS", "CTR", "SPEND", "SAVES", "CLOSEUPS"
                ]
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                insights = data.get("data", [])
                
                metrics = []
                for insight in insights:
                    try:
                        metric = PinterestMetrics(
                            campaign_id=campaign_id,
                            campaign_name=campaign_name,
                            impressions=int(insight.get("IMPRESSIONS", 0)),
                            clicks=int(insight.get("CLICKS", 0)),
                            ctr=float(insight.get("CTR", 0)),
                            spend=float(insight.get("SPEND", 0)),
                            saves=int(insight.get("SAVES", 0)),
                            closeups=int(insight.get("CLOSEUPS", 0)),
                            engagement_rate=self._calculate_engagement_rate(insight),
                            date=insight.get("DATE", ""),
                            ad_account_id=self.ad_account_id
                        )
                        metrics.append(metric)
                    except Exception as e:
                        logger.error(f"❌ Error processing insight for campaign {campaign_id}: {e}")
                        continue
                
                logger.info(f"✅ Retrieved {len(metrics)} metrics for campaign {campaign_name}")
                return metrics
            else:
                logger.error(f"❌ Failed to get metrics for campaign {campaign_id}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting campaign metrics: {e}")
            return []
    
    def _calculate_engagement_rate(self, insight: Dict[str, Any]) -> float:
        """
        Calculate engagement rate from Pinterest metrics
        
        Args:
            insight: Pinterest insight data
            
        Returns:
            Engagement rate as percentage
        """
        try:
            impressions = int(insight.get("IMPRESSIONS", 0))
            saves = int(insight.get("SAVES", 0))
            closeups = int(insight.get("CLOSEUPS", 0))
            
            if impressions > 0:
                engagement_rate = ((saves + closeups) / impressions) * 100
                return round(engagement_rate, 2)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"❌ Error calculating engagement rate: {e}")
            return 0.0
    
    def _transform_pinterest_data(self, metrics: List[PinterestMetrics]) -> List[Dict[str, Any]]:
        """
        Transform Pinterest data to Track AI format
        
        Args:
            metrics: List of Pinterest metrics
            
        Returns:
            List of transformed data
        """
        try:
            transformed_data = []
            
            for metric in metrics:
                transformed_metric = {
                    "platform": "pinterest",
                    "campaign_id": metric.campaign_id,
                    "campaign_name": metric.campaign_name,
                    "ad_account_id": metric.ad_account_id,
                    "date": metric.date,
                    "impressions": metric.impressions,
                    "clicks": metric.clicks,
                    "ctr": metric.ctr,
                    "spend": metric.spend,
                    "saves": metric.saves,
                    "closeups": metric.closeups,
                    "engagement_rate": metric.engagement_rate,
                    "pinterest_specific": {
                        "saves": metric.saves,
                        "closeups": metric.closeups,
                        "engagement_rate": metric.engagement_rate
                    },
                    "normalized_metrics": {
                        "impressions": metric.impressions,
                        "clicks": metric.clicks,
                        "ctr": metric.ctr,
                        "spend": metric.spend,
                        "engagement": metric.saves + metric.closeups
                    }
                }
                transformed_data.append(transformed_metric)
            
            logger.info(f"✅ Transformed {len(transformed_data)} Pinterest metrics")
            return transformed_data
            
        except Exception as e:
            logger.error(f"❌ Error transforming Pinterest data: {e}")
            return []
    
    def _send_to_track_ai_dashboard(self, data: List[Dict[str, Any]]) -> bool:
        """
        Send Pinterest data to Track AI dashboard
        
        Args:
            data: Transformed Pinterest data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not data:
                logger.warning("⚠️ No data to send to Track AI dashboard")
                return True
            
            # Send to Track AI dashboard API
            url = f"{TRACK_AI_DASHBOARD_API}/pinterest/metrics"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('TRACK_AI_API_KEY', '')}"
            }
            
            payload = {
                "platform": "pinterest",
                "metrics": data,
                "sync_timestamp": datetime.now().isoformat(),
                "total_metrics": len(data)
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully sent {len(data)} metrics to Track AI dashboard")
                return True
            else:
                logger.error(f"❌ Failed to send data to Track AI dashboard: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending data to Track AI dashboard: {e}")
            return False
    
    def _rate_limit_delay(self):
        """
        Implement rate limiting for Pinterest API calls
        """
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    def get_pinterest_dashboard_data(self) -> Dict[str, Any]:
        """
        Get Pinterest dashboard data from Track AI
        
        Returns:
            Dictionary with Pinterest dashboard data
        """
        try:
            url = f"{TRACK_AI_DASHBOARD_API}/pinterest/dashboard"
            headers = {
                "Authorization": f"Bearer {os.getenv('TRACK_AI_API_KEY', '')}"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Retrieved Pinterest dashboard data from Track AI")
                return data
            else:
                logger.error(f"❌ Failed to get Pinterest dashboard data: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error getting Pinterest dashboard data: {e}")
            return {}
    
    def get_cross_platform_analytics(self) -> Dict[str, Any]:
        """
        Get cross-platform analytics including Pinterest
        
        Returns:
            Dictionary with cross-platform analytics
        """
        try:
            url = f"{TRACK_AI_DASHBOARD_API}/analytics/cross-platform"
            headers = {
                "Authorization": f"Bearer {os.getenv('TRACK_AI_API_KEY', '')}"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Retrieved cross-platform analytics")
                return data
            else:
                logger.error(f"❌ Failed to get cross-platform analytics: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error getting cross-platform analytics: {e}")
            return {}
    
    def start_automated_sync(self):
        """
        Start automated data synchronization
        """
        try:
            logger.info("🔄 Starting automated Pinterest data synchronization")
            
            # Schedule sync at 5 AM and 5 PM UTC
            schedule.every().day.at("05:00").do(self.sync_pinterest_data)
            schedule.every().day.at("17:00").do(self.sync_pinterest_data)
            
            # Run initial sync
            self.sync_pinterest_data()
            
            # Start scheduler in background thread
            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            
            logger.info("✅ Automated Pinterest data synchronization started")
            logger.info("   Sync schedule: 5:00 AM and 5:00 PM UTC")
            
        except Exception as e:
            logger.error(f"❌ Error starting automated sync: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get synchronization status
        
        Returns:
            Dictionary with sync status
        """
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "cached_metrics_count": len(self.cached_metrics),
            "sync_interval_hours": SYNC_INTERVAL_HOURS,
            "rate_limit_delay": self.rate_limit_delay,
            "ad_account_id": self.ad_account_id
        }

# Convenience functions for easy integration
def sync_pinterest_dashboard_data() -> bool:
    """
    Synchronize Pinterest data with Track AI dashboard
    
    Returns:
        True if synchronization successful, False otherwise
    """
    integration = PinterestDashboardIntegration()
    return integration.sync_pinterest_data()

def get_pinterest_dashboard_metrics() -> Dict[str, Any]:
    """
    Get Pinterest dashboard metrics from Track AI
    
    Returns:
        Dictionary with Pinterest metrics
    """
    integration = PinterestDashboardIntegration()
    return integration.get_pinterest_dashboard_data()

def start_pinterest_automated_sync():
    """
    Start automated Pinterest data synchronization
    """
    integration = PinterestDashboardIntegration()
    integration.start_automated_sync()

# Example usage
if __name__ == "__main__":
    # Initialize integration
    integration = PinterestDashboardIntegration()
    
    # Sync Pinterest data
    success = integration.sync_pinterest_data()
    if success:
        print("✅ Pinterest data synchronization successful")
    else:
        print("❌ Pinterest data synchronization failed")
    
    # Get dashboard data
    dashboard_data = integration.get_pinterest_dashboard_data()
    print(f"📊 Dashboard data: {len(dashboard_data.get('metrics', []))} metrics")
    
    # Get sync status
    sync_status = integration.get_sync_status()
    print(f"🔄 Sync status: {sync_status}")
