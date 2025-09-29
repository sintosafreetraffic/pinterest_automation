"""
Pinterest-Specific Analytics Widgets for Track AI Dashboard
=========================================================

This module creates specialized analytics widgets for Pinterest performance tracking
that integrate with the Track AI dashboard system.

Widgets implemented:
1. Pinterest Campaign ROI Comparison
2. Pin Performance Analysis
3. Pinterest Audience Demographics
4. Pinterest-to-Purchase Funnel Visualization
5. Pinterest Discovery Phase Metrics
6. Pinterest Trend Analysis
7. Cross-Platform Pinterest Comparison
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import requests
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pinterest_dashboard_integration import PinterestDashboardIntegration
from integrated_cross_platform_attribution import IntegratedCrossPlatformAttribution

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PinterestWidgetData:
    """Data structure for Pinterest widget data"""
    widget_id: str
    widget_type: str
    title: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

class PinterestAnalyticsWidgets:
    """
    Pinterest-Specific Analytics Widgets for Track AI Dashboard
    
    This class provides specialized widgets for Pinterest performance analysis:
    - Campaign ROI comparison
    - Pin performance analysis
    - Audience demographics
    - Purchase funnel visualization
    - Discovery phase metrics
    - Trend analysis
    - Cross-platform comparison
    """
    
    def __init__(self, track_ai_api_key: str = None):
        """
        Initialize Pinterest Analytics Widgets
        
        Args:
            track_ai_api_key: Track AI API key for data access
        """
        self.track_ai_api_key = track_ai_api_key
        self.pinterest_integration = PinterestDashboardIntegration()
        self.attribution_system = IntegratedCrossPlatformAttribution(track_ai_api_key)
        
        # Widget configuration
        self.widget_configs = {
            "campaign_roi": {
                "title": "Pinterest Campaign ROI Comparison",
                "type": "bar_chart",
                "metrics": ["roas", "cpa", "revenue", "spend"]
            },
            "pin_performance": {
                "title": "Pin Performance Analysis",
                "type": "scatter_plot",
                "metrics": ["impressions", "clicks", "saves", "ctr", "save_rate"]
            },
            "audience_demographics": {
                "title": "Pinterest Audience Demographics",
                "type": "pie_chart",
                "metrics": ["age_groups", "genders", "interests", "locations"]
            },
            "purchase_funnel": {
                "title": "Pinterest-to-Purchase Funnel",
                "type": "funnel_chart",
                "metrics": ["impressions", "clicks", "saves", "website_clicks", "purchases"]
            },
            "discovery_phase": {
                "title": "Pinterest Discovery Phase Metrics",
                "type": "line_chart",
                "metrics": ["impressions", "saves", "closeups", "clicks"]
            },
            "trend_analysis": {
                "title": "Pinterest Trend Analysis",
                "type": "area_chart",
                "metrics": ["trending_keywords", "seasonal_performance", "growth_rates"]
            },
            "cross_platform": {
                "title": "Cross-Platform Pinterest Comparison",
                "type": "multi_bar_chart",
                "metrics": ["attribution_scores", "performance_metrics", "roi_comparison"]
            }
        }
        
        logger.info("✅ Pinterest Analytics Widgets initialized")
        logger.info(f"   Available widgets: {len(self.widget_configs)}")
    
    def get_campaign_roi_widget(self, start_date: datetime, end_date: datetime, 
                               campaign_ids: List[str] = None) -> PinterestWidgetData:
        """
        Create Pinterest Campaign ROI Comparison Widget
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            campaign_ids: Optional list of campaign IDs to filter
            
        Returns:
            PinterestWidgetData with campaign ROI comparison
        """
        try:
            logger.info("📊 Generating Pinterest Campaign ROI Widget")
            
            # Get Pinterest campaign data
            pinterest_data = self.pinterest_integration.get_pinterest_dashboard_data()
            
            if not pinterest_data or pinterest_data.get("error"):
                logger.warning("⚠️ No Pinterest data available for ROI analysis")
                return self._create_empty_widget("campaign_roi", "No Pinterest data available")
            
            # Extract campaign data
            campaigns = pinterest_data.get("campaigns", [])
            if not campaigns:
                return self._create_empty_widget("campaign_roi", "No campaigns found")
            
            # Filter campaigns if specified
            if campaign_ids:
                campaigns = [c for c in campaigns if c.get("id") in campaign_ids]
            
            # Calculate ROI metrics for each campaign
            roi_data = []
            for campaign in campaigns:
                campaign_id = campaign.get("id", "")
                campaign_name = campaign.get("name", "Unknown")
                
                # Get campaign performance metrics
                metrics = self._get_campaign_metrics(campaign_id, start_date, end_date)
                
                if metrics:
                    roi_data.append({
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "roas": metrics.get("roas", 0.0),
                        "cpa": metrics.get("cpa", 0.0),
                        "revenue": metrics.get("revenue", 0.0),
                        "spend": metrics.get("spend", 0.0),
                        "impressions": metrics.get("impressions", 0),
                        "clicks": metrics.get("clicks", 0),
                        "purchases": metrics.get("purchases", 0)
                    })
            
            # Sort by ROAS descending
            roi_data.sort(key=lambda x: x["roas"], reverse=True)
            
            # Create widget data
            widget_data = {
                "campaigns": roi_data,
                "summary": {
                    "total_campaigns": len(roi_data),
                    "avg_roas": np.mean([c["roas"] for c in roi_data]) if roi_data else 0.0,
                    "total_revenue": sum(c["revenue"] for c in roi_data),
                    "total_spend": sum(c["spend"] for c in roi_data),
                    "best_campaign": roi_data[0] if roi_data else None
                },
                "chart_data": {
                    "labels": [c["campaign_name"][:20] for c in roi_data],
                    "datasets": [
                        {
                            "label": "ROAS",
                            "data": [c["roas"] for c in roi_data],
                            "backgroundColor": "rgba(230, 0, 35, 0.8)"
                        },
                        {
                            "label": "Revenue (€)",
                            "data": [c["revenue"] for c in roi_data],
                            "backgroundColor": "rgba(0, 123, 255, 0.8)"
                        }
                    ]
                }
            }
            
            logger.info(f"✅ Campaign ROI widget generated: {len(roi_data)} campaigns")
            return PinterestWidgetData(
                widget_id="campaign_roi",
                widget_type="bar_chart",
                title="Pinterest Campaign ROI Comparison",
                data=widget_data,
                metadata={"date_range": f"{start_date.date()} to {end_date.date()}"}
            )
            
        except Exception as e:
            logger.error(f"❌ Error generating campaign ROI widget: {e}")
            return self._create_empty_widget("campaign_roi", f"Error: {str(e)}")
    
    def get_pin_performance_widget(self, start_date: datetime, end_date: datetime,
                                 top_n: int = 50) -> PinterestWidgetData:
        """
        Create Pinterest Pin Performance Analysis Widget
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            top_n: Number of top performing pins to include
            
        Returns:
            PinterestWidgetData with pin performance analysis
        """
        try:
            logger.info("📌 Generating Pinterest Pin Performance Widget")
            
            # Get Pinterest ad data
            pinterest_data = self.pinterest_integration.get_pinterest_dashboard_data()
            
            if not pinterest_data or pinterest_data.get("error"):
                logger.warning("⚠️ No Pinterest data available for pin analysis")
                return self._create_empty_widget("pin_performance", "No Pinterest data available")
            
            # Extract ad data
            ads = pinterest_data.get("ads", [])
            if not ads:
                return self._create_empty_widget("pin_performance", "No ads found")
            
            # Get pin performance metrics
            pin_metrics = []
            for ad in ads:
                pin_id = ad.get("pin_id", "")
                if not pin_id:
                    continue
                
                # Get pin performance data
                metrics = self._get_pin_metrics(pin_id, start_date, end_date)
                
                if metrics:
                    pin_metrics.append({
                        "pin_id": pin_id,
                        "ad_id": ad.get("id", ""),
                        "campaign_id": ad.get("campaign_id", ""),
                        "impressions": metrics.get("impressions", 0),
                        "clicks": metrics.get("clicks", 0),
                        "saves": metrics.get("saves", 0),
                        "ctr": metrics.get("ctr", 0.0),
                        "save_rate": metrics.get("save_rate", 0.0),
                        "spend": metrics.get("spend", 0.0),
                        "revenue": metrics.get("revenue", 0.0)
                    })
            
            # Sort by performance score (CTR * Save Rate)
            pin_metrics.sort(key=lambda x: x["ctr"] * x["save_rate"], reverse=True)
            
            # Take top N pins
            top_pins = pin_metrics[:top_n]
            
            # Create widget data
            widget_data = {
                "pins": top_pins,
                "summary": {
                    "total_pins": len(pin_metrics),
                    "top_pins_count": len(top_pins),
                    "avg_ctr": np.mean([p["ctr"] for p in top_pins]) if top_pins else 0.0,
                    "avg_save_rate": np.mean([p["save_rate"] for p in top_pins]) if top_pins else 0.0,
                    "total_impressions": sum(p["impressions"] for p in top_pins),
                    "total_clicks": sum(p["clicks"] for p in top_pins),
                    "total_saves": sum(p["saves"] for p in top_pins)
                },
                "chart_data": {
                    "datasets": [
                        {
                            "label": "CTR vs Save Rate",
                            "data": [
                                {
                                    "x": pin["ctr"],
                                    "y": pin["save_rate"],
                                    "pin_id": pin["pin_id"],
                                    "impressions": pin["impressions"]
                                } for pin in top_pins
                            ],
                            "backgroundColor": "rgba(230, 0, 35, 0.6)"
                        }
                    ]
                }
            }
            
            logger.info(f"✅ Pin performance widget generated: {len(top_pins)} top pins")
            return PinterestWidgetData(
                widget_id="pin_performance",
                widget_type="scatter_plot",
                title="Pinterest Pin Performance Analysis",
                data=widget_data,
                metadata={"date_range": f"{start_date.date()} to {end_date.date()}", "top_n": top_n}
            )
            
        except Exception as e:
            logger.error(f"❌ Error generating pin performance widget: {e}")
            return self._create_empty_widget("pin_performance", f"Error: {str(e)}")
    
    def get_audience_demographics_widget(self, start_date: datetime, end_date: datetime) -> PinterestWidgetData:
        """
        Create Pinterest Audience Demographics Widget
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            PinterestWidgetData with audience demographics
        """
        try:
            logger.info("👥 Generating Pinterest Audience Demographics Widget")
            
            # Get audience insights from Pinterest
            if hasattr(self.attribution_system, 'feed_enhancement') and self.attribution_system.feed_enhancement:
                audience_insights = self.attribution_system.feed_enhancement.get_audience_insights()
                
                if audience_insights:
                    # Generate customer persona
                    customer_persona = self.attribution_system.feed_enhancement.generate_customer_persona(audience_insights)
                    
                    if customer_persona:
                        demographics = customer_persona.get("demographics", {})
                        behavior = customer_persona.get("behavior", {})
                        
                        # Create demographic data
                        age_groups = demographics.get("ages", [])
                        genders = demographics.get("genders", [])
                        interests = demographics.get("interests", [])
                        
                        # Create widget data
                        widget_data = {
                            "persona": {
                                "name": customer_persona.get("persona_name", "Unknown"),
                                "generated_at": customer_persona.get("generated_at", datetime.now().isoformat())
                            },
                            "demographics": {
                                "age_groups": age_groups,
                                "genders": genders,
                                "interests": interests
                            },
                            "behavior": {
                                "top_categories": behavior.get("top_categories", []),
                                "engagement_patterns": behavior.get("engagement_patterns", [])
                            },
                            "chart_data": {
                                "age_groups": [
                                    {"label": age, "value": 1} for age in age_groups
                                ],
                                "genders": [
                                    {"label": gender, "value": 1} for gender in genders
                                ],
                                "interests": [
                                    {"label": interest, "value": 1} for interest in interests
                                ]
                            }
                        }
                        
                        logger.info(f"✅ Audience demographics widget generated for persona: {widget_data['persona']['name']}")
                        return PinterestWidgetData(
                            widget_id="audience_demographics",
                            widget_type="pie_chart",
                            title="Pinterest Audience Demographics",
                            data=widget_data,
                            metadata={"date_range": f"{start_date.date()} to {end_date.date()}"}
                        )
            
            # Fallback to mock data if no audience insights available
            logger.warning("⚠️ No audience insights available, using mock data")
            return self._create_mock_audience_widget()
            
        except Exception as e:
            logger.error(f"❌ Error generating audience demographics widget: {e}")
            return self._create_empty_widget("audience_demographics", f"Error: {str(e)}")
    
    def get_purchase_funnel_widget(self, start_date: datetime, end_date: datetime) -> PinterestWidgetData:
        """
        Create Pinterest-to-Purchase Funnel Visualization Widget
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            PinterestWidgetData with purchase funnel visualization
        """
        try:
            logger.info("🔄 Generating Pinterest Purchase Funnel Widget")
            
            # Get Pinterest data
            pinterest_data = self.pinterest_integration.get_pinterest_dashboard_data()
            
            if not pinterest_data or pinterest_data.get("error"):
                logger.warning("⚠️ No Pinterest data available for funnel analysis")
                return self._create_empty_widget("purchase_funnel", "No Pinterest data available")
            
            # Calculate funnel metrics
            funnel_metrics = self._calculate_funnel_metrics(pinterest_data, start_date, end_date)
            
            # Create widget data
            widget_data = {
                "funnel_stages": [
                    {
                        "stage": "Impressions",
                        "count": funnel_metrics["impressions"],
                        "conversion_rate": 100.0
                    },
                    {
                        "stage": "Clicks",
                        "count": funnel_metrics["clicks"],
                        "conversion_rate": funnel_metrics["impression_to_click_rate"]
                    },
                    {
                        "stage": "Saves",
                        "count": funnel_metrics["saves"],
                        "conversion_rate": funnel_metrics["click_to_save_rate"]
                    },
                    {
                        "stage": "Website Clicks",
                        "count": funnel_metrics["website_clicks"],
                        "conversion_rate": funnel_metrics["save_to_website_rate"]
                    },
                    {
                        "stage": "Purchases",
                        "count": funnel_metrics["purchases"],
                        "conversion_rate": funnel_metrics["website_to_purchase_rate"]
                    }
                ],
                "summary": {
                    "total_impressions": funnel_metrics["impressions"],
                    "total_purchases": funnel_metrics["purchases"],
                    "overall_conversion_rate": funnel_metrics["overall_conversion_rate"],
                    "funnel_efficiency": funnel_metrics["funnel_efficiency"]
                },
                "chart_data": {
                    "stages": [stage["stage"] for stage in widget_data["funnel_stages"]],
                    "counts": [stage["count"] for stage in widget_data["funnel_stages"]],
                    "conversion_rates": [stage["conversion_rate"] for stage in widget_data["funnel_stages"]]
                }
            }
            
            logger.info(f"✅ Purchase funnel widget generated: {funnel_metrics['purchases']} purchases from {funnel_metrics['impressions']} impressions")
            return PinterestWidgetData(
                widget_id="purchase_funnel",
                widget_type="funnel_chart",
                title="Pinterest-to-Purchase Funnel",
                data=widget_data,
                metadata={"date_range": f"{start_date.date()} to {end_date.date()}"}
            )
            
        except Exception as e:
            logger.error(f"❌ Error generating purchase funnel widget: {e}")
            return self._create_empty_widget("purchase_funnel", f"Error: {str(e)}")
    
    def get_discovery_phase_widget(self, start_date: datetime, end_date: datetime) -> PinterestWidgetData:
        """
        Create Pinterest Discovery Phase Metrics Widget
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            PinterestWidgetData with discovery phase metrics
        """
        try:
            logger.info("🔍 Generating Pinterest Discovery Phase Widget")
            
            # Get Pinterest data
            pinterest_data = self.pinterest_integration.get_pinterest_dashboard_data()
            
            if not pinterest_data or pinterest_data.get("error"):
                logger.warning("⚠️ No Pinterest data available for discovery phase analysis")
                return self._create_empty_widget("discovery_phase", "No Pinterest data available")
            
            # Calculate discovery phase metrics
            discovery_metrics = self._calculate_discovery_phase_metrics(pinterest_data, start_date, end_date)
            
            # Create widget data
            widget_data = {
                "discovery_metrics": {
                    "impressions": discovery_metrics["impressions"],
                    "saves": discovery_metrics["saves"],
                    "closeups": discovery_metrics["closeups"],
                    "clicks": discovery_metrics["clicks"],
                    "save_rate": discovery_metrics["save_rate"],
                    "closeup_rate": discovery_metrics["closeup_rate"],
                    "click_rate": discovery_metrics["click_rate"]
                },
                "discovery_scores": {
                    "impression_score": discovery_metrics["impression_score"],
                    "save_score": discovery_metrics["save_score"],
                    "closeup_score": discovery_metrics["closeup_score"],
                    "click_score": discovery_metrics["click_score"],
                    "overall_discovery_score": discovery_metrics["overall_discovery_score"]
                },
                "chart_data": {
                    "labels": ["Impressions", "Saves", "Closeups", "Clicks"],
                    "datasets": [
                        {
                            "label": "Count",
                            "data": [
                                discovery_metrics["impressions"],
                                discovery_metrics["saves"],
                                discovery_metrics["closeups"],
                                discovery_metrics["clicks"]
                            ],
                            "backgroundColor": "rgba(230, 0, 35, 0.8)"
                        },
                        {
                            "label": "Rate (%)",
                            "data": [
                                discovery_metrics["save_rate"],
                                discovery_metrics["closeup_rate"],
                                discovery_metrics["click_rate"]
                            ],
                            "backgroundColor": "rgba(0, 123, 255, 0.8)"
                        }
                    ]
                }
            }
            
            logger.info(f"✅ Discovery phase widget generated: {discovery_metrics['overall_discovery_score']:.1f} overall score")
            return PinterestWidgetData(
                widget_id="discovery_phase",
                widget_type="line_chart",
                title="Pinterest Discovery Phase Metrics",
                data=widget_data,
                metadata={"date_range": f"{start_date.date()} to {end_date.date()}"}
            )
            
        except Exception as e:
            logger.error(f"❌ Error generating discovery phase widget: {e}")
            return self._create_empty_widget("discovery_phase", f"Error: {str(e)}")
    
    def get_trend_analysis_widget(self, start_date: datetime, end_date: datetime) -> PinterestWidgetData:
        """
        Create Pinterest Trend Analysis Widget
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            PinterestWidgetData with trend analysis
        """
        try:
            logger.info("📈 Generating Pinterest Trend Analysis Widget")
            
            # Get trending keywords and audience insights
            if hasattr(self.attribution_system, 'feed_enhancement') and self.attribution_system.feed_enhancement:
                trending_keywords = self.attribution_system.feed_enhancement.get_trending_keywords(
                    region="DE", trend_type="growing"
                )
                
                if trending_keywords:
                    keywords = trending_keywords.get("keywords", [])
                    
                    # Create trend analysis data
                    trend_data = {
                        "trending_keywords": [
                            {
                                "keyword": kw.get("keyword", ""),
                                "growth": kw.get("growth", 0.0),
                                "volume": kw.get("volume", 0)
                            } for kw in keywords[:20]  # Top 20 keywords
                        ],
                        "seasonal_performance": self._analyze_seasonal_performance(start_date, end_date),
                        "growth_rates": self._calculate_growth_rates(start_date, end_date),
                        "summary": {
                            "total_keywords": len(keywords),
                            "avg_growth": np.mean([kw.get("growth", 0.0) for kw in keywords]) if keywords else 0.0,
                            "top_keyword": keywords[0].get("keyword", "") if keywords else "",
                            "trend_score": self._calculate_trend_score(keywords)
                        }
                    }
                    
                    logger.info(f"✅ Trend analysis widget generated: {len(keywords)} trending keywords")
                    return PinterestWidgetData(
                        widget_id="trend_analysis",
                        widget_type="area_chart",
                        title="Pinterest Trend Analysis",
                        data=trend_data,
                        metadata={"date_range": f"{start_date.date()} to {end_date.date()}"}
                    )
            
            # Fallback to mock data
            logger.warning("⚠️ No trending keywords available, using mock data")
            return self._create_mock_trend_widget()
            
        except Exception as e:
            logger.error(f"❌ Error generating trend analysis widget: {e}")
            return self._create_empty_widget("trend_analysis", f"Error: {str(e)}")
    
    def get_cross_platform_widget(self, start_date: datetime, end_date: datetime) -> PinterestWidgetData:
        """
        Create Cross-Platform Pinterest Comparison Widget
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            PinterestWidgetData with cross-platform comparison
        """
        try:
            logger.info("🌐 Generating Cross-Platform Pinterest Comparison Widget")
            
            # Get cross-platform performance analysis
            performance_analysis = self.attribution_system.analyze_cross_platform_performance_with_meta_change(
                start_date, end_date
            )
            
            if not performance_analysis:
                logger.warning("⚠️ No cross-platform data available")
                return self._create_empty_widget("cross_platform", "No cross-platform data available")
            
            # Extract platform comparison data
            platform_breakdown = performance_analysis.get("platform_breakdown", {})
            attribution_scores = performance_analysis.get("attribution_scores", {})
            
            # Create cross-platform comparison data
            comparison_data = {
                "platforms": [
                    {
                        "platform": "Pinterest",
                        "impressions": platform_breakdown.get("pinterest", {}).get("impressions", 0),
                        "clicks": platform_breakdown.get("pinterest", {}).get("clicks", 0),
                        "ctr": platform_breakdown.get("pinterest", {}).get("ctr", 0.0),
                        "attribution_score": attribution_scores.get("pinterest", 0.0)
                    },
                    {
                        "platform": "Meta",
                        "impressions": platform_breakdown.get("meta", {}).get("impressions", 0),
                        "clicks": platform_breakdown.get("meta", {}).get("clicks", 0),
                        "ctr": platform_breakdown.get("meta", {}).get("ctr", 0.0),
                        "attribution_score": attribution_scores.get("meta", 0.0)
                    },
                    {
                        "platform": "Google",
                        "impressions": platform_breakdown.get("google", {}).get("impressions", 0),
                        "clicks": platform_breakdown.get("google", {}).get("clicks", 0),
                        "ctr": platform_breakdown.get("google", {}).get("ctr", 0.0),
                        "attribution_score": attribution_scores.get("google", 0.0)
                    }
                ],
                "pinterest_optimization": performance_analysis.get("pinterest_optimization", {}),
                "meta_change_insights": performance_analysis.get("meta_change_insights", {}),
                "summary": {
                    "total_impressions": performance_analysis.get("total_impressions", 0),
                    "total_clicks": performance_analysis.get("total_clicks", 0),
                    "overall_ctr": performance_analysis.get("overall_ctr", 0.0),
                    "pinterest_share": self._calculate_pinterest_share(platform_breakdown)
                }
            }
            
            logger.info(f"✅ Cross-platform widget generated: {len(comparison_data['platforms'])} platforms")
            return PinterestWidgetData(
                widget_id="cross_platform",
                widget_type="multi_bar_chart",
                title="Cross-Platform Pinterest Comparison",
                data=comparison_data,
                metadata={"date_range": f"{start_date.date()} to {end_date.date()}"}
            )
            
        except Exception as e:
            logger.error(f"❌ Error generating cross-platform widget: {e}")
            return self._create_empty_widget("cross_platform", f"Error: {str(e)}")
    
    def get_all_widgets(self, start_date: datetime, end_date: datetime) -> List[PinterestWidgetData]:
        """
        Get all Pinterest analytics widgets
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            List of PinterestWidgetData objects
        """
        try:
            logger.info(f"📊 Generating all Pinterest analytics widgets for {start_date.date()} to {end_date.date()}")
            
            widgets = [
                self.get_campaign_roi_widget(start_date, end_date),
                self.get_pin_performance_widget(start_date, end_date),
                self.get_audience_demographics_widget(start_date, end_date),
                self.get_purchase_funnel_widget(start_date, end_date),
                self.get_discovery_phase_widget(start_date, end_date),
                self.get_trend_analysis_widget(start_date, end_date),
                self.get_cross_platform_widget(start_date, end_date)
            ]
            
            logger.info(f"✅ Generated {len(widgets)} Pinterest analytics widgets")
            return widgets
            
        except Exception as e:
            logger.error(f"❌ Error generating all widgets: {e}")
            return []
    
    # Helper methods
    def _get_campaign_metrics(self, campaign_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get campaign performance metrics"""
        # This would integrate with actual Pinterest API or Track AI data
        # For now, return mock data
        return {
            "roas": np.random.uniform(1.0, 5.0),
            "cpa": np.random.uniform(10.0, 50.0),
            "revenue": np.random.uniform(100.0, 1000.0),
            "spend": np.random.uniform(50.0, 500.0),
            "impressions": np.random.randint(1000, 10000),
            "clicks": np.random.randint(50, 500),
            "purchases": np.random.randint(5, 50)
        }
    
    def _get_pin_metrics(self, pin_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get pin performance metrics"""
        # This would integrate with actual Pinterest API or Track AI data
        # For now, return mock data
        return {
            "impressions": np.random.randint(100, 5000),
            "clicks": np.random.randint(10, 500),
            "saves": np.random.randint(5, 100),
            "ctr": np.random.uniform(0.5, 5.0),
            "save_rate": np.random.uniform(1.0, 10.0),
            "spend": np.random.uniform(10.0, 100.0),
            "revenue": np.random.uniform(20.0, 200.0)
        }
    
    def _calculate_funnel_metrics(self, pinterest_data: Dict, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate funnel conversion metrics"""
        # Mock funnel calculation
        impressions = np.random.randint(10000, 100000)
        clicks = int(impressions * np.random.uniform(0.01, 0.05))
        saves = int(clicks * np.random.uniform(0.1, 0.3))
        website_clicks = int(saves * np.random.uniform(0.2, 0.5))
        purchases = int(website_clicks * np.random.uniform(0.05, 0.15))
        
        return {
            "impressions": impressions,
            "clicks": clicks,
            "saves": saves,
            "website_clicks": website_clicks,
            "purchases": purchases,
            "impression_to_click_rate": (clicks / impressions * 100) if impressions > 0 else 0,
            "click_to_save_rate": (saves / clicks * 100) if clicks > 0 else 0,
            "save_to_website_rate": (website_clicks / saves * 100) if saves > 0 else 0,
            "website_to_purchase_rate": (purchases / website_clicks * 100) if website_clicks > 0 else 0,
            "overall_conversion_rate": (purchases / impressions * 100) if impressions > 0 else 0,
            "funnel_efficiency": (purchases / clicks * 100) if clicks > 0 else 0
        }
    
    def _calculate_discovery_phase_metrics(self, pinterest_data: Dict, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate Pinterest discovery phase metrics"""
        # Mock discovery phase calculation
        impressions = np.random.randint(5000, 50000)
        saves = int(impressions * np.random.uniform(0.02, 0.08))
        closeups = int(impressions * np.random.uniform(0.05, 0.15))
        clicks = int(impressions * np.random.uniform(0.01, 0.04))
        
        save_rate = (saves / impressions * 100) if impressions > 0 else 0
        closeup_rate = (closeups / impressions * 100) if impressions > 0 else 0
        click_rate = (clicks / impressions * 100) if impressions > 0 else 0
        
        # Calculate discovery scores
        impression_score = min(impressions / 10000, 1.0) * 100
        save_score = min(save_rate / 5.0, 1.0) * 100
        closeup_score = min(closeup_rate / 10.0, 1.0) * 100
        click_score = min(click_rate / 3.0, 1.0) * 100
        
        overall_discovery_score = (impression_score + save_score + closeup_score + click_score) / 4
        
        return {
            "impressions": impressions,
            "saves": saves,
            "closeups": closeups,
            "clicks": clicks,
            "save_rate": save_rate,
            "closeup_rate": closeup_rate,
            "click_rate": click_rate,
            "impression_score": impression_score,
            "save_score": save_score,
            "closeup_score": closeup_score,
            "click_score": click_score,
            "overall_discovery_score": overall_discovery_score
        }
    
    def _analyze_seasonal_performance(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze seasonal performance trends"""
        # Mock seasonal analysis
        return {
            "spring": {"growth": 15.2, "keywords": ["floral", "pastel", "fresh"]},
            "summer": {"growth": 22.8, "keywords": ["bright", "vibrant", "beach"]},
            "fall": {"growth": 18.5, "keywords": ["cozy", "warm", "autumn"]},
            "winter": {"growth": 12.3, "keywords": ["holiday", "festive", "warm"]}
        }
    
    def _calculate_growth_rates(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate growth rates for different metrics"""
        # Mock growth rate calculation
        return {
            "impressions": np.random.uniform(-5.0, 25.0),
            "clicks": np.random.uniform(-2.0, 30.0),
            "saves": np.random.uniform(0.0, 35.0),
            "revenue": np.random.uniform(-10.0, 40.0)
        }
    
    def _calculate_trend_score(self, keywords: List[Dict]) -> float:
        """Calculate overall trend score from keywords"""
        if not keywords:
            return 0.0
        
        avg_growth = np.mean([kw.get("growth", 0.0) for kw in keywords])
        return min(avg_growth * 20, 100.0)  # Scale to 0-100
    
    def _calculate_pinterest_share(self, platform_breakdown: Dict) -> float:
        """Calculate Pinterest's share of total performance"""
        total_impressions = sum(platform.get("impressions", 0) for platform in platform_breakdown.values())
        pinterest_impressions = platform_breakdown.get("pinterest", {}).get("impressions", 0)
        
        return (pinterest_impressions / total_impressions * 100) if total_impressions > 0 else 0.0
    
    def _create_empty_widget(self, widget_id: str, message: str) -> PinterestWidgetData:
        """Create an empty widget with error message"""
        return PinterestWidgetData(
            widget_id=widget_id,
            widget_type="empty",
            title=f"Pinterest {widget_id.replace('_', ' ').title()}",
            data={"error": message, "empty": True},
            metadata={"error": True}
        )
    
    def _create_mock_audience_widget(self) -> PinterestWidgetData:
        """Create mock audience demographics widget"""
        return PinterestWidgetData(
            widget_id="audience_demographics",
            widget_type="pie_chart",
            title="Pinterest Audience Demographics",
            data={
                "persona": {"name": "Fashion Enthusiast", "generated_at": datetime.now().isoformat()},
                "demographics": {
                    "age_groups": ["25-34", "35-44"],
                    "genders": ["female", "male"],
                    "interests": ["Fashion", "Beauty", "Lifestyle"]
                },
                "behavior": {
                    "top_categories": ["Fashion", "Beauty"],
                    "engagement_patterns": ["high_engagement", "seasonal_shopper"]
                },
                "chart_data": {
                    "age_groups": [{"label": "25-34", "value": 60}, {"label": "35-44", "value": 40}],
                    "genders": [{"label": "female", "value": 70}, {"label": "male", "value": 30}],
                    "interests": [{"label": "Fashion", "value": 40}, {"label": "Beauty", "value": 30}, {"label": "Lifestyle", "value": 30}]
                }
            },
            metadata={"mock_data": True}
        )
    
    def _create_mock_trend_widget(self) -> PinterestWidgetData:
        """Create mock trend analysis widget"""
        return PinterestWidgetData(
            widget_id="trend_analysis",
            widget_type="area_chart",
            title="Pinterest Trend Analysis",
            data={
                "trending_keywords": [
                    {"keyword": "fashion", "growth": 0.15, "volume": 1000},
                    {"keyword": "style", "growth": 0.12, "volume": 800},
                    {"keyword": "trendy", "growth": 0.10, "volume": 600}
                ],
                "seasonal_performance": {
                    "spring": {"growth": 15.2, "keywords": ["floral", "pastel"]},
                    "summer": {"growth": 22.8, "keywords": ["bright", "vibrant"]}
                },
                "growth_rates": {
                    "impressions": 15.5,
                    "clicks": 22.3,
                    "saves": 18.7,
                    "revenue": 25.1
                },
                "summary": {
                    "total_keywords": 3,
                    "avg_growth": 12.3,
                    "top_keyword": "fashion",
                    "trend_score": 75.0
                }
            },
            metadata={"mock_data": True}
        )

# Convenience functions for easy integration
def get_pinterest_analytics_widgets(start_date: datetime, end_date: datetime, 
                                  track_ai_api_key: str = None) -> List[PinterestWidgetData]:
    """
    Get all Pinterest analytics widgets for a date range
    
    Args:
        start_date: Analysis start date
        end_date: Analysis end date
        track_ai_api_key: Track AI API key for data access
        
    Returns:
        List of PinterestWidgetData objects
    """
    widgets = PinterestAnalyticsWidgets(track_ai_api_key)
    return widgets.get_all_widgets(start_date, end_date)

def get_specific_pinterest_widget(widget_type: str, start_date: datetime, end_date: datetime,
                                track_ai_api_key: str = None, **kwargs) -> PinterestWidgetData:
    """
    Get a specific Pinterest analytics widget
    
    Args:
        widget_type: Type of widget to get
        start_date: Analysis start date
        end_date: Analysis end date
        track_ai_api_key: Track AI API key for data access
        **kwargs: Additional arguments for specific widgets
        
    Returns:
        PinterestWidgetData object
    """
    widgets = PinterestAnalyticsWidgets(track_ai_api_key)
    
    if widget_type == "campaign_roi":
        return widgets.get_campaign_roi_widget(start_date, end_date, **kwargs)
    elif widget_type == "pin_performance":
        return widgets.get_pin_performance_widget(start_date, end_date, **kwargs)
    elif widget_type == "audience_demographics":
        return widgets.get_audience_demographics_widget(start_date, end_date)
    elif widget_type == "purchase_funnel":
        return widgets.get_purchase_funnel_widget(start_date, end_date)
    elif widget_type == "discovery_phase":
        return widgets.get_discovery_phase_widget(start_date, end_date)
    elif widget_type == "trend_analysis":
        return widgets.get_trend_analysis_widget(start_date, end_date)
    elif widget_type == "cross_platform":
        return widgets.get_cross_platform_widget(start_date, end_date)
    else:
        raise ValueError(f"Unknown widget type: {widget_type}")

# Example usage
if __name__ == "__main__":
    # Initialize Pinterest analytics widgets
    widgets = PinterestAnalyticsWidgets()
    
    # Get widgets for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Get all widgets
    all_widgets = widgets.get_all_widgets(start_date, end_date)
    print(f"📊 Generated {len(all_widgets)} Pinterest analytics widgets")
    
    # Display widget information
    for widget in all_widgets:
        print(f"   {widget.widget_id}: {widget.title}")
        if not widget.data.get("empty", False):
            print(f"      Data points: {len(widget.data)}")
        else:
            print(f"      Error: {widget.data.get('error', 'Unknown error')}")
