"""
Shopify Webhook Handler for Pinterest Conversion Tracking
========================================================

This module handles Shopify webhooks for server-side conversion validation
and Pinterest conversion tracking with proper attribution windows.

Features:
- Order creation webhook handling
- Order update webhook handling
- Order cancellation webhook handling
- Server-side conversion validation
- Pinterest conversion tracking
- Cross-device tracking
- Enhanced conversions with hashed customer data
"""

import os
import sys
import json
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify
import requests

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_conversion_tracking import PinterestConversionTracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Flask app for webhook handling
app = Flask(__name__)

# Configuration
SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN", "")
TRACK_AI_STORE_ID = os.getenv("TRACK_AI_STORE_ID", "pinterest_store")

class ShopifyWebhookHandler:
    """
    Shopify Webhook Handler for Pinterest Conversion Tracking
    
    Handles Shopify webhooks and triggers Pinterest conversion tracking
    with proper attribution windows and server-side validation.
    """
    
    def __init__(self):
        """Initialize Shopify webhook handler"""
        self.conversion_tracker = PinterestConversionTracker(
            access_token=PINTEREST_ACCESS_TOKEN,
            store_id=TRACK_AI_STORE_ID
        )
        logger.info("✅ Shopify webhook handler initialized")
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify Shopify webhook signature
        
        Args:
            payload: Webhook payload
            signature: Webhook signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not SHOPIFY_WEBHOOK_SECRET:
                logger.warning("⚠️ Shopify webhook secret not configured")
                return True  # Allow in development
            
            # Calculate expected signature
            expected_signature = hmac.new(
                SHOPIFY_WEBHOOK_SECRET.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if is_valid:
                logger.info("✅ Webhook signature verified")
            else:
                logger.warning("⚠️ Webhook signature verification failed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Error verifying webhook signature: {e}")
            return False
    
    def handle_order_creation(self, order_data: Dict[str, Any]) -> bool:
        """
        Handle order creation webhook
        
        Args:
            order_data: Shopify order data
            
        Returns:
            True if handling successful, False otherwise
        """
        try:
            logger.info(f"🛒 Handling order creation: {order_data.get('id')}")
            
            # Extract order information
            order_id = str(order_data.get("id", ""))
            order_value = float(order_data.get("total_price", 0))
            customer_email = order_data.get("customer", {}).get("email")
            customer_phone = order_data.get("customer", {}).get("phone")
            
            # Extract order items
            order_items = []
            for line_item in order_data.get("line_items", []):
                order_items.append({
                    "product_id": str(line_item.get("product_id", "")),
                    "variant_id": str(line_item.get("variant_id", "")),
                    "title": line_item.get("title", ""),
                    "quantity": int(line_item.get("quantity", 0)),
                    "price": float(line_item.get("price", 0))
                })
            
            # Extract session data from order attributes or note attributes
            session_data = self._extract_session_data_from_order(order_data)
            
            # Track purchase completion
            success = self.conversion_tracker.track_purchase_completion(
                order_id=order_id,
                order_value=order_value,
                order_items=order_items,
                customer_email=customer_email,
                customer_phone=customer_phone,
                session_data=session_data,
                user_agent=order_data.get("user_agent"),
                ip_address=order_data.get("browser_ip")
            )
            
            if success:
                logger.info(f"✅ Order creation tracked successfully: {order_id}")
            else:
                logger.warning(f"⚠️ Failed to track order creation: {order_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error handling order creation: {e}")
            return False
    
    def handle_order_update(self, order_data: Dict[str, Any]) -> bool:
        """
        Handle order update webhook
        
        Args:
            order_data: Shopify order data
            
        Returns:
            True if handling successful, False otherwise
        """
        try:
            logger.info(f"📝 Handling order update: {order_data.get('id')}")
            
            # Check if order was fulfilled or cancelled
            fulfillment_status = order_data.get("fulfillment_status")
            financial_status = order_data.get("financial_status")
            
            if fulfillment_status == "fulfilled":
                logger.info(f"✅ Order fulfilled: {order_data.get('id')}")
                # Track fulfillment event if needed
            elif financial_status == "refunded":
                logger.info(f"💰 Order refunded: {order_data.get('id')}")
                # Track refund event if needed
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling order update: {e}")
            return False
    
    def handle_order_cancellation(self, order_data: Dict[str, Any]) -> bool:
        """
        Handle order cancellation webhook
        
        Args:
            order_data: Shopify order data
            
        Returns:
            True if handling successful, False otherwise
        """
        try:
            logger.info(f"❌ Handling order cancellation: {order_data.get('id')}")
            
            # Track cancellation event if needed
            # This could be used for attribution analysis
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling order cancellation: {e}")
            return False
    
    def _extract_session_data_from_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract session data from order attributes
        
        Args:
            order_data: Shopify order data
            
        Returns:
            Dictionary with session data
        """
        try:
            # Check order attributes for UTM parameters
            order_attributes = order_data.get("note_attributes", [])
            session_data = {}
            
            for attr in order_attributes:
                name = attr.get("name", "").lower()
                value = attr.get("value", "")
                
                if name.startswith("utm_"):
                    session_data[name] = value
                elif name in ["track_ai_store_id", "track_ai_pixel_id", "track_ai_timestamp"]:
                    session_data[name] = value
            
            # If no UTM parameters found in order attributes, try to extract from referrer
            if not session_data.get("utm_source"):
                referrer = order_data.get("referring_site")
                if referrer:
                    session_data.update(self._extract_utm_from_referrer(referrer))
            
            logger.info(f"📊 Extracted session data: {session_data}")
            return session_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting session data: {e}")
            return {}
    
    def _extract_utm_from_referrer(self, referrer: str) -> Dict[str, str]:
        """
        Extract UTM parameters from referrer URL
        
        Args:
            referrer: Referrer URL
            
        Returns:
            Dictionary with UTM parameters
        """
        try:
            from urllib.parse import urlparse, parse_qs
            
            parsed_url = urlparse(referrer)
            query_params = parse_qs(parsed_url.query)
            
            utm_params = {}
            for key, value in query_params.items():
                if key.startswith("utm_"):
                    utm_params[key] = value[0] if value else ""
            
            return utm_params
            
        except Exception as e:
            logger.error(f"❌ Error extracting UTM from referrer: {e}")
            return {}

# Initialize webhook handler
webhook_handler = ShopifyWebhookHandler()

# Flask routes for webhook handling
@app.route('/webhooks/orders/create', methods=['POST'])
def handle_order_create_webhook():
    """Handle Shopify order creation webhook"""
    try:
        # Get request data
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Shopify-Hmac-Sha256', '')
        
        # Verify webhook signature
        if not webhook_handler.verify_webhook_signature(payload, signature):
            return jsonify({"error": "Invalid signature"}), 401
        
        # Parse order data
        order_data = json.loads(payload)
        
        # Handle order creation
        success = webhook_handler.handle_order_creation(order_data)
        
        if success:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error handling order create webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhooks/orders/updated', methods=['POST'])
def handle_order_update_webhook():
    """Handle Shopify order update webhook"""
    try:
        # Get request data
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Shopify-Hmac-Sha256', '')
        
        # Verify webhook signature
        if not webhook_handler.verify_webhook_signature(payload, signature):
            return jsonify({"error": "Invalid signature"}), 401
        
        # Parse order data
        order_data = json.loads(payload)
        
        # Handle order update
        success = webhook_handler.handle_order_update(order_data)
        
        if success:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error handling order update webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhooks/orders/cancelled', methods=['POST'])
def handle_order_cancellation_webhook():
    """Handle Shopify order cancellation webhook"""
    try:
        # Get request data
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Shopify-Hmac-Sha256', '')
        
        # Verify webhook signature
        if not webhook_handler.verify_webhook_signature(payload, signature):
            return jsonify({"error": "Invalid signature"}), 401
        
        # Parse order data
        order_data = json.loads(payload)
        
        # Handle order cancellation
        success = webhook_handler.handle_order_cancellation(order_data)
        
        if success:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error handling order cancellation webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhooks/orders/paid', methods=['POST'])
def handle_order_paid_webhook():
    """Handle Shopify order paid webhook"""
    try:
        # Get request data
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Shopify-Hmac-Sha256', '')
        
        # Verify webhook signature
        if not webhook_handler.verify_webhook_signature(payload, signature):
            return jsonify({"error": "Invalid signature"}), 401
        
        # Parse order data
        order_data = json.loads(payload)
        
        # Handle order paid (similar to order creation)
        success = webhook_handler.handle_order_creation(order_data)
        
        if success:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error handling order paid webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

@app.route('/conversion-funnel', methods=['GET'])
def get_conversion_funnel():
    """Get conversion funnel analysis"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get conversion funnel analysis
        funnel_data = webhook_handler.conversion_tracker.get_conversion_funnel_analysis(
            start_date=start_dt,
            end_date=end_dt
        )
        
        return jsonify(funnel_data), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting conversion funnel: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/roi-analysis', methods=['GET'])
def get_roi_analysis():
    """Get ROI analysis"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get ROI analysis
        roi_data = webhook_handler.conversion_tracker.get_roi_analysis(
            start_date=start_dt,
            end_date=end_dt
        )
        
        return jsonify(roi_data), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting ROI analysis: {e}")
        return jsonify({"error": str(e)}), 500

# Run the Flask app
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Shopify webhook handler on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
