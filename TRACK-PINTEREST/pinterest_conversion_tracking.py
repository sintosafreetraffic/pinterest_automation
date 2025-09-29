"""
Pinterest Conversion Tracking Implementation
===========================================

This module implements comprehensive conversion tracking for Pinterest campaigns
using Track AI's conversion tracking API with proper attribution windows,
server-side validation, and enhanced conversion tracking.

Features:
- Product view tracking
- Add to cart tracking
- Checkout initiation tracking
- Purchase completion tracking
- Attribution windows (30-day click, 24-hour view)
- Server-side conversion validation
- Cross-device tracking
- Enhanced conversions with hashed customer data
- Value tracking for ROI calculations
- Conversion funnel analysis
"""

import os
import sys
import json
import time
import hashlib
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import hmac
import base64

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_track_ai_config import PinterestTrackAIConfig
from track_ai_integration import PinterestTrackAIIntegration

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Pinterest API Configuration
PINTEREST_API_BASE = "https://api.pinterest.com/v5"
SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")
TRACK_AI_ENDPOINT = os.getenv("TRACK_AI_ENDPOINT", "https://track.ai.yourdomain.com/api/event/track")

class PinterestConversionTracker:
    """
    Pinterest Conversion Tracking Manager
    
    Handles comprehensive conversion tracking for Pinterest campaigns including
    product views, add to cart, checkout initiation, and purchase completion.
    """
    
    def __init__(self, access_token: str = None, store_id: str = None):
        """
        Initialize Pinterest Conversion Tracker
        
        Args:
            access_token: Pinterest API access token
            store_id: Track AI store ID
        """
        self.access_token = access_token or os.getenv("PINTEREST_ACCESS_TOKEN")
        self.store_id = store_id or os.getenv("TRACK_AI_STORE_ID", "pinterest_store")
        self.track_ai_integration = PinterestTrackAIIntegration()
        self.track_ai_config = PinterestTrackAIConfig(store_id=self.store_id)
        
        # Attribution windows
        self.click_attribution_window = 30  # 30 days
        self.view_attribution_window = 1     # 24 hours
        
        logger.info(f"✅ Pinterest Conversion Tracker initialized for store: {self.store_id}")
    
    def track_product_view(self, 
                          product_id: str,
                          product_name: str,
                          product_price: float,
                          product_url: str,
                          session_data: Dict[str, Any],
                          user_agent: str = None,
                          ip_address: str = None) -> bool:
        """
        Track product view event
        
        Args:
            product_id: Shopify product ID
            product_name: Product name
            product_price: Product price
            product_url: Product URL
            session_data: Session data with UTM parameters
            user_agent: User agent string
            ip_address: User IP address
            
        Returns:
            True if tracking successful, False otherwise
        """
        try:
            logger.info(f"📊 Tracking product view: {product_name}")
            
            # Check if traffic is from Pinterest
            if not self._is_pinterest_traffic(session_data):
                logger.info("ℹ️ Not Pinterest traffic, skipping Pinterest conversion tracking")
                return True
            
            # Extract Pinterest metadata
            pinterest_metadata = self._extract_pinterest_metadata(session_data)
            
            # Create conversion event
            conversion_event = {
                "event_type": "product_view",
                "product_id": product_id,
                "product_name": product_name,
                "product_price": product_price,
                "product_url": product_url,
                "session_data": session_data,
                "pinterest_metadata": pinterest_metadata,
                "timestamp": datetime.now().isoformat(),
                "user_agent": user_agent,
                "ip_address": ip_address,
                "attribution_window": self.click_attribution_window,
                "conversion_value": product_price
            }
            
            # Send to Track AI
            success = self._send_to_track_ai(conversion_event)
            
            if success:
                logger.info(f"✅ Product view tracked successfully: {product_name}")
            else:
                logger.warning(f"⚠️ Failed to track product view: {product_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error tracking product view: {e}")
            return False
    
    def track_add_to_cart(self,
                         product_id: str,
                         product_name: str,
                         product_price: float,
                         quantity: int,
                         session_data: Dict[str, Any],
                         user_agent: str = None,
                         ip_address: str = None) -> bool:
        """
        Track add to cart event
        
        Args:
            product_id: Shopify product ID
            product_name: Product name
            product_price: Product price
            quantity: Quantity added to cart
            session_data: Session data with UTM parameters
            user_agent: User agent string
            ip_address: User IP address
            
        Returns:
            True if tracking successful, False otherwise
        """
        try:
            logger.info(f"🛒 Tracking add to cart: {product_name} (qty: {quantity})")
            
            # Check if traffic is from Pinterest
            if not self._is_pinterest_traffic(session_data):
                logger.info("ℹ️ Not Pinterest traffic, skipping Pinterest conversion tracking")
                return True
            
            # Extract Pinterest metadata
            pinterest_metadata = self._extract_pinterest_metadata(session_data)
            
            # Calculate conversion value
            conversion_value = product_price * quantity
            
            # Create conversion event
            conversion_event = {
                "event_type": "add_to_cart",
                "product_id": product_id,
                "product_name": product_name,
                "product_price": product_price,
                "quantity": quantity,
                "conversion_value": conversion_value,
                "session_data": session_data,
                "pinterest_metadata": pinterest_metadata,
                "timestamp": datetime.now().isoformat(),
                "user_agent": user_agent,
                "ip_address": ip_address,
                "attribution_window": self.click_attribution_window
            }
            
            # Send to Track AI
            success = self._send_to_track_ai(conversion_event)
            
            if success:
                logger.info(f"✅ Add to cart tracked successfully: {product_name}")
            else:
                logger.warning(f"⚠️ Failed to track add to cart: {product_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error tracking add to cart: {e}")
            return False
    
    def track_checkout_initiation(self,
                                 cart_value: float,
                                 cart_items: List[Dict[str, Any]],
                                 session_data: Dict[str, Any],
                                 user_agent: str = None,
                                 ip_address: str = None) -> bool:
        """
        Track checkout initiation event
        
        Args:
            cart_value: Total cart value
            cart_items: List of cart items
            session_data: Session data with UTM parameters
            user_agent: User agent string
            ip_address: User IP address
            
        Returns:
            True if tracking successful, False otherwise
        """
        try:
            logger.info(f"💳 Tracking checkout initiation: €{cart_value:.2f}")
            
            # Check if traffic is from Pinterest
            if not self._is_pinterest_traffic(session_data):
                logger.info("ℹ️ Not Pinterest traffic, skipping Pinterest conversion tracking")
                return True
            
            # Extract Pinterest metadata
            pinterest_metadata = self._extract_pinterest_metadata(session_data)
            
            # Create conversion event
            conversion_event = {
                "event_type": "checkout_initiation",
                "cart_value": cart_value,
                "cart_items": cart_items,
                "conversion_value": cart_value,
                "session_data": session_data,
                "pinterest_metadata": pinterest_metadata,
                "timestamp": datetime.now().isoformat(),
                "user_agent": user_agent,
                "ip_address": ip_address,
                "attribution_window": self.click_attribution_window
            }
            
            # Send to Track AI
            success = self._send_to_track_ai(conversion_event)
            
            if success:
                logger.info(f"✅ Checkout initiation tracked successfully: €{cart_value:.2f}")
            else:
                logger.warning(f"⚠️ Failed to track checkout initiation: €{cart_value:.2f}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error tracking checkout initiation: {e}")
            return False
    
    def track_purchase_completion(self,
                                order_id: str,
                                order_value: float,
                                order_items: List[Dict[str, Any]],
                                session_data: Dict[str, Any],
                                customer_email: str = None,
                                customer_phone: str = None,
                                user_agent: str = None,
                                ip_address: str = None) -> bool:
        """
        Track purchase completion event with enhanced conversions
        
        Args:
            order_id: Shopify order ID
            order_value: Total order value
            order_items: List of order items
            customer_email: Customer email (for enhanced conversions)
            customer_phone: Customer phone (for enhanced conversions)
            session_data: Session data with UTM parameters
            user_agent: User agent string
            ip_address: User IP address
            
        Returns:
            True if tracking successful, False otherwise
        """
        try:
            logger.info(f"🎉 Tracking purchase completion: Order {order_id} - €{order_value:.2f}")
            
            # Check if traffic is from Pinterest
            if not self._is_pinterest_traffic(session_data):
                logger.info("ℹ️ Not Pinterest traffic, skipping Pinterest conversion tracking")
                return True
            
            # Extract Pinterest metadata
            pinterest_metadata = self._extract_pinterest_metadata(session_data)
            
            # Create enhanced conversion event with hashed customer data
            conversion_event = {
                "event_type": "purchase",
                "order_id": order_id,
                "order_value": order_value,
                "order_items": order_items,
                "conversion_value": order_value,
                "session_data": session_data,
                "pinterest_metadata": pinterest_metadata,
                "timestamp": datetime.now().isoformat(),
                "user_agent": user_agent,
                "ip_address": ip_address,
                "attribution_window": self.click_attribution_window,
                "enhanced_conversions": {
                    "hashed_email": self._hash_customer_data(customer_email) if customer_email else None,
                    "hashed_phone": self._hash_customer_data(customer_phone) if customer_phone else None,
                    "customer_data_available": bool(customer_email or customer_phone)
                }
            }
            
            # Send to Track AI
            success = self._send_to_track_ai(conversion_event)
            
            if success:
                logger.info(f"✅ Purchase completion tracked successfully: Order {order_id}")
                
                # Send to Pinterest API for conversion tracking
                pinterest_success = self._send_to_pinterest_api(conversion_event)
                if pinterest_success:
                    logger.info(f"✅ Pinterest API conversion tracking successful: Order {order_id}")
                else:
                    logger.warning(f"⚠️ Pinterest API conversion tracking failed: Order {order_id}")
            else:
                logger.warning(f"⚠️ Failed to track purchase completion: Order {order_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error tracking purchase completion: {e}")
            return False
    
    def _is_pinterest_traffic(self, session_data: Dict[str, Any]) -> bool:
        """
        Check if traffic is from Pinterest
        
        Args:
            session_data: Session data with UTM parameters
            
        Returns:
            True if traffic is from Pinterest, False otherwise
        """
        utm_source = session_data.get("utm_source")
        utm_medium = session_data.get("utm_medium")
        
        return (
            utm_source == "pinterest" and
            utm_medium in ["cpc", "social", "paid_social"]
        )
    
    def _extract_pinterest_metadata(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract Pinterest metadata from session data
        
        Args:
            session_data: Session data with UTM parameters
            
        Returns:
            Dictionary with Pinterest metadata
        """
        return {
            "utm_source": session_data.get("utm_source"),
            "utm_medium": session_data.get("utm_medium"),
            "utm_campaign": session_data.get("utm_campaign"),
            "utm_campaign_id": session_data.get("utm_campaign_id"),
            "utm_pin_id": session_data.get("utm_pin_id"),
            "utm_ad_id": session_data.get("utm_ad_id"),
            "utm_term": session_data.get("utm_term"),
            "utm_content": session_data.get("utm_content"),
            "track_ai_store_id": session_data.get("track_ai_store_id"),
            "track_ai_pixel_id": session_data.get("track_ai_pixel_id"),
            "track_ai_timestamp": session_data.get("track_ai_timestamp")
        }
    
    def _hash_customer_data(self, customer_data: str) -> str:
        """
        Hash customer data for enhanced conversions (GDPR/CCPA compliant)
        
        Args:
            customer_data: Customer email or phone
            
        Returns:
            Hashed customer data
        """
        if not customer_data:
            return None
        
        # Normalize data (lowercase, trim)
        normalized_data = customer_data.lower().strip()
        
        # Hash using SHA-256
        hashed_data = hashlib.sha256(normalized_data.encode()).hexdigest()
        
        return hashed_data
    
    def _send_to_track_ai(self, conversion_event: Dict[str, Any]) -> bool:
        """
        Send conversion event to Track AI
        
        Args:
            conversion_event: Conversion event data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use Track AI integration to send event
            success = self.track_ai_integration.track_conversion_event(
                event_type=conversion_event["event_type"],
                conversion_value=conversion_event.get("conversion_value", 0),
                session_data=conversion_event["session_data"],
                pinterest_metadata=conversion_event["pinterest_metadata"],
                enhanced_conversions=conversion_event.get("enhanced_conversions"),
                timestamp=conversion_event["timestamp"]
            )
            
            if success:
                logger.info(f"✅ Conversion event sent to Track AI: {conversion_event['event_type']}")
            else:
                logger.warning(f"⚠️ Failed to send conversion event to Track AI: {conversion_event['event_type']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending to Track AI: {e}")
            return False
    
    def _send_to_pinterest_api(self, conversion_event: Dict[str, Any]) -> bool:
        """
        Send conversion event to Pinterest API
        
        Args:
            conversion_event: Conversion event data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.access_token:
                logger.warning("⚠️ Pinterest access token not available")
                return False
            
            # Get Pinterest ad account ID
            from pinterest_auth import get_ad_account_id
            ad_account_id = get_ad_account_id(self.access_token)
            
            if not ad_account_id:
                logger.warning("⚠️ Pinterest ad account ID not available")
                return False
            
            # Create Pinterest conversion event
            pinterest_event = {
                "event_name": "purchase",
                "event_time": int(datetime.now().timestamp()),
                "event_id": conversion_event["order_id"],
                "user_data": {
                    "em": conversion_event.get("enhanced_conversions", {}).get("hashed_email"),
                    "ph": conversion_event.get("enhanced_conversions", {}).get("hashed_phone")
                },
                "custom_data": {
                    "value": conversion_event["order_value"],
                    "currency": "EUR",
                    "content_ids": [item.get("product_id") for item in conversion_event["order_items"]],
                    "content_type": "product"
                },
                "action_source": "website"
            }
            
            # Send to Pinterest Conversions API
            url = f"{PINTEREST_API_BASE}/ad_accounts/{ad_account_id}/events"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=pinterest_event, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ Pinterest API conversion tracking successful")
                return True
            else:
                logger.warning(f"⚠️ Pinterest API conversion tracking failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending to Pinterest API: {e}")
            return False
    
    def get_conversion_funnel_analysis(self, 
                                     start_date: datetime = None,
                                     end_date: datetime = None) -> Dict[str, Any]:
        """
        Get conversion funnel analysis for Pinterest traffic
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Dictionary with funnel analysis data
        """
        try:
            logger.info("📊 Getting Pinterest conversion funnel analysis")
            
            # Default to last 30 days if no dates provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Get conversion data from Track AI
            funnel_data = self.track_ai_integration.get_conversion_funnel(
                store_id=self.store_id,
                start_date=start_date,
                end_date=end_date,
                traffic_source="pinterest"
            )
            
            if funnel_data:
                logger.info(f"✅ Conversion funnel analysis retrieved: {funnel_data.get('total_events', 0)} events")
                return funnel_data
            else:
                logger.warning("⚠️ No conversion funnel data available")
                return {"error": "No conversion funnel data available"}
                
        except Exception as e:
            logger.error(f"❌ Error getting conversion funnel analysis: {e}")
            return {"error": str(e)}
    
    def get_roi_analysis(self, 
                        start_date: datetime = None,
                        end_date: datetime = None) -> Dict[str, Any]:
        """
        Get ROI analysis for Pinterest campaigns
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Dictionary with ROI analysis data
        """
        try:
            logger.info("💰 Getting Pinterest ROI analysis")
            
            # Default to last 30 days if no dates provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Get ROI data from Track AI
            roi_data = self.track_ai_integration.get_roi_analysis(
                store_id=self.store_id,
                start_date=start_date,
                end_date=end_date,
                traffic_source="pinterest"
            )
            
            if roi_data:
                logger.info(f"✅ ROI analysis retrieved: €{roi_data.get('total_revenue', 0):.2f} revenue")
                return roi_data
            else:
                logger.warning("⚠️ No ROI data available")
                return {"error": "No ROI data available"}
                
        except Exception as e:
            logger.error(f"❌ Error getting ROI analysis: {e}")
            return {"error": str(e)}

# Convenience functions for easy integration
def track_pinterest_product_view(product_id: str,
                               product_name: str,
                               product_price: float,
                               product_url: str,
                               session_data: Dict[str, Any],
                               **kwargs) -> bool:
    """
    Track Pinterest product view event
    
    Args:
        product_id: Shopify product ID
        product_name: Product name
        product_price: Product price
        product_url: Product URL
        session_data: Session data with UTM parameters
        **kwargs: Additional parameters
        
    Returns:
        True if tracking successful, False otherwise
    """
    tracker = PinterestConversionTracker()
    return tracker.track_product_view(
        product_id=product_id,
        product_name=product_name,
        product_price=product_price,
        product_url=product_url,
        session_data=session_data,
        **kwargs
    )

def track_pinterest_add_to_cart(product_id: str,
                               product_name: str,
                               product_price: float,
                               quantity: int,
                               session_data: Dict[str, Any],
                               **kwargs) -> bool:
    """
    Track Pinterest add to cart event
    
    Args:
        product_id: Shopify product ID
        product_name: Product name
        product_price: Product price
        quantity: Quantity added to cart
        session_data: Session data with UTM parameters
        **kwargs: Additional parameters
        
    Returns:
        True if tracking successful, False otherwise
    """
    tracker = PinterestConversionTracker()
    return tracker.track_add_to_cart(
        product_id=product_id,
        product_name=product_name,
        product_price=product_price,
        quantity=quantity,
        session_data=session_data,
        **kwargs
    )

def track_pinterest_purchase(order_id: str,
                           order_value: float,
                           order_items: List[Dict[str, Any]],
                           session_data: Dict[str, Any],
                           customer_email: str = None,
                           customer_phone: str = None,
                           **kwargs) -> bool:
    """
    Track Pinterest purchase completion event
    
    Args:
        order_id: Shopify order ID
        order_value: Total order value
        order_items: List of order items
        session_data: Session data with UTM parameters
        customer_email: Customer email (for enhanced conversions)
        customer_phone: Customer phone (for enhanced conversions)
        **kwargs: Additional parameters
        
    Returns:
        True if tracking successful, False otherwise
    """
    tracker = PinterestConversionTracker()
    return tracker.track_purchase_completion(
        order_id=order_id,
        order_value=order_value,
        order_items=order_items,
        customer_email=customer_email,
        customer_phone=customer_phone,
        session_data=session_data,
        **kwargs
    )

# Example usage
if __name__ == "__main__":
    # Example session data from Pinterest traffic
    session_data = {
        "utm_source": "pinterest",
        "utm_medium": "cpc",
        "utm_campaign": "test_campaign",
        "utm_campaign_id": "123456789",
        "utm_pin_id": "111222333",
        "utm_ad_id": "987654321",
        "track_ai_store_id": "pinterest_store",
        "track_ai_pixel_id": "pinterest_pixel"
    }
    
    # Track product view
    success = track_pinterest_product_view(
        product_id="12345",
        product_name="Test Product",
        product_price=29.99,
        product_url="https://store.myshopify.com/products/test-product",
        session_data=session_data
    )
    
    if success:
        print("✅ Product view tracked successfully")
    else:
        print("❌ Failed to track product view")
