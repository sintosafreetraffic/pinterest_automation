"""
Pinterest Pin URL Generator with Track AI Integration
====================================================

This module provides enhanced URL generation for Pinterest pins with automatic
tracking parameter appending, UTM parameter generation, and Track AI pixel integration.

Features:
- Automatic tracking parameter appending to all destination URLs
- UTM parameter generation based on campaign metadata
- Track AI pixel integration for comprehensive tracking
- URL validation and length management
- Pinterest API v5 integration for campaign and ad metadata
- URL shortening service integration for long URLs
"""

import os
import sys
import time
import requests
import urllib.parse
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from track_ai_integration import PinterestTrackAIIntegration, validate_pinterest_url
from pinterest_auth import get_access_token

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Pinterest API Configuration
BASE_URL = "https://api.pinterest.com/v5"
MAX_URL_LENGTH = 2000  # Pinterest URL length limit
BITLY_API_URL = "https://api-ssl.bitly.com/v4/shorten"  # Bitly API v4 for URL shortening

class PinterestURLGenerator:
    """
    Enhanced Pinterest URL Generator with Track AI Integration
    
    Handles automatic tracking parameter appending, UTM parameter generation,
    and Track AI pixel integration for all Pinterest destination URLs.
    """
    
    def __init__(self, access_token: str = None, bitly_token: str = None):
        """
        Initialize Pinterest URL Generator
        
        Args:
            access_token: Pinterest API access token
            bitly_token: Bitly API token for URL shortening
        """
        self.access_token = access_token or get_access_token()
        self.bitly_token = bitly_token or os.getenv("BITLY_TOKEN")
        self.track_ai_integration = PinterestTrackAIIntegration()
        
    def get_campaign_metadata(self, campaign_id: str) -> Dict[str, Any]:
        """
        Retrieve campaign metadata from Pinterest API
        
        Args:
            campaign_id: Pinterest campaign ID
            
        Returns:
            Dictionary with campaign metadata
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{BASE_URL}/ad_accounts/{self.get_ad_account_id()}/campaigns/{campaign_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                campaign_data = response.json()
                logger.info(f"✅ Retrieved campaign metadata for {campaign_id}")
                return campaign_data
            else:
                logger.warning(f"⚠️ Failed to retrieve campaign metadata: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error retrieving campaign metadata: {e}")
            return {}
    
    def get_ad_metadata(self, ad_id: str) -> Dict[str, Any]:
        """
        Retrieve ad metadata from Pinterest API
        
        Args:
            ad_id: Pinterest ad ID
            
        Returns:
            Dictionary with ad metadata
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{BASE_URL}/ad_accounts/{self.get_ad_account_id()}/ads/{ad_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                ad_data = response.json()
                logger.info(f"✅ Retrieved ad metadata for {ad_id}")
                return ad_data
            else:
                logger.warning(f"⚠️ Failed to retrieve ad metadata: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error retrieving ad metadata: {e}")
            return {}
    
    def get_ad_account_id(self) -> str:
        """
        Get Pinterest ad account ID
        
        Returns:
            Ad account ID
        """
        try:
            from pinterest_auth import get_ad_account_id
            return get_ad_account_id(self.access_token)
        except Exception as e:
            logger.error(f"❌ Error getting ad account ID: {e}")
            return ""
    
    def generate_tracking_parameters(self, 
                                   base_url: str,
                                   campaign_id: str = None,
                                   ad_id: str = None,
                                   pin_id: str = None,
                                   campaign_name: str = None,
                                   objective_type: str = "WEB_CONVERSION",
                                   launch_date: str = None,
                                   product_name: str = None,
                                   product_type: str = None,
                                   board_title: str = None,
                                   pin_variant: str = None,
                                   daily_budget: int = None) -> str:
        """
        Generate enhanced URL with comprehensive tracking parameters
        
        Args:
            base_url: Base destination URL
            campaign_id: Pinterest campaign ID
            ad_id: Pinterest ad ID
            pin_id: Pinterest pin ID
            campaign_name: Campaign name
            objective_type: Campaign objective
            launch_date: Campaign launch date
            product_name: Product name
            product_type: Product type
            board_title: Pinterest board title
            pin_variant: Pin variant
            daily_budget: Daily budget in cents
            
        Returns:
            Enhanced URL with comprehensive tracking parameters
        """
        try:
            logger.info(f"🔗 Generating enhanced URL for: {base_url}")
            
            # Get campaign metadata if campaign_id is provided
            campaign_metadata = {}
            if campaign_id:
                campaign_metadata = self.get_campaign_metadata(campaign_id)
                if not campaign_name and campaign_metadata:
                    campaign_name = campaign_metadata.get('name', 'Unknown Campaign')
                if not objective_type and campaign_metadata:
                    objective_type = campaign_metadata.get('objective_type', 'WEB_CONVERSION')
                if not daily_budget and campaign_metadata:
                    daily_budget = campaign_metadata.get('daily_spend_cap', 1000)
            
            # Get ad metadata if ad_id is provided
            ad_metadata = {}
            if ad_id:
                ad_metadata = self.get_ad_metadata(ad_id)
            
            # Generate enhanced URL with Track AI integration
            enhanced_url = self.track_ai_integration.generate_enhanced_destination_url(
                base_url=base_url,
                campaign_name=campaign_name or f"Campaign_{campaign_id}",
                objective_type=objective_type,
                launch_date=launch_date or datetime.now().strftime('%Y-%m-%d'),
                product_name=product_name,
                product_type=product_type,
                board_title=board_title,
                pin_variant=pin_variant,
                campaign_id=campaign_id,
                pin_id=pin_id,
                ad_id=ad_id,
                daily_budget=daily_budget
            )
            
            # Validate URL length
            if not self.track_ai_integration.validate_url_length(enhanced_url, MAX_URL_LENGTH):
                logger.warning("⚠️ Enhanced URL exceeds length limit, creating fallback")
                essential_params = {
                    'utm_source': 'pinterest',
                    'utm_medium': 'cpc' if objective_type == 'WEB_CONVERSION' else 'social',
                    'utm_campaign': f"{launch_date or datetime.now().strftime('%Y-%m-%d')}_{campaign_name or 'campaign'}_{objective_type}".lower().replace(' ', '_'),
                    'utm_campaign_id': campaign_id or '',
                    'utm_pin_id': pin_id or '',
                    'utm_ad_id': ad_id or '',
                    'track_ai_store_id': self.track_ai_integration.store_id,
                    'track_ai_pixel_id': self.track_ai_integration.pixel_id
                }
                enhanced_url = self.track_ai_integration.create_fallback_url(base_url, essential_params)
            
            # Final URL validation
            is_valid, error_msg = validate_pinterest_url(enhanced_url)
            if not is_valid:
                logger.error(f"❌ Generated URL is invalid: {error_msg}")
                return base_url
            
            logger.info(f"✅ Enhanced URL generated: {enhanced_url}")
            return enhanced_url
            
        except Exception as e:
            logger.error(f"❌ Error generating enhanced URL: {e}")
            return base_url
    
    def shorten_url(self, url: str) -> str:
        """
        Shorten URL using Bitly API v4
        
        Args:
            url: URL to shorten
            
        Returns:
            Shortened URL or original URL if shortening fails
        """
        try:
            if not self.bitly_token:
                logger.warning("⚠️ Bitly token not configured, skipping URL shortening")
                return url
            
            headers = {
                "Authorization": f"Bearer {self.bitly_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "long_url": url,
                "domain": "bit.ly"
            }
            
            response = requests.post(BITLY_API_URL, json=payload, headers=headers)
            
            if response.status_code == 201:
                shortened_data = response.json()
                shortened_url = shortened_data.get('link', url)
                logger.info(f"✅ URL shortened: {shortened_url}")
                return shortened_url
            else:
                logger.warning(f"⚠️ URL shortening failed: {response.status_code}")
                return url
                
        except Exception as e:
            logger.error(f"❌ Error shortening URL: {e}")
            return url
    
    def generate_pin_url(self, 
                        base_url: str,
                        campaign_id: str = None,
                        ad_id: str = None,
                        pin_id: str = None,
                        **kwargs) -> str:
        """
        Generate enhanced pin URL with comprehensive tracking
        
        Args:
            base_url: Base destination URL
            campaign_id: Pinterest campaign ID
            ad_id: Pinterest ad ID
            pin_id: Pinterest pin ID
            **kwargs: Additional parameters
            
        Returns:
            Enhanced URL with comprehensive tracking
        """
        try:
            # Generate enhanced URL with tracking parameters
            enhanced_url = self.generate_tracking_parameters(
                base_url=base_url,
                campaign_id=campaign_id,
                ad_id=ad_id,
                pin_id=pin_id,
                **kwargs
            )
            
            # Shorten URL if it's too long
            if len(enhanced_url) > MAX_URL_LENGTH:
                logger.info("🔗 URL exceeds length limit, attempting to shorten")
                shortened_url = self.shorten_url(enhanced_url)
                if len(shortened_url) < len(enhanced_url):
                    enhanced_url = shortened_url
                    logger.info(f"✅ URL shortened successfully: {enhanced_url}")
                else:
                    logger.warning("⚠️ URL shortening failed, using original URL")
            
            return enhanced_url
            
        except Exception as e:
            logger.error(f"❌ Error generating pin URL: {e}")
            return base_url
    
    def batch_generate_urls(self, 
                           urls_data: list,
                           campaign_id: str = None,
                           **kwargs) -> Dict[str, Any]:
        """
        Generate enhanced URLs for multiple pins in batch
        
        Args:
            urls_data: List of URL data dictionaries
            campaign_id: Pinterest campaign ID
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with results summary
        """
        try:
            results = {
                'successful': [],
                'failed': [],
                'total': len(urls_data)
            }
            
            for i, url_data in enumerate(urls_data):
                try:
                    logger.info(f"🔗 Generating URL {i+1}/{len(urls_data)}")
                    
                    enhanced_url = self.generate_pin_url(
                        base_url=url_data.get('base_url'),
                        campaign_id=campaign_id,
                        ad_id=url_data.get('ad_id'),
                        pin_id=url_data.get('pin_id'),
                        **kwargs
                    )
                    
                    if enhanced_url != url_data.get('base_url'):
                        results['successful'].append({
                            'original_url': url_data.get('base_url'),
                            'enhanced_url': enhanced_url,
                            'product_name': url_data.get('product_name'),
                            'campaign_id': campaign_id
                        })
                    else:
                        results['failed'].append({
                            'original_url': url_data.get('base_url'),
                            'error': 'URL generation failed',
                            'product_name': url_data.get('product_name')
                        })
                        
                except Exception as e:
                    logger.error(f"❌ Error generating URL {i+1}: {e}")
                    results['failed'].append({
                        'original_url': url_data.get('base_url'),
                        'error': str(e),
                        'product_name': url_data.get('product_name')
                    })
            
            logger.info(f"🎯 URL Generation Results: {len(results['successful'])} successful, {len(results['failed'])} failed")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in batch URL generation: {e}")
            return {'successful': [], 'failed': [], 'total': 0}

# Convenience functions for easy integration
def generate_enhanced_pin_url(base_url: str, 
                            campaign_id: str = None,
                            ad_id: str = None,
                            pin_id: str = None,
                            **kwargs) -> str:
    """
    Convenience function to generate enhanced pin URL
    
    Args:
        base_url: Base destination URL
        campaign_id: Pinterest campaign ID
        ad_id: Pinterest ad ID
        pin_id: Pinterest pin ID
        **kwargs: Additional parameters
        
    Returns:
        Enhanced URL with comprehensive tracking
    """
    generator = PinterestURLGenerator()
    return generator.generate_pin_url(
        base_url=base_url,
        campaign_id=campaign_id,
        ad_id=ad_id,
        pin_id=pin_id,
        **kwargs
    )

def validate_url_generation(base_url: str, enhanced_url: str) -> Tuple[bool, str]:
    """
    Validate URL generation results
    
    Args:
        base_url: Original base URL
        enhanced_url: Generated enhanced URL
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if URL was enhanced
        if enhanced_url == base_url:
            return False, "URL was not enhanced"
        
        # Check URL validity
        is_valid, error_msg = validate_pinterest_url(enhanced_url)
        if not is_valid:
            return False, f"Enhanced URL is invalid: {error_msg}"
        
        # Check URL length
        if len(enhanced_url) > MAX_URL_LENGTH:
            return False, f"URL exceeds maximum length: {len(enhanced_url)} > {MAX_URL_LENGTH}"
        
        return True, "URL generation successful"
        
    except Exception as e:
        return False, f"Validation error: {e}"
