"""
Track AI Integration for Pinterest Automation
============================================

This module provides Track AI pixel integration for Pinterest campaigns,
enabling comprehensive conversion tracking and cross-platform attribution.

Features:
- UTM parameter generation for Pinterest campaigns
- Track AI pixel integration for destination URLs
- Cross-platform attribution tracking
- Conversion tracking with Pinterest metadata
"""

import os
import urllib.parse
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Track AI Configuration
TRACK_AI_ENDPOINT = os.getenv("TRACK_AI_ENDPOINT", "https://your-track-ai-domain.com/api/event/track")
TRACK_AI_STORE_ID = os.getenv("TRACK_AI_STORE_ID", "default_store")
TRACK_AI_PIXEL_ID = os.getenv("TRACK_AI_PIXEL_ID", "default_pixel")

class PinterestTrackAIIntegration:
    """
    Pinterest Track AI Integration Class
    
    Handles UTM parameter generation and Track AI pixel integration
    for Pinterest campaigns to enable comprehensive tracking.
    """
    
    def __init__(self, store_id: str = None, pixel_id: str = None):
        """
        Initialize Pinterest Track AI Integration
        
        Args:
            store_id: Track AI store identifier
            pixel_id: Track AI pixel identifier
        """
        self.store_id = store_id or TRACK_AI_STORE_ID
        self.pixel_id = pixel_id or TRACK_AI_PIXEL_ID
        self.endpoint = TRACK_AI_ENDPOINT
        
    def generate_utm_parameters(self, 
                              campaign_name: str,
                              objective_type: str,
                              launch_date: str,
                              product_name: str = None,
                              product_type: str = None,
                              board_title: str = None,
                              pin_variant: str = None,
                              campaign_id: str = None,
                              pin_id: str = None,
                              ad_id: str = None,
                              daily_budget: int = None) -> Dict[str, str]:
        """
        Generate comprehensive UTM parameters for Pinterest campaigns
        
        Args:
            campaign_name: Name of the Pinterest campaign
            objective_type: Campaign objective (WEB_CONVERSION, CONSIDERATION, etc.)
            launch_date: Campaign launch date
            product_name: Product name for term tracking
            product_type: Product type for term tracking
            board_title: Pinterest board title
            pin_variant: Pin variant identifier
            campaign_id: Pinterest campaign ID
            pin_id: Pinterest pin ID
            ad_id: Pinterest ad ID
            daily_budget: Daily budget in cents
            
        Returns:
            Dictionary of UTM parameters
        """
        try:
            # Core UTM parameters
            utm_params = {
                'utm_source': 'pinterest',
                'utm_medium': 'cpc' if objective_type == 'WEB_CONVERSION' else 'social',
                'utm_campaign': f"{launch_date}_{campaign_name}_{objective_type}".lower().replace(' ', '_').replace('-', '_'),
            }
            
            # Product-level tracking
            if product_name and product_type:
                utm_params['utm_term'] = f"{product_name}_{product_type}".lower().replace(' ', '_').replace('-', '_')
            
            # Content differentiation
            if board_title and pin_variant:
                utm_params['utm_content'] = f"{board_title}_{pin_variant}".lower().replace(' ', '_').replace('-', '_')
            
            # Pinterest-specific tracking
            if campaign_id:
                utm_params['utm_campaign_id'] = campaign_id
            if pin_id:
                utm_params['utm_pin_id'] = pin_id
            if ad_id:
                utm_params['utm_ad_id'] = ad_id
            
            # Budget tier tracking
            if daily_budget:
                budget_tier = f"{daily_budget/100:.0f}_euro"
                utm_params['utm_budget_tier'] = budget_tier
            
            # Track AI specific parameters
            utm_params['utm_track_ai_store'] = self.store_id
            utm_params['utm_track_ai_pixel'] = self.pixel_id
            
            logger.info(f"Generated UTM parameters: {utm_params}")
            return utm_params
            
        except Exception as e:
            logger.error(f"Error generating UTM parameters: {e}")
            return {}
    
    def generate_track_ai_pixel_url(self, 
                                  base_url: str,
                                  utm_params: Dict[str, str],
                                  event_type: str = "page_view") -> str:
        """
        Generate Track AI pixel URL with UTM parameters
        
        Args:
            base_url: Base destination URL
            utm_params: UTM parameters dictionary
            event_type: Track AI event type
            
        Returns:
            URL with Track AI pixel and UTM parameters
        """
        try:
            # Parse the base URL
            parsed_url = urllib.parse.urlparse(base_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Add UTM parameters
            for key, value in utm_params.items():
                query_params[key] = [value]
            
            # Add Track AI pixel parameters
            query_params['track_ai_event'] = [event_type]
            query_params['track_ai_store_id'] = [self.store_id]
            query_params['track_ai_pixel_id'] = [self.pixel_id]
            query_params['track_ai_timestamp'] = [str(int(datetime.now().timestamp()))]
            
            # Reconstruct URL
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            track_ai_url = urllib.parse.urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            logger.info(f"Generated Track AI pixel URL: {track_ai_url}")
            return track_ai_url
            
        except Exception as e:
            logger.error(f"Error generating Track AI pixel URL: {e}")
            return base_url
    
    def generate_enhanced_destination_url(self,
                                        base_url: str,
                                        campaign_name: str,
                                        objective_type: str,
                                        launch_date: str,
                                        product_name: str = None,
                                        product_type: str = None,
                                        board_title: str = None,
                                        pin_variant: str = None,
                                        campaign_id: str = None,
                                        pin_id: str = None,
                                        ad_id: str = None,
                                        daily_budget: int = None) -> str:
        """
        Generate enhanced destination URL with Track AI pixel and UTM parameters
        
        Args:
            base_url: Base product URL
            campaign_name: Pinterest campaign name
            objective_type: Campaign objective
            launch_date: Campaign launch date
            product_name: Product name
            product_type: Product type
            board_title: Pinterest board title
            pin_variant: Pin variant
            campaign_id: Pinterest campaign ID
            pin_id: Pinterest pin ID
            ad_id: Pinterest ad ID
            daily_budget: Daily budget in cents
            
        Returns:
            Enhanced URL with Track AI pixel and UTM parameters
        """
        try:
            # Generate UTM parameters
            utm_params = self.generate_utm_parameters(
                campaign_name=campaign_name,
                objective_type=objective_type,
                launch_date=launch_date,
                product_name=product_name,
                product_type=product_type,
                board_title=board_title,
                pin_variant=pin_variant,
                campaign_id=campaign_id,
                pin_id=pin_id,
                ad_id=ad_id,
                daily_budget=daily_budget
            )
            
            # Generate Track AI pixel URL
            track_ai_url = self.generate_track_ai_pixel_url(
                base_url=base_url,
                utm_params=utm_params,
                event_type="page_view"
            )
            
            logger.info(f"Enhanced destination URL generated: {track_ai_url}")
            return track_ai_url
            
        except Exception as e:
            logger.error(f"Error generating enhanced destination URL: {e}")
            return base_url
    
    def validate_url_length(self, url: str, max_length: int = 2048) -> bool:
        """
        Validate URL length to ensure it doesn't exceed browser limits
        
        Args:
            url: URL to validate
            max_length: Maximum URL length
            
        Returns:
            True if URL is within limits, False otherwise
        """
        return len(url) <= max_length
    
    def create_fallback_url(self, base_url: str, essential_params: Dict[str, str]) -> str:
        """
        Create fallback URL with only essential parameters if main URL is too long
        
        Args:
            base_url: Base destination URL
            essential_params: Essential UTM parameters
            
        Returns:
            Fallback URL with essential parameters only
        """
        try:
            parsed_url = urllib.parse.urlparse(base_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Add only essential parameters
            for key, value in essential_params.items():
                query_params[key] = [value]
            
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            fallback_url = urllib.parse.urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            logger.info(f"Created fallback URL: {fallback_url}")
            return fallback_url
            
        except Exception as e:
            logger.error(f"Error creating fallback URL: {e}")
            return base_url

# Convenience functions for easy integration
def generate_pinterest_track_ai_url(base_url: str, 
                                   campaign_name: str,
                                   objective_type: str,
                                   launch_date: str,
                                   **kwargs) -> str:
    """
    Convenience function to generate Pinterest Track AI URL
    
    Args:
        base_url: Base product URL
        campaign_name: Pinterest campaign name
        objective_type: Campaign objective
        launch_date: Campaign launch date
        **kwargs: Additional parameters
        
    Returns:
        Enhanced URL with Track AI pixel and UTM parameters
    """
    integration = PinterestTrackAIIntegration()
    return integration.generate_enhanced_destination_url(
        base_url=base_url,
        campaign_name=campaign_name,
        objective_type=objective_type,
        launch_date=launch_date,
        **kwargs
    )

def validate_pinterest_url(url: str) -> tuple[bool, str]:
    """
    Validate Pinterest URL for Track AI integration
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    integration = PinterestTrackAIIntegration()
    
    if not integration.validate_url_length(url):
        return False, "URL exceeds maximum length limit"
    
    if not url.startswith('http'):
        return False, "URL must start with http or https"
    
    return True, "URL is valid"
