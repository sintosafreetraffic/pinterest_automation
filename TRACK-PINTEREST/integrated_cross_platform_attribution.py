"""
Integrated Cross-Platform Attribution with Meta-Change Feed Enhancement
=====================================================================

This module integrates the cross-platform attribution system with the meta-change
product feed enhancement functionality, providing a unified solution for:

- Cross-platform attribution tracking across Pinterest, Meta, TikTok, etc.
- Product feed enhancement with Pinterest trends and audience insights
- Bulk metadata enrichment with AI-powered optimization
- Customer persona generation and targeting
- Enhanced Pinterest feed generation with strategic metadata
- Real-time attribution analysis and optimization

Features:
- Multi-touch attribution models (first-click, last-click, linear, time-decay, position-based, data-driven, ML)
- Customer journey mapping across platforms
- Pinterest discovery phase optimization
- Product feed enhancement with trending keywords
- Bulk metadata enrichment with LLM
- Enhanced Pinterest feed generation
- Cross-platform performance analytics
- Real-time attribution insights
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
import csv
import xml.etree.ElementTree as ET
import re

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cross_platform_attribution import (
    CrossPlatformAttribution, AttributionModel, Platform, Touchpoint, 
    CustomerJourney, AttributionResult
)
from pinterest_dashboard_integration import PinterestDashboardIntegration
from pinterest_conversion_tracking import PinterestConversionTracker

# Add meta-change directory to path
meta_change_path = '/Users/saschavanwell/Documents/meta-change'
sys.path.append(meta_change_path)

# Import meta-change modules
try:
    from bulk_metadata_enricher import LLMClient, ShopifyClient, SYSTEM_PROMPT
    from enhanced_pinterest_feed_generator import EnhancedPinterestFeedGenerator, TrendKeywordManager, TaxonomyManager
    from product_feed_enhancement import ProductFeedEnhancement
    META_CHANGE_AVAILABLE = True
    print("✅ Meta-change modules loaded successfully")
except ImportError as e:
    print(f"⚠️ Meta-change modules not available: {e}")
    META_CHANGE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Track AI Configuration
TRACK_AI_API_BASE = os.getenv("TRACK_AI_API_BASE", "https://track.ai.yourdomain.com/api")
TRACK_AI_API_KEY = os.getenv("TRACK_AI_API_KEY", "")

class IntegratedCrossPlatformAttribution:
    """
    Integrated Cross-Platform Attribution with Meta-Change Feed Enhancement
    
    This class provides a unified solution for:
    1. Cross-platform attribution tracking and analysis
    2. Product feed enhancement with Pinterest trends
    3. Bulk metadata enrichment with AI
    4. Enhanced Pinterest feed generation
    5. Customer persona generation and targeting
    6. Real-time attribution optimization
    """
    
    def __init__(self, track_ai_api_key: str = None):
        """
        Initialize Integrated Cross-Platform Attribution System
        
        Args:
            track_ai_api_key: Track AI API key for data access
        """
        self.track_ai_api_key = track_ai_api_key or TRACK_AI_API_KEY
        
        # Initialize core attribution system
        self.attribution = CrossPlatformAttribution(track_ai_api_key)
        self.pinterest_integration = PinterestDashboardIntegration()
        self.conversion_tracker = PinterestConversionTracker()
        
        # Initialize meta-change components
        self.meta_change_available = META_CHANGE_AVAILABLE
        if self.meta_change_available:
            self.feed_enhancement = ProductFeedEnhancement()
            self.feed_generator = EnhancedPinterestFeedGenerator()
            self.trend_manager = TrendKeywordManager()
            self.taxonomy_manager = TaxonomyManager()
            
            # Initialize LLM client for bulk metadata enrichment
            self.llm_client = self._initialize_llm_client()
            self.shopify_client = self._initialize_shopify_client()
        else:
            self.feed_enhancement = None
            self.feed_generator = None
            self.trend_manager = None
            self.taxonomy_manager = None
            self.llm_client = None
            self.shopify_client = None
        
        # Enhanced attribution models with meta-change integration
        self.enhanced_attribution_models = {
            AttributionModel.FIRST_CLICK: {"weight": 0.3, "pinterest_boost": 1.2},
            AttributionModel.LAST_CLICK: {"weight": 0.4, "pinterest_boost": 1.0},
            AttributionModel.LINEAR: {"weight": 0.2, "pinterest_boost": 1.1},
            AttributionModel.TIME_DECAY: {"weight": 0.3, "pinterest_boost": 1.3},
            AttributionModel.POSITION_BASED: {"weight": 0.25, "pinterest_boost": 1.4},
            AttributionModel.DATA_DRIVEN: {"weight": 0.35, "pinterest_boost": 1.5},
            AttributionModel.MACHINE_LEARNING: {"weight": 0.4, "pinterest_boost": 1.6}
        }
        
        # Pinterest discovery phase optimization
        self.pinterest_discovery_weights = {
            "impression": 0.1,
            "save": 0.3,
            "closeup": 0.2,
            "click": 0.4
        }
        
        logger.info("✅ Integrated Cross-Platform Attribution System initialized")
        logger.info(f"   Meta-change integration: {'Available' if self.meta_change_available else 'Not Available'}")
        logger.info(f"   Attribution models: {len(self.enhanced_attribution_models)}")
    
    def _initialize_llm_client(self) -> Optional[LLMClient]:
        """Initialize LLM client for bulk metadata enrichment"""
        try:
            llm_key = os.getenv("LLM_API_KEY")
            llm_base = os.getenv("LLM_BASE_URL")
            llm_model = os.getenv("LLM_MODEL", "deepseek-chat")
            
            if llm_key:
                return LLMClient(llm_key, llm_base, llm_model)
            else:
                logger.warning("⚠️ LLM API key not found - bulk metadata enrichment disabled")
                return None
        except Exception as e:
            logger.error(f"❌ Error initializing LLM client: {e}")
            return None
    
    def _initialize_shopify_client(self) -> Optional[ShopifyClient]:
        """Initialize Shopify client for bulk metadata enrichment"""
        try:
            store_domain = os.getenv("SHOPIFY_STORE_DOMAIN")
            api_version = os.getenv("SHOPIFY_ADMIN_API_VERSION", "2025-01")
            admin_token = os.getenv("SHOPIFY_STORE_API_KEY")
            
            if store_domain and admin_token:
                return ShopifyClient(store_domain, api_version, admin_token)
            else:
                logger.warning("⚠️ Shopify credentials not found - bulk metadata enrichment disabled")
                return None
        except Exception as e:
            logger.error(f"❌ Error initializing Shopify client: {e}")
            return None
    
    def calculate_enhanced_attribution(self, journey: CustomerJourney, 
                                     model: AttributionModel = AttributionModel.DATA_DRIVEN) -> AttributionResult:
        """
        Calculate enhanced attribution with meta-change integration
        
        Args:
            journey: Customer journey with touchpoints
            model: Attribution model to use
            
        Returns:
            Enhanced attribution result with meta-change insights
        """
        try:
            logger.info(f"🧮 Calculating enhanced attribution for journey {journey.user_id}")
            
            # Calculate base attribution
            base_result = self.attribution.calculate_attribution(journey, model)
            
            if not base_result:
                return self.attribution._create_empty_attribution_result(journey, model)
            
            # Enhance with meta-change insights if available
            if self.meta_change_available:
                enhanced_result = self._enhance_attribution_with_meta_change(base_result, journey)
                return enhanced_result
            else:
                return base_result
                
        except Exception as e:
            logger.error(f"❌ Error calculating enhanced attribution: {e}")
            return self.attribution._create_empty_attribution_result(journey, model)
    
    def _enhance_attribution_with_meta_change(self, base_result: AttributionResult, 
                                            journey: CustomerJourney) -> AttributionResult:
        """Enhance attribution result with meta-change insights"""
        try:
            # Get Pinterest trends and audience insights
            trending_keywords = self.feed_enhancement.get_trending_keywords(region="DE", trend_type="growing")
            audience_insights = self.feed_enhancement.get_audience_insights()
            
            # Generate customer persona
            customer_persona = None
            if audience_insights:
                customer_persona = self.feed_enhancement.generate_customer_persona(audience_insights)
            
            # Filter keywords by audience
            filtered_keywords = []
            if trending_keywords and customer_persona:
                filtered_keywords = self.feed_enhancement.filter_keywords_by_audience(
                    trending_keywords, customer_persona
                )
            
            # Enhance platform scores with Pinterest discovery phase optimization
            enhanced_platform_scores = self._optimize_pinterest_discovery_phase(
                base_result.platform_scores, filtered_keywords, customer_persona
            )
            
            # Enhance campaign scores with trending keywords
            enhanced_campaign_scores = self._enhance_campaign_scores_with_trends(
                base_result.campaign_scores, filtered_keywords
            )
            
            # Create enhanced attribution result
            enhanced_result = AttributionResult(
                journey=base_result.journey,
                model=base_result.model,
                platform_scores=enhanced_platform_scores,
                campaign_scores=enhanced_campaign_scores,
                ad_scores=base_result.ad_scores,
                total_attribution=sum(enhanced_platform_scores.values()),
                confidence_score=base_result.confidence_score,
                model_accuracy=base_result.model_accuracy
            )
            
            # Add meta-change insights
            enhanced_result.meta_change_insights = {
                "trending_keywords": filtered_keywords[:10],
                "customer_persona": customer_persona.get("persona_name", "Unknown") if customer_persona else "Unknown",
                "audience_interests": customer_persona.get("demographics", {}).get("interests", []) if customer_persona else [],
                "pinterest_discovery_optimization": self._calculate_pinterest_discovery_score(enhanced_platform_scores)
            }
            
            logger.info(f"✅ Enhanced attribution with meta-change insights")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Error enhancing attribution with meta-change: {e}")
            return base_result
    
    def _optimize_pinterest_discovery_phase(self, platform_scores: Dict[Platform, float], 
                                          trending_keywords: List[str], 
                                          customer_persona: Dict) -> Dict[Platform, float]:
        """Optimize Pinterest discovery phase attribution"""
        try:
            enhanced_scores = platform_scores.copy()
            
            # Boost Pinterest attribution for discovery phase
            if Platform.PINTEREST in enhanced_scores:
                pinterest_score = enhanced_scores[Platform.PINTEREST]
                
                # Apply Pinterest discovery phase boost
                discovery_boost = 1.0
                if trending_keywords:
                    discovery_boost += 0.2  # 20% boost for trending keywords
                
                if customer_persona and customer_persona.get("demographics", {}).get("interests"):
                    discovery_boost += 0.1  # 10% boost for persona match
                
                enhanced_scores[Platform.PINTEREST] = pinterest_score * discovery_boost
                logger.info(f"🎯 Pinterest discovery phase optimized: {pinterest_score:.2f} → {enhanced_scores[Platform.PINTEREST]:.2f}")
            
            return enhanced_scores
            
        except Exception as e:
            logger.error(f"❌ Error optimizing Pinterest discovery phase: {e}")
            return platform_scores
    
    def _enhance_campaign_scores_with_trends(self, campaign_scores: Dict[str, float], 
                                           trending_keywords: List[str]) -> Dict[str, float]:
        """Enhance campaign scores with trending keywords"""
        try:
            enhanced_scores = campaign_scores.copy()
            
            # Boost campaigns with trending keywords
            for campaign_id, score in enhanced_scores.items():
                # Simple boost based on trending keywords availability
                if trending_keywords:
                    trend_boost = 1.0 + (len(trending_keywords) * 0.01)  # 1% per keyword
                    enhanced_scores[campaign_id] = score * trend_boost
            
            return enhanced_scores
            
        except Exception as e:
            logger.error(f"❌ Error enhancing campaign scores: {e}")
            return campaign_scores
    
    def _calculate_pinterest_discovery_score(self, platform_scores: Dict[Platform, float]) -> float:
        """Calculate Pinterest discovery phase score"""
        try:
            pinterest_score = platform_scores.get(Platform.PINTEREST, 0.0)
            total_score = sum(platform_scores.values())
            
            if total_score > 0:
                discovery_ratio = pinterest_score / total_score
                return min(discovery_ratio * 2, 1.0)  # Cap at 1.0
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"❌ Error calculating Pinterest discovery score: {e}")
            return 0.0
    
    def enhance_product_feed_with_attribution(self, products: List[Dict], 
                                            attribution_insights: Dict) -> List[Dict]:
        """
        Enhance product feed with attribution insights
        
        Args:
            products: List of product data
            attribution_insights: Attribution insights from cross-platform analysis
            
        Returns:
            List of enhanced products with attribution insights
        """
        try:
            if not self.meta_change_available:
                logger.warning("⚠️ Meta-change integration not available")
                return products
            
            logger.info(f"🎨 Enhancing {len(products)} products with attribution insights")
            
            enhanced_products = []
            for product in products:
                try:
                    # Get trending keywords for this product
                    product_type = product.get("product_type", "")
                    trending_keywords = self.feed_enhancement.get_trending_keywords(
                        region="DE", trend_type="growing", interests=[product_type]
                    )
                    
                    # Get audience insights
                    audience_insights = self.feed_enhancement.get_audience_insights()
                    
                    # Generate customer persona
                    customer_persona = None
                    if audience_insights:
                        customer_persona = self.feed_enhancement.generate_customer_persona(audience_insights)
                    
                    # Filter keywords by audience
                    filtered_keywords = []
                    if trending_keywords and customer_persona:
                        filtered_keywords = self.feed_enhancement.filter_keywords_by_audience(
                            trending_keywords, customer_persona
                        )
                    
                    # Enhance product metadata
                    enhanced_metadata = self.feed_enhancement.enhance_product_metadata(
                        product, filtered_keywords, customer_persona
                    )
                    
                    # Add attribution insights
                    enhanced_metadata['attribution_insights'] = {
                        'pinterest_discovery_score': attribution_insights.get('pinterest_discovery_score', 0.0),
                        'cross_platform_performance': attribution_insights.get('cross_platform_performance', {}),
                        'optimization_recommendations': self._generate_optimization_recommendations(
                            product, filtered_keywords, customer_persona
                        )
                    }
                    
                    enhanced_products.append(enhanced_metadata)
                    
                except Exception as e:
                    logger.error(f"❌ Error enhancing product {product.get('id', 'Unknown')}: {e}")
                    enhanced_products.append(product)  # Return original if enhancement fails
            
            logger.info(f"✅ Enhanced {len(enhanced_products)} products with attribution insights")
            return enhanced_products
            
        except Exception as e:
            logger.error(f"❌ Error enhancing product feed: {e}")
            return products
    
    def _generate_optimization_recommendations(self, product: Dict, 
                                            trending_keywords: List[str], 
                                            customer_persona: Dict) -> List[str]:
        """Generate optimization recommendations for a product"""
        recommendations = []
        
        # Pinterest optimization
        if trending_keywords:
            recommendations.append(f"Use trending keywords: {', '.join(trending_keywords[:3])}")
        
        # Audience targeting
        if customer_persona:
            persona_name = customer_persona.get("persona_name", "Unknown")
            recommendations.append(f"Target audience: {persona_name}")
        
        # Product-specific recommendations
        product_type = product.get("product_type", "")
        if "dress" in product_type.lower():
            recommendations.append("Focus on occasion-based marketing (wedding, party, casual)")
        elif "shoes" in product_type.lower():
            recommendations.append("Emphasize comfort and style for different occasions")
        
        return recommendations
    
    def generate_enhanced_pinterest_feed_with_attribution(self, products: List[Dict], 
                                                        attribution_insights: Dict) -> Dict:
        """
        Generate enhanced Pinterest feed with attribution insights
        
        Args:
            products: List of product data
            attribution_insights: Attribution insights from cross-platform analysis
            
        Returns:
            Dictionary with enhanced feed information
        """
        try:
            if not self.meta_change_available:
                logger.warning("⚠️ Meta-change integration not available")
                return {"success": False, "error": "Meta-change integration not available"}
            
            logger.info(f"🎯 Generating enhanced Pinterest feed with attribution insights")
            
            # Enhance products with attribution insights
            enhanced_products = self.enhance_product_feed_with_attribution(products, attribution_insights)
            
            # Generate enhanced feed
            feed_result = self.feed_generator.generate_enhanced_csv_feed(enhanced_products)
            
            # Generate campaign-specific feeds
            campaign_feeds = self.feed_generator.generate_campaign_specific_feeds(enhanced_products)
            
            # Add attribution insights to feed metadata
            feed_metadata = {
                "attribution_insights": attribution_insights,
                "enhancement_timestamp": datetime.now().isoformat(),
                "total_products": len(enhanced_products),
                "trending_keywords_used": len(attribution_insights.get('trending_keywords', [])),
                "customer_persona": attribution_insights.get('customer_persona', 'Unknown')
            }
            
            result = {
                "success": True,
                "main_feed": feed_result,
                "campaign_feeds": campaign_feeds,
                "feed_metadata": feed_metadata,
                "enhanced_products_count": len(enhanced_products)
            }
            
            logger.info(f"✅ Enhanced Pinterest feed generated successfully")
            logger.info(f"   Main feed: {feed_result}")
            logger.info(f"   Campaign feeds: {len(campaign_feeds)}")
            logger.info(f"   Enhanced products: {len(enhanced_products)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating enhanced Pinterest feed: {e}")
            return {"success": False, "error": str(e)}
    
    def bulk_enhance_metadata_with_attribution(self, products: List[Dict], 
                                             attribution_insights: Dict,
                                             apply_changes: bool = False) -> Dict:
        """
        Bulk enhance product metadata with attribution insights
        
        Args:
            products: List of product data
            attribution_insights: Attribution insights from cross-platform analysis
            apply_changes: Whether to apply changes to Shopify
            
        Returns:
            Dictionary with enhancement results
        """
        try:
            if not self.meta_change_available or not self.llm_client or not self.shopify_client:
                logger.warning("⚠️ Bulk metadata enhancement not available")
                return {"success": False, "error": "Bulk metadata enhancement not available"}
            
            logger.info(f"🔧 Bulk enhancing metadata for {len(products)} products")
            
            enhanced_products = []
            changes_applied = 0
            
            for product in products:
                try:
                    # Get trending keywords and audience insights
                    product_type = product.get("product_type", "")
                    trending_keywords = self.feed_enhancement.get_trending_keywords(
                        region="DE", trend_type="growing", interests=[product_type]
                    )
                    
                    audience_insights = self.feed_enhancement.get_audience_insights()
                    customer_persona = None
                    if audience_insights:
                        customer_persona = self.feed_enhancement.generate_customer_persona(audience_insights)
                    
                    # Filter keywords by audience
                    filtered_keywords = []
                    if trending_keywords and customer_persona:
                        filtered_keywords = self.feed_enhancement.filter_keywords_by_audience(
                            trending_keywords, customer_persona
                        )
                    
                    # Enhance product metadata with LLM
                    enhanced_metadata = self._enhance_single_product_metadata(
                        product, filtered_keywords, customer_persona, apply_changes
                    )
                    
                    if enhanced_metadata:
                        enhanced_products.append(enhanced_metadata)
                        if apply_changes and enhanced_metadata.get("changes_applied"):
                            changes_applied += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error enhancing product {product.get('id', 'Unknown')}: {e}")
                    continue
            
            result = {
                "success": True,
                "enhanced_products": len(enhanced_products),
                "changes_applied": changes_applied,
                "attribution_insights": attribution_insights,
                "enhancement_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Bulk metadata enhancement completed")
            logger.info(f"   Enhanced products: {len(enhanced_products)}")
            logger.info(f"   Changes applied: {changes_applied}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in bulk metadata enhancement: {e}")
            return {"success": False, "error": str(e)}
    
    def _enhance_single_product_metadata(self, product: Dict, trending_keywords: List[str], 
                                       customer_persona: Dict, apply_changes: bool = False) -> Dict:
        """Enhance metadata for a single product using LLM"""
        try:
            # Create enhanced prompt with attribution insights
            enhanced_prompt = self._create_enhanced_llm_prompt(product, trending_keywords, customer_persona)
            
            # Call LLM for enhancement
            llm_response = self.llm_client.chat_json(SYSTEM_PROMPT, enhanced_prompt)
            
            # Validate and apply changes
            if llm_response and apply_changes:
                # Apply changes to Shopify
                self._apply_product_changes(product, llm_response)
                llm_response["changes_applied"] = True
            else:
                llm_response["changes_applied"] = False
            
            return llm_response
            
        except Exception as e:
            logger.error(f"❌ Error enhancing product metadata: {e}")
            return None
    
    def _create_enhanced_llm_prompt(self, product: Dict, trending_keywords: List[str], 
                                  customer_persona: Dict) -> str:
        """Create enhanced LLM prompt with attribution insights"""
        try:
            # Base product information
            product_info = {
                "title": product.get("title", ""),
                "body_html": product.get("body_html", ""),
                "tags": product.get("tags", ""),
                "product_type": product.get("product_type", ""),
                "handle": product.get("handle", "")
            }
            
            # Add attribution insights
            attribution_context = {
                "trending_keywords": trending_keywords[:10],
                "customer_persona": customer_persona.get("persona_name", "Unknown") if customer_persona else "Unknown",
                "audience_interests": customer_persona.get("demographics", {}).get("interests", []) if customer_persona else [],
                "optimization_focus": "Pinterest discovery phase optimization"
            }
            
            # Create enhanced prompt
            enhanced_prompt = {
                "product": product_info,
                "attribution_context": attribution_context,
                "optimization_goals": [
                    "Maximize Pinterest discoverability",
                    "Optimize for trending keywords",
                    "Target customer persona preferences",
                    "Enhance cross-platform attribution"
                ]
            }
            
            return json.dumps(enhanced_prompt, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Error creating enhanced LLM prompt: {e}")
            return json.dumps({"product": product}, ensure_ascii=False, indent=2)
    
    def _apply_product_changes(self, product: Dict, llm_response: Dict) -> bool:
        """Apply product changes to Shopify"""
        try:
            if not self.shopify_client:
                return False
            
            product_id = product.get("id")
            if not product_id:
                return False
            
            # Extract changes from LLM response
            title = llm_response.get("title")
            body_html = llm_response.get("body_html")
            tags = llm_response.get("tags")
            product_type = llm_response.get("product_type")
            handle = llm_response.get("handle")
            
            # Apply changes
            self.shopify_client.update_product(
                product_id, title, body_html, tags, product_type, handle
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error applying product changes: {e}")
            return False
    
    def analyze_cross_platform_performance_with_meta_change(self, 
                                                          start_date: datetime, 
                                                          end_date: datetime) -> Dict:
        """
        Analyze cross-platform performance with meta-change integration
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Comprehensive cross-platform performance analysis
        """
        try:
            logger.info(f"📊 Analyzing cross-platform performance with meta-change integration")
            
            # Get base cross-platform analysis
            base_analysis = self.attribution.analyze_cross_platform_performance(start_date, end_date)
            
            # Enhance with meta-change insights
            if self.meta_change_available:
                meta_change_insights = self._get_meta_change_insights()
                
                # Combine analyses
                enhanced_analysis = {
                    **base_analysis,
                    "meta_change_insights": meta_change_insights,
                    "pinterest_optimization": self._analyze_pinterest_optimization(),
                    "trending_keywords_impact": self._analyze_trending_keywords_impact(),
                    "customer_persona_effectiveness": self._analyze_customer_persona_effectiveness()
                }
                
                logger.info(f"✅ Enhanced cross-platform analysis completed")
                return enhanced_analysis
            else:
                logger.warning("⚠️ Meta-change integration not available - returning base analysis")
                return base_analysis
                
        except Exception as e:
            logger.error(f"❌ Error analyzing cross-platform performance: {e}")
            return {}
    
    def _get_meta_change_insights(self) -> Dict:
        """Get meta-change insights for analysis"""
        try:
            insights = {}
            
            # Get trending keywords
            trending_keywords = self.feed_enhancement.get_trending_keywords(region="DE", trend_type="growing")
            if trending_keywords:
                insights["trending_keywords"] = trending_keywords.get("keywords", [])[:10]
            
            # Get audience insights
            audience_insights = self.feed_enhancement.get_audience_insights()
            if audience_insights:
                insights["audience_insights"] = {
                    "type": audience_insights.get("type", "Unknown"),
                    "size": audience_insights.get("size", 0),
                    "categories": audience_insights.get("categories", [])[:5]
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error getting meta-change insights: {e}")
            return {}
    
    def _analyze_pinterest_optimization(self) -> Dict:
        """Analyze Pinterest optimization effectiveness"""
        try:
            # Get Pinterest dashboard data
            pinterest_data = self.pinterest_integration.get_pinterest_dashboard_data()
            
            if pinterest_data:
                metrics = pinterest_data.get("metrics", [])
                total_impressions = sum(m.get("impressions", 0) for m in metrics)
                total_clicks = sum(m.get("clicks", 0) for m in metrics)
                total_saves = sum(m.get("saves", 0) for m in metrics)
                
                return {
                    "total_impressions": total_impressions,
                    "total_clicks": total_clicks,
                    "total_saves": total_saves,
                    "ctr": total_clicks / total_impressions if total_impressions > 0 else 0,
                    "save_rate": total_saves / total_impressions if total_impressions > 0 else 0,
                    "optimization_score": self._calculate_pinterest_optimization_score(metrics)
                }
            else:
                return {"optimization_score": 0.0}
                
        except Exception as e:
            logger.error(f"❌ Error analyzing Pinterest optimization: {e}")
            return {"optimization_score": 0.0}
    
    def _calculate_pinterest_optimization_score(self, metrics: List[Dict]) -> float:
        """Calculate Pinterest optimization score"""
        try:
            if not metrics:
                return 0.0
            
            total_impressions = sum(m.get("impressions", 0) for m in metrics)
            total_clicks = sum(m.get("clicks", 0) for m in metrics)
            total_saves = sum(m.get("saves", 0) for m in metrics)
            
            if total_impressions == 0:
                return 0.0
            
            ctr = total_clicks / total_impressions
            save_rate = total_saves / total_impressions
            
            # Calculate optimization score (CTR * 0.6 + Save Rate * 0.4)
            optimization_score = (ctr * 0.6) + (save_rate * 0.4)
            
            return min(optimization_score * 100, 100.0)  # Cap at 100
            
        except Exception as e:
            logger.error(f"❌ Error calculating Pinterest optimization score: {e}")
            return 0.0
    
    def _analyze_trending_keywords_impact(self) -> Dict:
        """Analyze the impact of trending keywords"""
        try:
            trending_keywords = self.feed_enhancement.get_trending_keywords(region="DE", trend_type="growing")
            
            if trending_keywords and trending_keywords.get("keywords"):
                keywords = trending_keywords["keywords"]
                return {
                    "total_keywords": len(keywords),
                    "top_keywords": [k.get("keyword", "") for k in keywords[:5]],
                    "impact_score": len(keywords) / 10.0  # Simple impact score
                }
            else:
                return {"total_keywords": 0, "top_keywords": [], "impact_score": 0.0}
                
        except Exception as e:
            logger.error(f"❌ Error analyzing trending keywords impact: {e}")
            return {"total_keywords": 0, "top_keywords": [], "impact_score": 0.0}
    
    def _analyze_customer_persona_effectiveness(self) -> Dict:
        """Analyze customer persona effectiveness"""
        try:
            audience_insights = self.feed_enhancement.get_audience_insights()
            
            if audience_insights:
                customer_persona = self.feed_enhancement.generate_customer_persona(audience_insights)
                
                if customer_persona:
                    return {
                        "persona_name": customer_persona.get("persona_name", "Unknown"),
                        "demographics": customer_persona.get("demographics", {}),
                        "behavior": customer_persona.get("behavior", {}),
                        "effectiveness_score": self._calculate_persona_effectiveness_score(customer_persona)
                    }
                else:
                    return {"effectiveness_score": 0.0}
            else:
                return {"effectiveness_score": 0.0}
                
        except Exception as e:
            logger.error(f"❌ Error analyzing customer persona effectiveness: {e}")
            return {"effectiveness_score": 0.0}
    
    def _calculate_persona_effectiveness_score(self, customer_persona: Dict) -> float:
        """Calculate customer persona effectiveness score"""
        try:
            base_score = 0.5
            
            # Add points for demographics
            demographics = customer_persona.get("demographics", {})
            if demographics.get("ages"):
                base_score += 0.1
            if demographics.get("interests"):
                base_score += 0.1
            
            # Add points for behavior
            behavior = customer_persona.get("behavior", {})
            if behavior.get("top_categories"):
                base_score += 0.1
            if behavior.get("engagement_patterns"):
                base_score += 0.1
            
            return min(base_score, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Error calculating persona effectiveness score: {e}")
            return 0.0
    
    def get_integrated_attribution_summary(self) -> Dict:
        """Get integrated attribution summary with meta-change insights"""
        try:
            summary = {
                "attribution_system": {
                    "models_available": len(self.enhanced_attribution_models),
                    "pinterest_discovery_optimization": True,
                    "cross_platform_tracking": True
                },
                "meta_change_integration": {
                    "available": self.meta_change_available,
                    "feed_enhancement": self.feed_enhancement is not None,
                    "bulk_metadata_enrichment": self.llm_client is not None,
                    "enhanced_feed_generation": self.feed_generator is not None
                },
                "capabilities": [
                    "Cross-platform attribution tracking",
                    "Pinterest discovery phase optimization",
                    "Product feed enhancement with trends",
                    "Bulk metadata enrichment with AI",
                    "Enhanced Pinterest feed generation",
                    "Customer persona generation",
                    "Real-time attribution analysis"
                ],
                "integration_status": "Fully Integrated" if self.meta_change_available else "Partial Integration"
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error getting integrated attribution summary: {e}")
            return {"error": str(e)}

# Convenience functions for easy integration
def calculate_integrated_attribution(user_id: str, 
                                   model: AttributionModel = AttributionModel.DATA_DRIVEN) -> Optional[AttributionResult]:
    """
    Calculate integrated attribution for a user with meta-change enhancement
    
    Args:
        user_id: User ID to calculate attribution for
        model: Attribution model to use
        
    Returns:
        Enhanced attribution result or None if error
    """
    integrated_attribution = IntegratedCrossPlatformAttribution()
    journey = integrated_attribution.attribution.get_customer_journey_map(user_id)
    
    if journey:
        return integrated_attribution.calculate_enhanced_attribution(journey, model)
    else:
        return None

def enhance_product_feed_with_attribution(products: List[Dict], 
                                        attribution_insights: Dict) -> List[Dict]:
    """
    Enhance product feed with attribution insights
    
    Args:
        products: List of product data
        attribution_insights: Attribution insights from cross-platform analysis
        
    Returns:
        List of enhanced products
    """
    integrated_attribution = IntegratedCrossPlatformAttribution()
    return integrated_attribution.enhance_product_feed_with_attribution(products, attribution_insights)

def generate_enhanced_pinterest_feed_with_attribution(products: List[Dict], 
                                                    attribution_insights: Dict) -> Dict:
    """
    Generate enhanced Pinterest feed with attribution insights
    
    Args:
        products: List of product data
        attribution_insights: Attribution insights from cross-platform analysis
        
    Returns:
        Dictionary with enhanced feed information
    """
    integrated_attribution = IntegratedCrossPlatformAttribution()
    return integrated_attribution.generate_enhanced_pinterest_feed_with_attribution(products, attribution_insights)

def analyze_integrated_cross_platform_performance(start_date: datetime, 
                                                  end_date: datetime) -> Dict:
    """
    Analyze integrated cross-platform performance with meta-change insights
    
    Args:
        start_date: Analysis start date
        end_date: Analysis end date
        
    Returns:
        Comprehensive cross-platform performance analysis
    """
    integrated_attribution = IntegratedCrossPlatformAttribution()
    return integrated_attribution.analyze_cross_platform_performance_with_meta_change(start_date, end_date)

# Example usage
if __name__ == "__main__":
    # Initialize integrated attribution system
    integrated_attribution = IntegratedCrossPlatformAttribution()
    
    # Get integrated attribution summary
    summary = integrated_attribution.get_integrated_attribution_summary()
    print(f"📊 Integrated Attribution Summary: {summary}")
    
    # Test enhanced attribution calculation
    journey = integrated_attribution.attribution.get_customer_journey_map("user_123")
    if journey:
        enhanced_result = integrated_attribution.calculate_enhanced_attribution(journey)
        print(f"🎯 Enhanced Attribution: {enhanced_result.total_attribution:.2f}")
    
    # Test cross-platform performance analysis
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    performance = integrated_attribution.analyze_cross_platform_performance_with_meta_change(start_date, end_date)
    print(f"📈 Cross-platform Performance: {performance.get('total_impressions', 0):,} impressions")
