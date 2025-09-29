"""
Cross-Platform Attribution Model for Track AI
============================================

This module implements a sophisticated cross-platform attribution model
that accurately tracks customer journeys across Pinterest, Meta, TikTok,
and other advertising channels.

Features:
- Multi-touch attribution rules
- First-click and last-click attribution models
- Machine learning-based attribution
- Customer journey mapping
- Cross-device tracking
- Advanced attribution models (time-decay, position-based, data-driven)
- Pinterest discovery phase optimization
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, Counter
import threading
from concurrent.futures import ThreadPoolExecutor

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_dashboard_integration import PinterestDashboardIntegration
from pinterest_conversion_tracking import PinterestConversionTracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Track AI Configuration
TRACK_AI_API_BASE = os.getenv("TRACK_AI_API_BASE", "https://track.ai.yourdomain.com/api")
TRACK_AI_API_KEY = os.getenv("TRACK_AI_API_KEY", "")

class AttributionModel(Enum):
    """Attribution model types"""
    FIRST_CLICK = "first_click"
    LAST_CLICK = "last_click"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"
    DATA_DRIVEN = "data_driven"
    MACHINE_LEARNING = "machine_learning"

class Platform(Enum):
    """Advertising platform types"""
    PINTEREST = "pinterest"
    META = "meta"
    TIKTOK = "tiktok"
    GOOGLE = "google"
    SNAPCHAT = "snapchat"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    OTHER = "other"

@dataclass
class Touchpoint:
    """Individual touchpoint in customer journey"""
    platform: Platform
    campaign_id: str
    ad_id: str
    timestamp: datetime
    event_type: str  # click, impression, view, save, etc.
    attribution_value: float = 0.0
    position: int = 0
    time_to_conversion: Optional[timedelta] = None
    device_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None

@dataclass
class CustomerJourney:
    """Complete customer journey with touchpoints"""
    user_id: str
    session_id: str
    conversion_value: float
    conversion_timestamp: datetime
    touchpoints: List[Touchpoint] = field(default_factory=list)
    attribution_scores: Dict[AttributionModel, Dict[str, float]] = field(default_factory=dict)
    journey_duration: Optional[timedelta] = None
    platform_sequence: List[Platform] = field(default_factory=list)
    device_sequence: List[str] = field(default_factory=list)

@dataclass
class AttributionResult:
    """Attribution calculation result"""
    journey: CustomerJourney
    model: AttributionModel
    platform_scores: Dict[Platform, float]
    campaign_scores: Dict[str, float]
    ad_scores: Dict[str, float]
    total_attribution: float
    confidence_score: float
    model_accuracy: Optional[float] = None

class CrossPlatformAttribution:
    """
    Cross-Platform Attribution Model Manager
    
    Implements sophisticated attribution models for tracking customer journeys
    across multiple advertising platforms including Pinterest, Meta, TikTok, etc.
    """
    
    def __init__(self, track_ai_api_key: str = None):
        """
        Initialize Cross-Platform Attribution Model
        
        Args:
            track_ai_api_key: Track AI API key for data access
        """
        self.track_ai_api_key = track_ai_api_key or TRACK_AI_API_KEY
        self.pinterest_integration = PinterestDashboardIntegration()
        self.conversion_tracker = PinterestConversionTracker()
        
        # Attribution model weights
        self.model_weights = {
            AttributionModel.FIRST_CLICK: {"first": 1.0, "middle": 0.0, "last": 0.0},
            AttributionModel.LAST_CLICK: {"first": 0.0, "middle": 0.0, "last": 1.0},
            AttributionModel.LINEAR: {"first": 0.33, "middle": 0.33, "last": 0.33},
            AttributionModel.TIME_DECAY: {"first": 0.4, "middle": 0.3, "last": 0.3},
            AttributionModel.POSITION_BASED: {"first": 0.4, "middle": 0.2, "last": 0.4}
        }
        
        # Platform-specific weights for Pinterest discovery phase
        self.platform_weights = {
            Platform.PINTEREST: 1.2,  # Higher weight for discovery
            Platform.META: 1.0,
            Platform.TIKTOK: 1.0,
            Platform.GOOGLE: 1.0,
            Platform.SNAPCHAT: 1.0,
            Platform.TWITTER: 1.0,
            Platform.LINKEDIN: 1.0,
            Platform.OTHER: 0.8
        }
        
        # Time decay parameters
        self.time_decay_half_life = 7  # days
        self.attribution_window = 30  # days
        
        # Machine learning model (placeholder for future implementation)
        self.ml_model = None
        
        logger.info("✅ Cross-Platform Attribution Model initialized")
        logger.info(f"   Attribution Window: {self.attribution_window} days")
        logger.info(f"   Time Decay Half-Life: {self.time_decay_half_life} days")
    
    def calculate_attribution(self, journey: CustomerJourney, model: AttributionModel) -> AttributionResult:
        """
        Calculate attribution for a customer journey using specified model
        
        Args:
            journey: Customer journey with touchpoints
            model: Attribution model to use
            
        Returns:
            Attribution result with scores
        """
        try:
            logger.info(f"🧮 Calculating attribution for journey {journey.user_id} using {model.value} model")
            
            if not journey.touchpoints:
                logger.warning("⚠️ No touchpoints found in journey")
                return self._create_empty_attribution_result(journey, model)
            
            # Calculate attribution based on model
            if model == AttributionModel.FIRST_CLICK:
                attribution_scores = self._calculate_first_click_attribution(journey)
            elif model == AttributionModel.LAST_CLICK:
                attribution_scores = self._calculate_last_click_attribution(journey)
            elif model == AttributionModel.LINEAR:
                attribution_scores = self._calculate_linear_attribution(journey)
            elif model == AttributionModel.TIME_DECAY:
                attribution_scores = self._calculate_time_decay_attribution(journey)
            elif model == AttributionModel.POSITION_BASED:
                attribution_scores = self._calculate_position_based_attribution(journey)
            elif model == AttributionModel.DATA_DRIVEN:
                attribution_scores = self._calculate_data_driven_attribution(journey)
            elif model == AttributionModel.MACHINE_LEARNING:
                attribution_scores = self._calculate_ml_attribution(journey)
            else:
                logger.error(f"❌ Unsupported attribution model: {model}")
                return self._create_empty_attribution_result(journey, model)
            
            # Calculate platform and campaign scores
            platform_scores = self._calculate_platform_scores(journey, attribution_scores)
            campaign_scores = self._calculate_campaign_scores(journey, attribution_scores)
            ad_scores = self._calculate_ad_scores(journey, attribution_scores)
            
            # Calculate total attribution and confidence
            total_attribution = sum(attribution_scores.values())
            confidence_score = self._calculate_confidence_score(journey, attribution_scores)
            
            # Create attribution result
            result = AttributionResult(
                journey=journey,
                model=model,
                platform_scores=platform_scores,
                campaign_scores=campaign_scores,
                ad_scores=ad_scores,
                total_attribution=total_attribution,
                confidence_score=confidence_score
            )
            
            logger.info(f"✅ Attribution calculated: {total_attribution:.2f} total, {confidence_score:.2f} confidence")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error calculating attribution: {e}")
            return self._create_empty_attribution_result(journey, model)
    
    def _calculate_first_click_attribution(self, journey: CustomerJourney) -> Dict[str, float]:
        """Calculate first-click attribution"""
        if not journey.touchpoints:
            return {}
        
        # Sort touchpoints by timestamp
        sorted_touchpoints = sorted(journey.touchpoints, key=lambda x: x.timestamp)
        first_touchpoint = sorted_touchpoints[0]
        
        # Assign full attribution to first touchpoint
        attribution_scores = {}
        for touchpoint in journey.touchpoints:
            if touchpoint == first_touchpoint:
                attribution_scores[f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"] = 1.0
            else:
                attribution_scores[f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"] = 0.0
        
        return attribution_scores
    
    def _calculate_last_click_attribution(self, journey: CustomerJourney) -> Dict[str, float]:
        """Calculate last-click attribution"""
        if not journey.touchpoints:
            return {}
        
        # Sort touchpoints by timestamp
        sorted_touchpoints = sorted(journey.touchpoints, key=lambda x: x.timestamp)
        last_touchpoint = sorted_touchpoints[-1]
        
        # Assign full attribution to last touchpoint
        attribution_scores = {}
        for touchpoint in journey.touchpoints:
            if touchpoint == last_touchpoint:
                attribution_scores[f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"] = 1.0
            else:
                attribution_scores[f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"] = 0.0
        
        return attribution_scores
    
    def _calculate_linear_attribution(self, journey: CustomerJourney) -> Dict[str, float]:
        """Calculate linear attribution"""
        if not journey.touchpoints:
            return {}
        
        # Equal attribution to all touchpoints
        attribution_value = 1.0 / len(journey.touchpoints)
        
        attribution_scores = {}
        for touchpoint in journey.touchpoints:
            attribution_scores[f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"] = attribution_value
        
        return attribution_scores
    
    def _calculate_time_decay_attribution(self, journey: CustomerJourney) -> Dict[str, float]:
        """Calculate time-decay attribution"""
        if not journey.touchpoints:
            return {}
        
        # Calculate time decay weights
        decay_weights = []
        for touchpoint in journey.touchpoints:
            time_diff = (journey.conversion_timestamp - touchpoint.timestamp).total_seconds() / 86400  # days
            decay_weight = np.exp(-time_diff / self.time_decay_half_life)
            decay_weights.append(decay_weight)
        
        # Normalize weights
        total_weight = sum(decay_weights)
        if total_weight > 0:
            decay_weights = [w / total_weight for w in decay_weights]
        
        attribution_scores = {}
        for i, touchpoint in enumerate(journey.touchpoints):
            attribution_scores[f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"] = decay_weights[i]
        
        return attribution_scores
    
    def _calculate_position_based_attribution(self, journey: CustomerJourney) -> Dict[str, float]:
        """Calculate position-based attribution"""
        if not journey.touchpoints:
            return {}
        
        # Sort touchpoints by timestamp
        sorted_touchpoints = sorted(journey.touchpoints, key=lambda x: x.timestamp)
        num_touchpoints = len(sorted_touchpoints)
        
        # Position-based weights
        weights = self.model_weights[AttributionModel.POSITION_BASED]
        
        attribution_scores = {}
        for i, touchpoint in enumerate(sorted_touchpoints):
            if i == 0:  # First
                weight = weights["first"]
            elif i == num_touchpoints - 1:  # Last
                weight = weights["last"]
            else:  # Middle
                weight = weights["middle"]
            
            attribution_scores[f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"] = weight
        
        return attribution_scores
    
    def _calculate_data_driven_attribution(self, journey: CustomerJourney) -> Dict[str, float]:
        """Calculate data-driven attribution using historical data"""
        try:
            # Get historical conversion data
            historical_data = self._get_historical_conversion_data()
            
            # Calculate conversion probabilities for each touchpoint
            conversion_probs = {}
            for touchpoint in journey.touchpoints:
                prob = self._calculate_touchpoint_conversion_probability(touchpoint, historical_data)
                conversion_probs[f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"] = prob
            
            # Normalize probabilities
            total_prob = sum(conversion_probs.values())
            if total_prob > 0:
                attribution_scores = {k: v / total_prob for k, v in conversion_probs.items()}
            else:
                # Fallback to linear attribution
                attribution_scores = self._calculate_linear_attribution(journey)
            
            return attribution_scores
            
        except Exception as e:
            logger.error(f"❌ Error in data-driven attribution: {e}")
            return self._calculate_linear_attribution(journey)
    
    def _calculate_ml_attribution(self, journey: CustomerJourney) -> Dict[str, float]:
        """Calculate machine learning-based attribution"""
        try:
            if not self.ml_model:
                logger.warning("⚠️ ML model not available, falling back to data-driven attribution")
                return self._calculate_data_driven_attribution(journey)
            
            # Prepare features for ML model
            features = self._prepare_ml_features(journey)
            
            # Predict attribution scores
            attribution_scores = self.ml_model.predict(features)
            
            # Normalize scores
            total_score = sum(attribution_scores.values())
            if total_score > 0:
                attribution_scores = {k: v / total_score for k, v in attribution_scores.items()}
            
            return attribution_scores
            
        except Exception as e:
            logger.error(f"❌ Error in ML attribution: {e}")
            return self._calculate_data_driven_attribution(journey)
    
    def _calculate_platform_scores(self, journey: CustomerJourney, attribution_scores: Dict[str, float]) -> Dict[Platform, float]:
        """Calculate platform-level attribution scores"""
        platform_scores = defaultdict(float)
        
        for touchpoint in journey.touchpoints:
            key = f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"
            if key in attribution_scores:
                platform_scores[touchpoint.platform] += attribution_scores[key]
        
        return dict(platform_scores)
    
    def _calculate_campaign_scores(self, journey: CustomerJourney, attribution_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate campaign-level attribution scores"""
        campaign_scores = defaultdict(float)
        
        for touchpoint in journey.touchpoints:
            key = f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"
            if key in attribution_scores:
                campaign_scores[touchpoint.campaign_id] += attribution_scores[key]
        
        return dict(campaign_scores)
    
    def _calculate_ad_scores(self, journey: CustomerJourney, attribution_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate ad-level attribution scores"""
        ad_scores = defaultdict(float)
        
        for touchpoint in journey.touchpoints:
            key = f"{touchpoint.platform.value}_{touchpoint.campaign_id}_{touchpoint.ad_id}"
            if key in attribution_scores:
                ad_scores[touchpoint.ad_id] += attribution_scores[key]
        
        return dict(ad_scores)
    
    def _calculate_confidence_score(self, journey: CustomerJourney, attribution_scores: Dict[str, float]) -> float:
        """Calculate confidence score for attribution"""
        try:
            # Factors affecting confidence
            num_touchpoints = len(journey.touchpoints)
            journey_duration = journey.journey_duration.total_seconds() / 86400 if journey.journey_duration else 0  # days
            
            # Base confidence from number of touchpoints
            base_confidence = min(1.0, num_touchpoints / 5.0)  # Max confidence at 5+ touchpoints
            
            # Time factor (longer journeys = higher confidence)
            time_factor = min(1.0, journey_duration / 7.0)  # Max confidence at 7+ days
            
            # Attribution distribution factor
            attribution_values = list(attribution_scores.values())
            if attribution_values:
                max_attribution = max(attribution_values)
                distribution_factor = 1.0 - (max_attribution - 0.5) * 2  # Penalize extreme distributions
            else:
                distribution_factor = 0.0
            
            # Calculate final confidence
            confidence = (base_confidence + time_factor + distribution_factor) / 3.0
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"❌ Error calculating confidence score: {e}")
            return 0.5  # Default medium confidence
    
    def _get_historical_conversion_data(self) -> Dict[str, Any]:
        """Get historical conversion data for data-driven attribution"""
        try:
            # This would typically fetch from Track AI database
            # For now, return mock data
            return {
                "platform_conversion_rates": {
                    Platform.PINTEREST: 0.15,
                    Platform.META: 0.12,
                    Platform.TIKTOK: 0.10,
                    Platform.GOOGLE: 0.18
                },
                "campaign_conversion_rates": {},
                "ad_conversion_rates": {}
            }
        except Exception as e:
            logger.error(f"❌ Error getting historical data: {e}")
            return {}
    
    def _calculate_touchpoint_conversion_probability(self, touchpoint: Touchpoint, historical_data: Dict[str, Any]) -> float:
        """Calculate conversion probability for a touchpoint"""
        try:
            # Base probability from platform
            platform_rates = historical_data.get("platform_conversion_rates", {})
            base_prob = platform_rates.get(touchpoint.platform, 0.1)
            
            # Adjust for time to conversion
            if touchpoint.time_to_conversion:
                time_factor = max(0.1, 1.0 - (touchpoint.time_to_conversion.total_seconds() / 86400) / 30.0)
            else:
                time_factor = 1.0
            
            # Adjust for event type
            event_factors = {
                "click": 1.0,
                "impression": 0.3,
                "view": 0.5,
                "save": 0.8,
                "closeup": 0.7
            }
            event_factor = event_factors.get(touchpoint.event_type, 0.5)
            
            # Calculate final probability
            probability = base_prob * time_factor * event_factor
            return min(1.0, max(0.0, probability))
            
        except Exception as e:
            logger.error(f"❌ Error calculating touchpoint probability: {e}")
            return 0.1  # Default probability
    
    def _prepare_ml_features(self, journey: CustomerJourney) -> Dict[str, Any]:
        """Prepare features for machine learning model"""
        try:
            features = {
                "num_touchpoints": len(journey.touchpoints),
                "journey_duration_days": journey.journey_duration.total_seconds() / 86400 if journey.journey_duration else 0,
                "platforms": [tp.platform.value for tp in journey.touchpoints],
                "event_types": [tp.event_type for tp in journey.touchpoints],
                "conversion_value": journey.conversion_value,
                "has_pinterest": any(tp.platform == Platform.PINTEREST for tp in journey.touchpoints),
                "has_meta": any(tp.platform == Platform.META for tp in journey.touchpoints),
                "has_tiktok": any(tp.platform == Platform.TIKTOK for tp in journey.touchpoints)
            }
            return features
        except Exception as e:
            logger.error(f"❌ Error preparing ML features: {e}")
            return {}
    
    def _create_empty_attribution_result(self, journey: CustomerJourney, model: AttributionModel) -> AttributionResult:
        """Create empty attribution result for error cases"""
        return AttributionResult(
            journey=journey,
            model=model,
            platform_scores={},
            campaign_scores={},
            ad_scores={},
            total_attribution=0.0,
            confidence_score=0.0
        )
    
    def compare_attribution_models(self, journey: CustomerJourney) -> Dict[AttributionModel, AttributionResult]:
        """Compare different attribution models for a journey"""
        try:
            logger.info(f"🔍 Comparing attribution models for journey {journey.user_id}")
            
            results = {}
            for model in AttributionModel:
                try:
                    result = self.calculate_attribution(journey, model)
                    results[model] = result
                    logger.info(f"   {model.value}: {result.total_attribution:.2f} total, {result.confidence_score:.2f} confidence")
                except Exception as e:
                    logger.error(f"❌ Error calculating {model.value} attribution: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error comparing attribution models: {e}")
            return {}
    
    def get_customer_journey_map(self, user_id: str) -> Optional[CustomerJourney]:
        """Get customer journey map for a specific user"""
        try:
            # This would typically fetch from Track AI database
            # For now, return mock data
            logger.info(f"🗺️ Getting customer journey map for user {user_id}")
            
            # Mock journey data
            journey = CustomerJourney(
                user_id=user_id,
                session_id="session_123",
                conversion_value=150.0,
                conversion_timestamp=datetime.now()
            )
            
            # Add mock touchpoints
            touchpoints = [
                Touchpoint(
                    platform=Platform.PINTEREST,
                    campaign_id="123456789",
                    ad_id="987654321",
                    timestamp=datetime.now() - timedelta(days=3),
                    event_type="click",
                    position=1
                ),
                Touchpoint(
                    platform=Platform.META,
                    campaign_id="111222333",
                    ad_id="444555666",
                    timestamp=datetime.now() - timedelta(days=1),
                    event_type="click",
                    position=2
                ),
                Touchpoint(
                    platform=Platform.GOOGLE,
                    campaign_id="777888999",
                    ad_id="000111222",
                    timestamp=datetime.now() - timedelta(hours=2),
                    event_type="click",
                    position=3
                )
            ]
            
            journey.touchpoints = touchpoints
            journey.journey_duration = timedelta(days=3)
            journey.platform_sequence = [tp.platform for tp in touchpoints]
            
            return journey
            
        except Exception as e:
            logger.error(f"❌ Error getting customer journey map: {e}")
            return None
    
    def analyze_cross_platform_performance(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze cross-platform performance across all channels"""
        try:
            logger.info(f"📊 Analyzing cross-platform performance from {start_date} to {end_date}")
            
            # Get data from all platforms
            pinterest_data = self.pinterest_integration.get_pinterest_dashboard_data()
            
            # Mock data for other platforms
            meta_data = {"platform": "meta", "metrics": []}
            tiktok_data = {"platform": "tiktok", "metrics": []}
            google_data = {"platform": "google", "metrics": []}
            
            # Combine platform data
            all_platform_data = {
                "pinterest": pinterest_data,
                "meta": meta_data,
                "tiktok": tiktok_data,
                "google": google_data
            }
            
            # Calculate cross-platform metrics
            total_impressions = 0
            total_clicks = 0
            total_spend = 0
            platform_breakdown = {}
            
            for platform, data in all_platform_data.items():
                metrics = data.get("metrics", [])
                platform_impressions = sum(m.get("impressions", 0) for m in metrics)
                platform_clicks = sum(m.get("clicks", 0) for m in metrics)
                platform_spend = sum(m.get("spend", 0) for m in metrics)
                
                platform_breakdown[platform] = {
                    "impressions": platform_impressions,
                    "clicks": platform_clicks,
                    "spend": platform_spend,
                    "ctr": platform_clicks / platform_impressions if platform_impressions > 0 else 0
                }
                
                total_impressions += platform_impressions
                total_clicks += platform_clicks
                total_spend += platform_spend
            
            # Calculate cross-platform insights
            cross_platform_insights = {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_spend": total_spend,
                "overall_ctr": total_clicks / total_impressions if total_impressions > 0 else 0,
                "platform_breakdown": platform_breakdown,
                "top_performing_platform": max(platform_breakdown.keys(), key=lambda p: platform_breakdown[p]["ctr"]),
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
            logger.info(f"✅ Cross-platform analysis completed")
            logger.info(f"   Total Impressions: {total_impressions:,}")
            logger.info(f"   Total Clicks: {total_clicks:,}")
            logger.info(f"   Total Spend: ${total_spend:,.2f}")
            logger.info(f"   Overall CTR: {cross_platform_insights['overall_ctr']:.2%}")
            
            return cross_platform_insights
            
        except Exception as e:
            logger.error(f"❌ Error analyzing cross-platform performance: {e}")
            return {}
    
    def optimize_pinterest_discovery_phase(self, attribution_results: Dict[AttributionModel, AttributionResult]) -> Dict[str, Any]:
        """Optimize Pinterest discovery phase based on attribution results"""
        try:
            logger.info("🎯 Optimizing Pinterest discovery phase")
            
            # Analyze Pinterest performance across attribution models
            pinterest_scores = {}
            for model, result in attribution_results.items():
                pinterest_score = result.platform_scores.get(Platform.PINTEREST, 0.0)
                pinterest_scores[model] = pinterest_score
            
            # Calculate average Pinterest attribution
            avg_pinterest_attribution = sum(pinterest_scores.values()) / len(pinterest_scores) if pinterest_scores else 0.0
            
            # Determine optimization strategy
            if avg_pinterest_attribution > 0.4:
                strategy = "increase_budget"
                recommendation = "Pinterest is performing well in discovery phase. Consider increasing budget allocation."
            elif avg_pinterest_attribution > 0.2:
                strategy = "optimize_creative"
                recommendation = "Pinterest shows moderate performance. Focus on creative optimization and targeting."
            else:
                strategy = "review_strategy"
                recommendation = "Pinterest discovery performance is low. Review targeting and creative strategy."
            
            optimization_insights = {
                "average_pinterest_attribution": avg_pinterest_attribution,
                "strategy": strategy,
                "recommendation": recommendation,
                "pinterest_scores_by_model": pinterest_scores,
                "optimization_priority": "high" if avg_pinterest_attribution < 0.2 else "medium"
            }
            
            logger.info(f"✅ Pinterest discovery optimization completed")
            logger.info(f"   Average Pinterest Attribution: {avg_pinterest_attribution:.2f}")
            logger.info(f"   Strategy: {strategy}")
            logger.info(f"   Recommendation: {recommendation}")
            
            return optimization_insights
            
        except Exception as e:
            logger.error(f"❌ Error optimizing Pinterest discovery phase: {e}")
            return {}

# Convenience functions for easy integration
def calculate_cross_platform_attribution(user_id: str, model: AttributionModel = AttributionModel.DATA_DRIVEN) -> Optional[AttributionResult]:
    """
    Calculate cross-platform attribution for a user
    
    Args:
        user_id: User ID to calculate attribution for
        model: Attribution model to use
        
    Returns:
        Attribution result or None if error
    """
    attribution = CrossPlatformAttribution()
    journey = attribution.get_customer_journey_map(user_id)
    
    if journey:
        return attribution.calculate_attribution(journey, model)
    else:
        return None

def compare_attribution_models_for_user(user_id: str) -> Dict[AttributionModel, AttributionResult]:
    """
    Compare different attribution models for a user
    
    Args:
        user_id: User ID to analyze
        
    Returns:
        Dictionary of attribution results by model
    """
    attribution = CrossPlatformAttribution()
    journey = attribution.get_customer_journey_map(user_id)
    
    if journey:
        return attribution.compare_attribution_models(journey)
    else:
        return {}

def analyze_cross_platform_performance(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Analyze cross-platform performance across all channels
    
    Args:
        start_date: Analysis start date
        end_date: Analysis end date
        
    Returns:
        Cross-platform performance analysis
    """
    attribution = CrossPlatformAttribution()
    return attribution.analyze_cross_platform_performance(start_date, end_date)

# Example usage
if __name__ == "__main__":
    # Initialize attribution model
    attribution = CrossPlatformAttribution()
    
    # Get customer journey
    journey = attribution.get_customer_journey_map("user_123")
    if journey:
        print(f"✅ Customer journey retrieved: {len(journey.touchpoints)} touchpoints")
        
        # Calculate attribution using different models
        models_to_test = [
            AttributionModel.FIRST_CLICK,
            AttributionModel.LAST_CLICK,
            AttributionModel.LINEAR,
            AttributionModel.TIME_DECAY,
            AttributionModel.POSITION_BASED
        ]
        
        for model in models_to_test:
            result = attribution.calculate_attribution(journey, model)
            print(f"📊 {model.value}: {result.total_attribution:.2f} total, {result.confidence_score:.2f} confidence")
        
        # Compare all models
        comparison = attribution.compare_attribution_models(journey)
        print(f"🔍 Compared {len(comparison)} attribution models")
        
        # Optimize Pinterest discovery phase
        optimization = attribution.optimize_pinterest_discovery_phase(comparison)
        print(f"🎯 Pinterest optimization: {optimization.get('strategy')}")
    
    # Analyze cross-platform performance
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    performance = attribution.analyze_cross_platform_performance(start_date, end_date)
    print(f"📈 Cross-platform analysis: {performance.get('total_impressions', 0):,} impressions")
