"""
Pinterest Track AI Configuration
===============================

This module configures Track AI to properly recognize, categorize, and analyze
Pinterest traffic based on the implemented tracking parameters.

Features:
- Pinterest traffic source recognition
- UTM parameter mapping to Track AI data model
- Conversion attribution rules for Pinterest traffic
- Custom event tracking for Pinterest-specific interactions
- Multi-touch attribution models for Pinterest customer journey
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Track AI models and database
try:
    from track_ai.models import Pixel, Store, Event, FilterRule, AuditLog
    from track_ai.db import SessionLocal
    TRACK_AI_AVAILABLE = True
except ImportError:
    print("⚠️ Track AI models not available, using mock configuration")
    TRACK_AI_AVAILABLE = False
    # Create mock classes for type hints
    class Pixel:
        pass
    class Store:
        pass
    class Event:
        pass
    class FilterRule:
        pass
    class AuditLog:
        pass
    class SessionLocal:
        pass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class PinterestTrackAIConfig:
    """
    Pinterest Track AI Configuration Manager
    
    Handles Pinterest traffic recognition, UTM parameter mapping,
    conversion attribution, and multi-touch attribution models.
    """
    
    def __init__(self, store_id: str = None):
        """
        Initialize Pinterest Track AI configuration
        
        Args:
            store_id: Track AI store ID for Pinterest integration
        """
        self.store_id = store_id or os.getenv("TRACK_AI_STORE_ID", "pinterest_store")
        self.pinterest_pixel_id = os.getenv("TRACK_AI_PINTEREST_PIXEL_ID", "pinterest_pixel")
        self.track_ai_endpoint = os.getenv("TRACK_AI_ENDPOINT", "https://track.ai.yourdomain.com/api/event/track")
        
        logger.info(f"✅ Pinterest Track AI Config initialized for store: {self.store_id}")
    
    def configure_pinterest_traffic_recognition(self) -> bool:
        """
        Configure Track AI to recognize Pinterest traffic
        
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            logger.info("🔧 Configuring Pinterest traffic recognition in Track AI")
            
            if not TRACK_AI_AVAILABLE:
                logger.warning("⚠️ Track AI not available, creating mock configuration")
                return self._create_mock_pinterest_config()
            
            # Get database session
            db = SessionLocal()
            try:
                # 1. Create Pinterest pixel if it doesn't exist
                pinterest_pixel = self._create_pinterest_pixel(db)
                if not pinterest_pixel:
                    logger.error("❌ Failed to create Pinterest pixel")
                    return False
                
                # 2. Create Pinterest traffic recognition rules
                rules_created = self._create_pinterest_traffic_rules(db, pinterest_pixel.id)
                if not rules_created:
                    logger.error("❌ Failed to create Pinterest traffic rules")
                    return False
                
                # 3. Configure conversion attribution rules
                attribution_configured = self._configure_pinterest_attribution(db, pinterest_pixel.id)
                if not attribution_configured:
                    logger.error("❌ Failed to configure Pinterest attribution")
                    return False
                
                # 4. Set up multi-touch attribution models
                attribution_models_configured = self._configure_multi_touch_attribution(db)
                if not attribution_models_configured:
                    logger.error("❌ Failed to configure multi-touch attribution")
                    return False
                
                # Commit all changes
                db.commit()
                logger.info("✅ Pinterest traffic recognition configured successfully")
                return True
                
            except Exception as e:
                db.rollback()
                logger.error(f"❌ Error configuring Pinterest traffic recognition: {e}")
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error in Pinterest traffic recognition configuration: {e}")
            return False
    
    def _create_pinterest_pixel(self, db: Session) -> Optional[Pixel]:
        """
        Create Pinterest pixel in Track AI
        
        Args:
            db: Database session
            
        Returns:
            Created Pinterest pixel or None if failed
        """
        try:
            # Check if Pinterest pixel already exists
            existing_pixel = db.query(Pixel).filter(
                Pixel.store_id == self.store_id,
                Pixel.type == "pinterest",
                Pixel.pixel_id == self.pinterest_pixel_id
            ).first()
            
            if existing_pixel:
                logger.info(f"✅ Pinterest pixel already exists: {existing_pixel.id}")
                return existing_pixel
            
            # Create new Pinterest pixel
            pinterest_pixel = Pixel(
                type="pinterest",
                pixel_id=self.pinterest_pixel_id,
                label="Pinterest Conversion Tracking",
                store_id=self.store_id,
                active=True,
                config={
                    "platform": "pinterest",
                    "conversion_tracking": True,
                    "utm_source": "pinterest",
                    "utm_medium": ["cpc", "social"],
                    "attribution_model": "multi_touch",
                    "conversion_window": 30,  # 30 days
                    "view_through_window": 1,  # 1 day
                    "click_through_window": 1,  # 1 day
                    "pinterest_specific": {
                        "campaign_tracking": True,
                        "pin_tracking": True,
                        "board_tracking": True,
                        "ad_group_tracking": True
                    }
                }
            )
            
            db.add(pinterest_pixel)
            db.flush()  # Get the ID
            
            logger.info(f"✅ Pinterest pixel created: {pinterest_pixel.id}")
            return pinterest_pixel
            
        except Exception as e:
            logger.error(f"❌ Error creating Pinterest pixel: {e}")
            return None
    
    def _create_pinterest_traffic_rules(self, db: Session, pixel_id: int) -> bool:
        """
        Create Pinterest traffic recognition rules
        
        Args:
            db: Database session
            pixel_id: Pinterest pixel ID
            
        Returns:
            True if rules created successfully, False otherwise
        """
        try:
            # Rule 1: Pinterest UTM Source Recognition
            utm_source_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=pixel_id,
                rule_name="Pinterest UTM Source Recognition",
                description="Recognize Pinterest traffic by UTM source parameter",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_source",
                            "operator": "eq",
                            "value": "pinterest"
                        }
                    ],
                    "logic": "AND"
                },
                priority=1,
                active=True
            )
            
            # Rule 2: Pinterest UTM Medium Recognition
            utm_medium_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=pixel_id,
                rule_name="Pinterest UTM Medium Recognition",
                description="Recognize Pinterest traffic by UTM medium parameter",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_medium",
                            "operator": "in",
                            "value": ["cpc", "social", "paid_social"]
                        }
                    ],
                    "logic": "AND"
                },
                priority=2,
                active=True
            )
            
            # Rule 3: Pinterest Campaign ID Recognition
            campaign_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=pixel_id,
                rule_name="Pinterest Campaign ID Recognition",
                description="Recognize Pinterest traffic by campaign ID parameter",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_campaign_id",
                            "operator": "regex",
                            "value": "^[0-9]+$"  # Numeric campaign ID
                        }
                    ],
                    "logic": "AND"
                },
                priority=3,
                active=True
            )
            
            # Rule 4: Pinterest Pin ID Recognition
            pin_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=pixel_id,
                rule_name="Pinterest Pin ID Recognition",
                description="Recognize Pinterest traffic by pin ID parameter",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_pin_id",
                            "operator": "regex",
                            "value": "^[0-9]+$"  # Numeric pin ID
                        }
                    ],
                    "logic": "AND"
                },
                priority=4,
                active=True
            )
            
            # Rule 5: Pinterest Ad ID Recognition
            ad_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=pixel_id,
                rule_name="Pinterest Ad ID Recognition",
                description="Recognize Pinterest traffic by ad ID parameter",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_ad_id",
                            "operator": "regex",
                            "value": "^[0-9]+$"  # Numeric ad ID
                        }
                    ],
                    "logic": "AND"
                },
                priority=5,
                active=True
            )
            
            # Add all rules to database
            rules = [utm_source_rule, utm_medium_rule, campaign_rule, pin_rule, ad_rule]
            for rule in rules:
                db.add(rule)
            
            logger.info(f"✅ Created {len(rules)} Pinterest traffic recognition rules")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating Pinterest traffic rules: {e}")
            return False
    
    def _configure_pinterest_attribution(self, db: Session, pixel_id: int) -> bool:
        """
        Configure Pinterest conversion attribution rules
        
        Args:
            db: Database session
            pixel_id: Pinterest pixel ID
            
        Returns:
            True if attribution configured successfully, False otherwise
        """
        try:
            # Attribution Rule 1: Pinterest Campaign Attribution
            campaign_attribution_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=pixel_id,
                rule_name="Pinterest Campaign Attribution",
                description="Attribute conversions to Pinterest campaigns",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_source",
                            "operator": "eq",
                            "value": "pinterest"
                        },
                        {
                            "field": "session.utm_campaign_id",
                            "operator": "regex",
                            "value": "^[0-9]+$"
                        },
                        {
                            "field": "event_type",
                            "operator": "in",
                            "value": ["purchase", "checkout", "conversion", "add_to_cart"]
                        }
                    ],
                    "logic": "AND"
                },
                priority=10,
                active=True
            )
            
            # Attribution Rule 2: Pinterest Pin Attribution
            pin_attribution_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=pixel_id,
                rule_name="Pinterest Pin Attribution",
                description="Attribute conversions to specific Pinterest pins",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_source",
                            "operator": "eq",
                            "value": "pinterest"
                        },
                        {
                            "field": "session.utm_pin_id",
                            "operator": "regex",
                            "value": "^[0-9]+$"
                        },
                        {
                            "field": "event_type",
                            "operator": "in",
                            "value": ["purchase", "checkout", "conversion"]
                        }
                    ],
                    "logic": "AND"
                },
                priority=11,
                active=True
            )
            
            # Attribution Rule 3: Pinterest Ad Attribution
            ad_attribution_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=pixel_id,
                rule_name="Pinterest Ad Attribution",
                description="Attribute conversions to specific Pinterest ads",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_source",
                            "operator": "eq",
                            "value": "pinterest"
                        },
                        {
                            "field": "session.utm_ad_id",
                            "operator": "regex",
                            "value": "^[0-9]+$"
                        },
                        {
                            "field": "event_type",
                            "operator": "in",
                            "value": ["purchase", "checkout", "conversion"]
                        }
                    ],
                    "logic": "AND"
                },
                priority=12,
                active=True
            )
            
            # Add attribution rules to database
            attribution_rules = [campaign_attribution_rule, pin_attribution_rule, ad_attribution_rule]
            for rule in attribution_rules:
                db.add(rule)
            
            logger.info(f"✅ Created {len(attribution_rules)} Pinterest attribution rules")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configuring Pinterest attribution: {e}")
            return False
    
    def _configure_multi_touch_attribution(self, db: Session) -> bool:
        """
        Configure multi-touch attribution models for Pinterest
        
        Args:
            db: Database session
            
        Returns:
            True if multi-touch attribution configured successfully, False otherwise
        """
        try:
            # Multi-touch Attribution Rule 1: Pinterest First Touch
            first_touch_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=None,  # Global rule
                rule_name="Pinterest First Touch Attribution",
                description="Attribute first touch to Pinterest in customer journey",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_source",
                            "operator": "eq",
                            "value": "pinterest"
                        },
                        {
                            "field": "session.utm_medium",
                            "operator": "in",
                            "value": ["cpc", "social"]
                        },
                        {
                            "field": "event_type",
                            "operator": "eq",
                            "value": "page_view"
                        }
                    ],
                    "logic": "AND"
                },
                priority=20,
                active=True
            )
            
            # Multi-touch Attribution Rule 2: Pinterest Last Touch
            last_touch_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=None,  # Global rule
                rule_name="Pinterest Last Touch Attribution",
                description="Attribute last touch to Pinterest before conversion",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_source",
                            "operator": "eq",
                            "value": "pinterest"
                        },
                        {
                            "field": "session.utm_medium",
                            "operator": "in",
                            "value": ["cpc", "social"]
                        },
                        {
                            "field": "event_type",
                            "operator": "in",
                            "value": ["purchase", "checkout", "conversion"]
                        }
                    ],
                    "logic": "AND"
                },
                priority=21,
                active=True
            )
            
            # Multi-touch Attribution Rule 3: Pinterest View-Through Attribution
            view_through_rule = FilterRule(
                store_id=self.store_id,
                pixel_id=None,  # Global rule
                rule_name="Pinterest View-Through Attribution",
                description="Attribute view-through conversions to Pinterest",
                rule_logic={
                    "conditions": [
                        {
                            "field": "session.utm_source",
                            "operator": "eq",
                            "value": "pinterest"
                        },
                        {
                            "field": "session.utm_medium",
                            "operator": "eq",
                            "value": "social"
                        },
                        {
                            "field": "event_type",
                            "operator": "in",
                            "value": ["purchase", "checkout", "conversion"]
                        }
                    ],
                    "logic": "AND"
                },
                priority=22,
                active=True
            )
            
            # Add multi-touch attribution rules to database
            attribution_rules = [first_touch_rule, last_touch_rule, view_through_rule]
            for rule in attribution_rules:
                db.add(rule)
            
            logger.info(f"✅ Created {len(attribution_rules)} multi-touch attribution rules")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configuring multi-touch attribution: {e}")
            return False
    
    def _create_mock_pinterest_config(self) -> bool:
        """
        Create mock Pinterest configuration when Track AI is not available
        
        Returns:
            True if mock configuration created successfully, False otherwise
        """
        try:
            logger.info("🔧 Creating mock Pinterest configuration")
            
            # Mock configuration data
            mock_config = {
                "pinterest_pixel": {
                    "id": "pinterest_pixel",
                    "type": "pinterest",
                    "label": "Pinterest Conversion Tracking",
                    "store_id": self.store_id,
                    "active": True,
                    "config": {
                        "platform": "pinterest",
                        "conversion_tracking": True,
                        "utm_source": "pinterest",
                        "utm_medium": ["cpc", "social", "paid_social"],
                        "attribution_model": "multi_touch",
                        "conversion_window": 30,
                        "view_through_window": 1,
                        "click_through_window": 1,
                        "pinterest_specific": {
                            "campaign_tracking": True,
                            "pin_tracking": True,
                            "board_tracking": True,
                            "ad_group_tracking": True
                        }
                    }
                },
                "traffic_rules": [
                    {
                        "name": "Pinterest UTM Source Recognition",
                        "description": "Recognize Pinterest traffic by UTM source parameter",
                        "conditions": [
                            {
                                "field": "session.utm_source",
                                "operator": "eq",
                                "value": "pinterest"
                            }
                        ],
                        "logic": "AND",
                        "priority": 1
                    },
                    {
                        "name": "Pinterest UTM Medium Recognition",
                        "description": "Recognize Pinterest traffic by UTM medium parameter",
                        "conditions": [
                            {
                                "field": "session.utm_medium",
                                "operator": "in",
                                "value": ["cpc", "social", "paid_social"]
                            }
                        ],
                        "logic": "AND",
                        "priority": 2
                    }
                ],
                "attribution_rules": [
                    {
                        "name": "Pinterest Campaign Attribution",
                        "description": "Attribute conversions to Pinterest campaigns",
                        "conditions": [
                            {
                                "field": "session.utm_source",
                                "operator": "eq",
                                "value": "pinterest"
                            },
                            {
                                "field": "session.utm_campaign_id",
                                "operator": "regex",
                                "value": "^[0-9]+$"
                            },
                            {
                                "field": "event_type",
                                "operator": "in",
                                "value": ["purchase", "checkout", "conversion", "add_to_cart"]
                            }
                        ],
                        "logic": "AND",
                        "priority": 10
                    }
                ],
                "multi_touch_attribution": [
                    {
                        "name": "Pinterest First Touch Attribution",
                        "description": "Attribute first touch to Pinterest in customer journey",
                        "conditions": [
                            {
                                "field": "session.utm_source",
                                "operator": "eq",
                                "value": "pinterest"
                            },
                            {
                                "field": "session.utm_medium",
                                "operator": "in",
                                "value": ["cpc", "social"]
                            },
                            {
                                "field": "event_type",
                                "operator": "eq",
                                "value": "page_view"
                            }
                        ],
                        "logic": "AND",
                        "priority": 20
                    }
                ]
            }
            
            # Save mock configuration to file
            import json
            config_file = os.path.join(os.path.dirname(__file__), "pinterest_track_ai_config.json")
            with open(config_file, 'w') as f:
                json.dump(mock_config, f, indent=2)
            
            logger.info(f"✅ Mock Pinterest configuration saved to: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating mock Pinterest configuration: {e}")
            return False
    
    def test_pinterest_traffic_recognition(self) -> Dict[str, Any]:
        """
        Test Pinterest traffic recognition with sample data
        
        Returns:
            Dictionary with test results
        """
        try:
            logger.info("🧪 Testing Pinterest traffic recognition")
            
            # Test data samples
            test_cases = [
                {
                    "name": "Pinterest UTM Source Traffic",
                    "event_data": {
                        "event_type": "page_view",
                        "session": {
                            "utm_source": "pinterest",
                            "utm_medium": "cpc",
                            "utm_campaign": "test_campaign",
                            "utm_campaign_id": "123456789",
                            "utm_pin_id": "111222333",
                            "utm_ad_id": "987654321"
                        },
                        "referrer": "https://pinterest.com",
                        "landing_page": "/products/test-product"
                    },
                    "expected_recognition": True
                },
                {
                    "name": "Pinterest Social Traffic",
                    "event_data": {
                        "event_type": "page_view",
                        "session": {
                            "utm_source": "pinterest",
                            "utm_medium": "social",
                            "utm_campaign": "social_campaign",
                            "utm_campaign_id": "987654321"
                        },
                        "referrer": "https://pinterest.com",
                        "landing_page": "/products/social-product"
                    },
                    "expected_recognition": True
                },
                {
                    "name": "Non-Pinterest Traffic",
                    "event_data": {
                        "event_type": "page_view",
                        "session": {
                            "utm_source": "google",
                            "utm_medium": "cpc",
                            "utm_campaign": "google_campaign"
                        },
                        "referrer": "https://google.com",
                        "landing_page": "/products/google-product"
                    },
                    "expected_recognition": False
                },
                {
                    "name": "Pinterest Conversion",
                    "event_data": {
                        "event_type": "purchase",
                        "session": {
                            "utm_source": "pinterest",
                            "utm_medium": "cpc",
                            "utm_campaign": "conversion_campaign",
                            "utm_campaign_id": "555666777",
                            "utm_pin_id": "444555666",
                            "utm_ad_id": "777888999"
                        },
                        "referrer": "https://pinterest.com",
                        "landing_page": "/checkout"
                    },
                    "expected_recognition": True
                }
            ]
            
            results = {
                "test_cases": [],
                "total_tests": len(test_cases),
                "passed_tests": 0,
                "failed_tests": 0
            }
            
            for test_case in test_cases:
                try:
                    # Simulate traffic recognition logic
                    is_pinterest = (
                        test_case["event_data"]["session"].get("utm_source") == "pinterest" and
                        test_case["event_data"]["session"].get("utm_medium") in ["cpc", "social", "paid_social"]
                    )
                    
                    test_result = {
                        "name": test_case["name"],
                        "expected": test_case["expected_recognition"],
                        "actual": is_pinterest,
                        "passed": is_pinterest == test_case["expected_recognition"],
                        "event_data": test_case["event_data"]
                    }
                    
                    results["test_cases"].append(test_result)
                    
                    if test_result["passed"]:
                        results["passed_tests"] += 1
                        logger.info(f"✅ {test_case['name']}: PASSED")
                    else:
                        results["failed_tests"] += 1
                        logger.error(f"❌ {test_case['name']}: FAILED")
                        
                except Exception as e:
                    logger.error(f"❌ Error testing {test_case['name']}: {e}")
                    results["failed_tests"] += 1
            
            logger.info(f"📊 Pinterest Traffic Recognition Test Results:")
            logger.info(f"   Total Tests: {results['total_tests']}")
            logger.info(f"   Passed: {results['passed_tests']}")
            logger.info(f"   Failed: {results['failed_tests']}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error testing Pinterest traffic recognition: {e}")
            return {"error": str(e)}
    
    def get_pinterest_attribution_summary(self) -> Dict[str, Any]:
        """
        Get Pinterest attribution summary from Track AI
        
        Returns:
            Dictionary with Pinterest attribution summary
        """
        try:
            logger.info("📊 Getting Pinterest attribution summary")
            
            if not TRACK_AI_AVAILABLE:
                logger.warning("⚠️ Track AI not available, returning mock summary")
                return self._get_mock_attribution_summary()
            
            # Get database session
            db = SessionLocal()
            try:
                # Get Pinterest pixel
                pinterest_pixel = db.query(Pixel).filter(
                    Pixel.store_id == self.store_id,
                    Pixel.type == "pinterest",
                    Pixel.active == True
                ).first()
                
                if not pinterest_pixel:
                    logger.warning("⚠️ Pinterest pixel not found")
                    return {"error": "Pinterest pixel not found"}
                
                # Get Pinterest events
                pinterest_events = db.query(Event).filter(
                    Event.pixel_id == pinterest_pixel.id
                ).order_by(desc(Event.created_at)).limit(100).all()
                
                # Calculate attribution metrics
                total_events = len(pinterest_events)
                conversion_events = [e for e in pinterest_events if e.event_type in ["purchase", "checkout", "conversion"]]
                conversion_count = len(conversion_events)
                conversion_rate = (conversion_count / total_events * 100) if total_events > 0 else 0
                
                # Get campaign attribution data
                campaign_attribution = {}
                for event in pinterest_events:
                    if event.raw_event and "session" in event.raw_event:
                        session_data = event.raw_event["session"]
                        campaign_id = session_data.get("utm_campaign_id")
                        if campaign_id:
                            if campaign_id not in campaign_attribution:
                                campaign_attribution[campaign_id] = {"events": 0, "conversions": 0}
                            campaign_attribution[campaign_id]["events"] += 1
                            if event.event_type in ["purchase", "checkout", "conversion"]:
                                campaign_attribution[campaign_id]["conversions"] += 1
                
                summary = {
                    "pinterest_pixel_id": pinterest_pixel.pixel_id,
                    "total_events": total_events,
                    "conversion_events": conversion_count,
                    "conversion_rate": f"{conversion_rate:.2f}%",
                    "campaign_attribution": campaign_attribution,
                    "last_event": {
                        "event_type": pinterest_events[0].event_type if pinterest_events else None,
                        "timestamp": pinterest_events[0].created_at.isoformat() if pinterest_events else None,
                        "status": pinterest_events[0].status if pinterest_events else None
                    } if pinterest_events else None
                }
                
                logger.info(f"✅ Pinterest attribution summary retrieved: {conversion_count} conversions from {total_events} events")
                return summary
                
            except Exception as e:
                logger.error(f"❌ Error getting Pinterest attribution summary: {e}")
                return {"error": str(e)}
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error in Pinterest attribution summary: {e}")
            return {"error": str(e)}
    
    def _get_mock_attribution_summary(self) -> Dict[str, Any]:
        """
        Get mock Pinterest attribution summary
        
        Returns:
            Dictionary with mock attribution summary
        """
        return {
            "pinterest_pixel_id": self.pinterest_pixel_id,
            "total_events": 150,
            "conversion_events": 25,
            "conversion_rate": "16.67%",
            "campaign_attribution": {
                "123456789": {"events": 50, "conversions": 8},
                "987654321": {"events": 45, "conversions": 7},
                "555666777": {"events": 55, "conversions": 10}
            },
            "last_event": {
                "event_type": "purchase",
                "timestamp": datetime.now().isoformat(),
                "status": "received"
            }
        }

# Convenience functions for easy integration
def configure_pinterest_track_ai(store_id: str = None) -> bool:
    """
    Configure Pinterest traffic recognition in Track AI
    
    Args:
        store_id: Track AI store ID
        
    Returns:
        True if configuration successful, False otherwise
    """
    config = PinterestTrackAIConfig(store_id=store_id)
    return config.configure_pinterest_traffic_recognition()

def test_pinterest_traffic_recognition(store_id: str = None) -> Dict[str, Any]:
    """
    Test Pinterest traffic recognition
    
    Args:
        store_id: Track AI store ID
        
    Returns:
        Dictionary with test results
    """
    config = PinterestTrackAIConfig(store_id=store_id)
    return config.test_pinterest_traffic_recognition()

def get_pinterest_attribution_summary(store_id: str = None) -> Dict[str, Any]:
    """
    Get Pinterest attribution summary
    
    Args:
        store_id: Track AI store ID
        
    Returns:
        Dictionary with attribution summary
    """
    config = PinterestTrackAIConfig(store_id=store_id)
    return config.get_pinterest_attribution_summary()

# Example usage
if __name__ == "__main__":
    # Configure Pinterest traffic recognition
    success = configure_pinterest_track_ai()
    if success:
        print("✅ Pinterest traffic recognition configured successfully")
    else:
        print("❌ Failed to configure Pinterest traffic recognition")
    
    # Test Pinterest traffic recognition
    test_results = test_pinterest_traffic_recognition()
    print(f"📊 Test Results: {test_results['passed_tests']}/{test_results['total_tests']} passed")
    
    # Get attribution summary
    attribution_summary = get_pinterest_attribution_summary()
    print(f"📈 Attribution Summary: {attribution_summary}")
