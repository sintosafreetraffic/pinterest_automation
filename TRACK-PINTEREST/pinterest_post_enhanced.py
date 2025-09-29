"""
Enhanced Pinterest Posting with Track AI Integration
===================================================

This module extends the original Pinterest posting functionality with
Track AI pixel integration for comprehensive conversion tracking.

Features:
- Track AI pixel integration for destination URLs
- UTM parameter generation for Pinterest campaigns
- Enhanced conversion tracking
- Cross-platform attribution
"""

import os
import time
import requests
import logging
from typing import Optional, Dict, Any
from track_ai_integration import PinterestTrackAIIntegration, generate_pinterest_track_ai_url

logger = logging.getLogger(__name__)

# Pinterest API Configuration
BASE_URL = "https://api.pinterest.com/v5"

def post_pin_with_track_ai(access_token: str, 
                          board_id: str, 
                          image_url: str, 
                          title: str, 
                          description: str, 
                          destination_url: str = None,
                          campaign_name: str = None,
                          objective_type: str = "WEB_CONVERSION",
                          launch_date: str = None,
                          product_name: str = None,
                          product_type: str = None,
                          board_title: str = None,
                          pin_variant: str = None,
                          campaign_id: str = None,
                          pin_id: str = None,
                          ad_id: str = None,
                          daily_budget: int = None) -> Optional[str]:
    """
    Post a pin to Pinterest with Track AI pixel integration
    
    Args:
        access_token: Pinterest API access token
        board_id: Pinterest board ID
        image_url: Image URL for the pin
        title: Pin title
        description: Pin description
        destination_url: Base destination URL
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
        Pinterest pin ID if successful, None otherwise
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Generate enhanced destination URL with Track AI pixel
        enhanced_destination_url = destination_url
        if destination_url and campaign_name and objective_type and launch_date:
            try:
                track_ai_integration = PinterestTrackAIIntegration()
                enhanced_destination_url = track_ai_integration.generate_enhanced_destination_url(
                    base_url=destination_url,
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
                
                # Validate URL length
                if not track_ai_integration.validate_url_length(enhanced_destination_url):
                    logger.warning("Enhanced URL too long, using fallback with essential parameters")
                    essential_params = {
                        'utm_source': 'pinterest',
                        'utm_medium': 'cpc' if objective_type == 'WEB_CONVERSION' else 'social',
                        'utm_campaign': f"{launch_date}_{campaign_name}_{objective_type}".lower().replace(' ', '_'),
                        'track_ai_store_id': track_ai_integration.store_id,
                        'track_ai_pixel_id': track_ai_integration.pixel_id
                    }
                    enhanced_destination_url = track_ai_integration.create_fallback_url(
                        destination_url, essential_params
                    )
                
                logger.info(f"Enhanced destination URL with Track AI: {enhanced_destination_url}")
                
            except Exception as e:
                logger.error(f"Error generating Track AI URL: {e}")
                enhanced_destination_url = destination_url

        payload = {
            "board_id": board_id,
            "title": title[:100],
            "alt_text": description[:500],
            "description": description[:500],
            "media_source": {
                "source_type": "image_url",
                "url": image_url
            },
            "call_to_action": "ON_SALE"
        }
        
        # Add enhanced destination URL (link) if provided
        if enhanced_destination_url:
            payload["link"] = enhanced_destination_url
            logger.info(f"Adding Track AI enhanced destination URL to pin: {enhanced_destination_url}")
        else:
            logger.info("No destination URL provided for pin")

        # Add rate limiting delay
        time.sleep(2)  # 2 second delay between requests

        url = f"{BASE_URL}/pins"
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            pin_data = response.json()
            pin_id = pin_data.get("id")
            logger.info(f"✅ Pin posted successfully with Track AI integration: {pin_id}")
            return pin_id
        else:
            logger.error(f"❌ Failed to post pin: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error posting pin with Track AI: {e}")
        return None

def post_pin_batch_with_track_ai(access_token: str,
                                pins_data: list,
                                campaign_name: str = None,
                                objective_type: str = "WEB_CONVERSION",
                                launch_date: str = None,
                                daily_budget: int = None) -> Dict[str, Any]:
    """
    Post multiple pins with Track AI integration
    
    Args:
        access_token: Pinterest API access token
        pins_data: List of pin data dictionaries
        campaign_name: Pinterest campaign name
        objective_type: Campaign objective
        launch_date: Campaign launch date
        daily_budget: Daily budget in cents
        
    Returns:
        Dictionary with results summary
    """
    results = {
        'successful': [],
        'failed': [],
        'total': len(pins_data)
    }
    
    for i, pin_data in enumerate(pins_data):
        try:
            logger.info(f"Posting pin {i+1}/{len(pins_data)} with Track AI integration")
            
            pin_id = post_pin_with_track_ai(
                access_token=access_token,
                board_id=pin_data.get('board_id'),
                image_url=pin_data.get('image_url'),
                title=pin_data.get('title'),
                description=pin_data.get('description'),
                destination_url=pin_data.get('destination_url'),
                campaign_name=campaign_name,
                objective_type=objective_type,
                launch_date=launch_date,
                product_name=pin_data.get('product_name'),
                product_type=pin_data.get('product_type'),
                board_title=pin_data.get('board_title'),
                pin_variant=pin_data.get('pin_variant'),
                campaign_id=pin_data.get('campaign_id'),
                pin_id=pin_data.get('pin_id'),
                ad_id=pin_data.get('ad_id'),
                daily_budget=daily_budget
            )
            
            if pin_id:
                results['successful'].append({
                    'pin_id': pin_id,
                    'product_name': pin_data.get('product_name'),
                    'destination_url': pin_data.get('destination_url')
                })
            else:
                results['failed'].append({
                    'product_name': pin_data.get('product_name'),
                    'error': 'Failed to post pin'
                })
                
        except Exception as e:
            logger.error(f"Error posting pin {i+1}: {e}")
            results['failed'].append({
                'product_name': pin_data.get('product_name'),
                'error': str(e)
            })
    
    logger.info(f"Track AI Pin Posting Results: {len(results['successful'])} successful, {len(results['failed'])} failed")
    return results

def validate_track_ai_integration() -> Dict[str, Any]:
    """
    Validate Track AI integration configuration
    
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'track_ai_endpoint': os.getenv("TRACK_AI_ENDPOINT"),
        'track_ai_store_id': os.getenv("TRACK_AI_STORE_ID"),
        'track_ai_pixel_id': os.getenv("TRACK_AI_PIXEL_ID"),
        'is_configured': False,
        'missing_config': []
    }
    
    required_configs = ['TRACK_AI_ENDPOINT', 'TRACK_AI_STORE_ID', 'TRACK_AI_PIXEL_ID']
    
    for config in required_configs:
        if not os.getenv(config):
            validation_results['missing_config'].append(config)
    
    validation_results['is_configured'] = len(validation_results['missing_config']) == 0
    
    return validation_results

# Import original functions for backward compatibility
try:
    from pinterest_post import get_all_boards, search_board_by_name, get_or_create_board
    logger.info("✅ Original Pinterest functions imported for backward compatibility")
except ImportError:
    logger.warning("⚠️ Could not import original Pinterest functions")
