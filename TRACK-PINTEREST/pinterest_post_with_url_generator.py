"""
Enhanced Pinterest Posting with URL Generator Integration
========================================================

This module extends the Pinterest posting functionality with automatic
URL generation, tracking parameter appending, and comprehensive conversion tracking.

Features:
- Automatic URL generation with tracking parameters
- Pinterest API v5 integration for campaign and ad metadata
- Track AI pixel integration for all destination URLs
- URL validation and length management
- URL shortening service integration
"""

import os
import sys
import time
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_url_generator import PinterestURLGenerator, generate_enhanced_pin_url, validate_url_generation
from track_ai_integration import PinterestTrackAIIntegration

logger = logging.getLogger(__name__)

# Pinterest API Configuration
BASE_URL = "https://api.pinterest.com/v5"

def post_pin_with_enhanced_url(access_token: str, 
                              board_id: str, 
                              image_url: str, 
                              title: str, 
                              description: str, 
                              destination_url: str = None,
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
                              daily_budget: int = None) -> Optional[str]:
    """
    Post a pin to Pinterest with enhanced URL generation and tracking
    
    Args:
        access_token: Pinterest API access token
        board_id: Pinterest board ID
        image_url: Image URL for the pin
        title: Pin title
        description: Pin description
        destination_url: Base destination URL
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
        Pinterest pin ID if successful, None otherwise
    """
    try:
        logger.info(f"📌 Posting pin with enhanced URL generation")
        
        # Initialize URL generator
        url_generator = PinterestURLGenerator(access_token=access_token)
        
        # Generate enhanced destination URL with comprehensive tracking
        enhanced_destination_url = destination_url
        if destination_url:
            try:
                enhanced_destination_url = url_generator.generate_pin_url(
                    base_url=destination_url,
                    campaign_id=campaign_id,
                    ad_id=ad_id,
                    pin_id=pin_id,
                    campaign_name=campaign_name,
                    objective_type=objective_type,
                    launch_date=launch_date,
                    product_name=product_name,
                    product_type=product_type,
                    board_title=board_title,
                    pin_variant=pin_variant,
                    daily_budget=daily_budget
                )
                
                # Validate URL generation
                is_valid, error_msg = validate_url_generation(destination_url, enhanced_destination_url)
                if not is_valid:
                    logger.warning(f"⚠️ URL generation validation failed: {error_msg}")
                    enhanced_destination_url = destination_url
                else:
                    logger.info(f"✅ Enhanced URL generated successfully")
                    logger.info(f"   Original: {destination_url}")
                    logger.info(f"   Enhanced: {enhanced_destination_url}")
                
            except Exception as e:
                logger.error(f"❌ Error generating enhanced URL: {e}")
                enhanced_destination_url = destination_url

        # Create pin payload
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

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
            logger.info(f"🔗 Adding enhanced destination URL to pin: {enhanced_destination_url}")
        else:
            logger.info("ℹ️ No destination URL provided for pin")

        # Add rate limiting delay
        time.sleep(2)  # 2 second delay between requests

        # Post pin to Pinterest
        url = f"{BASE_URL}/pins"
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            pin_data = response.json()
            created_pin_id = pin_data.get("id")
            logger.info(f"✅ Pin posted successfully with enhanced URL: {created_pin_id}")
            
            # Log tracking information
            if enhanced_destination_url != destination_url:
                logger.info(f"📊 Tracking Parameters Added:")
                logger.info(f"   Campaign ID: {campaign_id}")
                logger.info(f"   Ad ID: {ad_id}")
                logger.info(f"   Pin ID: {created_pin_id}")
                logger.info(f"   Product: {product_name}")
                logger.info(f"   Board: {board_title}")
            
            return created_pin_id
        else:
            logger.error(f"❌ Failed to post pin: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error posting pin with enhanced URL: {e}")
        return None

def post_pin_batch_with_enhanced_urls(access_token: str,
                                     pins_data: list,
                                     campaign_id: str = None,
                                     campaign_name: str = None,
                                     objective_type: str = "WEB_CONVERSION",
                                     launch_date: str = None,
                                     daily_budget: int = None) -> Dict[str, Any]:
    """
    Post multiple pins with enhanced URL generation
    
    Args:
        access_token: Pinterest API access token
        pins_data: List of pin data dictionaries
        campaign_id: Pinterest campaign ID
        campaign_name: Campaign name
        objective_type: Campaign objective
        launch_date: Campaign launch date
        daily_budget: Daily budget in cents
        
    Returns:
        Dictionary with results summary
    """
    try:
        logger.info(f"📌 Posting {len(pins_data)} pins with enhanced URL generation")
        
        results = {
            'successful': [],
            'failed': [],
            'total': len(pins_data),
            'enhanced_urls': 0,
            'original_urls': 0
        }
        
        for i, pin_data in enumerate(pins_data):
            try:
                logger.info(f"📌 Processing pin {i+1}/{len(pins_data)} with enhanced URL generation")
                
                # Generate enhanced URL
                enhanced_url = generate_enhanced_pin_url(
                    base_url=pin_data.get('destination_url'),
                    campaign_id=campaign_id,
                    ad_id=pin_data.get('ad_id'),
                    pin_id=pin_data.get('pin_id'),
                    campaign_name=campaign_name,
                    objective_type=objective_type,
                    launch_date=launch_date,
                    product_name=pin_data.get('product_name'),
                    product_type=pin_data.get('product_type'),
                    board_title=pin_data.get('board_title'),
                    pin_variant=pin_data.get('pin_variant'),
                    daily_budget=daily_budget
                )
                
                # Track URL enhancement
                if enhanced_url != pin_data.get('destination_url'):
                    results['enhanced_urls'] += 1
                else:
                    results['original_urls'] += 1
                
                # Post pin with enhanced URL
                pin_id = post_pin_with_enhanced_url(
                    access_token=access_token,
                    board_id=pin_data.get('board_id'),
                    image_url=pin_data.get('image_url'),
                    title=pin_data.get('title'),
                    description=pin_data.get('description'),
                    destination_url=enhanced_url,
                    campaign_id=campaign_id,
                    ad_id=pin_data.get('ad_id'),
                    pin_id=pin_data.get('pin_id'),
                    campaign_name=campaign_name,
                    objective_type=objective_type,
                    launch_date=launch_date,
                    product_name=pin_data.get('product_name'),
                    product_type=pin_data.get('product_type'),
                    board_title=pin_data.get('board_title'),
                    pin_variant=pin_data.get('pin_variant'),
                    daily_budget=daily_budget
                )
                
                if pin_id:
                    results['successful'].append({
                        'pin_id': pin_id,
                        'product_name': pin_data.get('product_name'),
                        'original_url': pin_data.get('destination_url'),
                        'enhanced_url': enhanced_url,
                        'url_enhanced': enhanced_url != pin_data.get('destination_url')
                    })
                else:
                    results['failed'].append({
                        'product_name': pin_data.get('product_name'),
                        'error': 'Failed to post pin',
                        'original_url': pin_data.get('destination_url'),
                        'enhanced_url': enhanced_url
                    })
                    
            except Exception as e:
                logger.error(f"❌ Error processing pin {i+1}: {e}")
                results['failed'].append({
                    'product_name': pin_data.get('product_name'),
                    'error': str(e),
                    'original_url': pin_data.get('destination_url')
                })
        
        logger.info(f"🎯 Enhanced URL Pin Posting Results:")
        logger.info(f"   ✅ Successful: {len(results['successful'])}")
        logger.info(f"   ❌ Failed: {len(results['failed'])}")
        logger.info(f"   🔗 Enhanced URLs: {results['enhanced_urls']}")
        logger.info(f"   📄 Original URLs: {results['original_urls']}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error in batch pin posting with enhanced URLs: {e}")
        return {'successful': [], 'failed': [], 'total': 0, 'enhanced_urls': 0, 'original_urls': 0}

def test_url_generation(base_url: str, 
                      campaign_id: str = None,
                      ad_id: str = None,
                      pin_id: str = None,
                      **kwargs) -> Dict[str, Any]:
    """
    Test URL generation functionality
    
    Args:
        base_url: Base destination URL
        campaign_id: Pinterest campaign ID
        ad_id: Pinterest ad ID
        pin_id: Pinterest pin ID
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with test results
    """
    try:
        logger.info(f"🧪 Testing URL generation for: {base_url}")
        
        # Generate enhanced URL
        enhanced_url = generate_enhanced_pin_url(
            base_url=base_url,
            campaign_id=campaign_id,
            ad_id=ad_id,
            pin_id=pin_id,
            **kwargs
        )
        
        # Validate URL generation
        is_valid, error_msg = validate_url_generation(base_url, enhanced_url)
        
        test_results = {
            'original_url': base_url,
            'enhanced_url': enhanced_url,
            'is_valid': is_valid,
            'error_message': error_msg,
            'url_enhanced': enhanced_url != base_url,
            'length_original': len(base_url),
            'length_enhanced': len(enhanced_url),
            'length_increase': len(enhanced_url) - len(base_url),
            'campaign_id': campaign_id,
            'ad_id': ad_id,
            'pin_id': pin_id
        }
        
        logger.info(f"📊 URL Generation Test Results:")
        logger.info(f"   Original URL: {base_url}")
        logger.info(f"   Enhanced URL: {enhanced_url}")
        logger.info(f"   Valid: {is_valid}")
        logger.info(f"   Enhanced: {enhanced_url != base_url}")
        logger.info(f"   Length Increase: {len(enhanced_url) - len(base_url)} characters")
        
        return test_results
        
    except Exception as e:
        logger.error(f"❌ Error testing URL generation: {e}")
        return {
            'original_url': base_url,
            'enhanced_url': base_url,
            'is_valid': False,
            'error_message': str(e),
            'url_enhanced': False
        }

# Import original functions for backward compatibility
try:
    from pinterest_post import get_all_boards, search_board_by_name, get_or_create_board
    logger.info("✅ Original Pinterest functions imported for backward compatibility")
except ImportError:
    logger.warning("⚠️ Could not import original Pinterest functions")
