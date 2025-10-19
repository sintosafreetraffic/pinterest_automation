#!/usr/bin/env python3
"""
Final Facebook Ad Library Scraper
Uses multiple strategies to find the actual ad creative content
"""

import asyncio
import logging
import re
import time
import random
from typing import Dict, Optional, List
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class FinalFacebookScraper:
    """Final Facebook scraper with multiple strategies"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def _setup_browser(self):
        """Setup Playwright browser with stealth settings"""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # Launch browser with stealth settings
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Add stealth scripts
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                window.chrome = {
                    runtime: {},
                };
            """)
            
            return True
            
        except ImportError:
            logger.error("❌ Playwright not installed. Install with: pip install playwright")
            return False
        except Exception as e:
            logger.error(f"❌ Error setting up browser: {e}")
            return False
    
    async def _cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"⚠️ Cleanup error: {e}")
    
    def extract_ad_id_from_url(self, url: str) -> Optional[str]:
        """Extract Facebook Ad ID from URL"""
        try:
            # Remove @ prefix if present
            if url.startswith('@'):
                url = url[1:]
            
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            if 'id' in query_params:
                return query_params['id'][0]
            return None
        except Exception as e:
            logger.error(f"❌ Error extracting Ad ID: {e}")
            return None
    
    def _is_profile_picture(self, src: str) -> bool:
        """Check if image is definitely a profile picture"""
        if not src:
            return True
        
        src_lower = src.lower()
        
        # Check for very small sizes (definitely profile pictures)
        very_small_sizes = ['s50x50', 's32x32', 's24x24', 's16x16', 's100x100', 's148x148', 's60x60', 's111x111']
        for size in very_small_sizes:
            if size in src_lower:
                return True
        
        # Check for profile picture patterns
        profile_patterns = [
            r'scontent.*profile.*\.jpg',
            r'scontent.*avatar.*\.jpg',
            r'scontent.*user.*\.jpg',
            r'profile.*\.jpg',
            r'avatar.*\.jpg'
        ]
        
        for pattern in profile_patterns:
            if re.search(pattern, src_lower):
                return True
        
        return False
    
    def _score_image_quality(self, src: str) -> int:
        """Score image based on likelihood of being ad creative"""
        if not src:
            return 0
        
        src_lower = src.lower()
        score = 0
        
        # Prefer larger sizes
        if 'originals' in src_lower:
            score += 1000
        elif 's736x' in src_lower:
            score += 800
        elif 's564x' in src_lower:
            score += 600
        elif 's474x' in src_lower:
            score += 400
        elif 's236x' in src_lower:
            score += 200
        elif 's148x148' in src_lower:
            score += 50
        elif 's60x60' in src_lower:
            score += 10  # Very low score for small images
        
        # Penalize profile pictures heavily
        if self._is_profile_picture(src):
            score -= 10000
        
        return score
    
    async def scrape_facebook_ad_creative(self, facebook_url: str) -> Dict:
        """Main scraping method with multiple strategies"""
        try:
            # Remove @ prefix if present before processing
            clean_url = facebook_url
            if facebook_url.startswith('@'):
                clean_url = facebook_url[1:]
            
            logger.info(f"🔍 Starting final Facebook scraping: {clean_url}")
            
            ad_id = self.extract_ad_id_from_url(facebook_url)
            if not ad_id:
                return self._create_error_result("Could not extract Ad ID")
            
            # Setup browser
            if not await self._setup_browser():
                return self._create_error_result("Failed to setup browser")
            
            # Navigate to page
            logger.info("🌐 Navigating to Facebook Ad Library...")
            await self.page.goto(clean_url, wait_until='networkidle', timeout=30000)
            
            # Wait for content to load
            await asyncio.sleep(random.uniform(3, 5))
            
            # Try multiple extraction methods
            creative_data = None
            
            # Method 1: Look for the best ad creative with multiple strategies
            creative_data = await self._extract_best_creative_multi_strategy()
            if creative_data:
                logger.info("✅ Found creative via multi-strategy extraction")
                return self._create_success_result(creative_data, ad_id)
            else:
                logger.warning("⚠️ No valid ad creative found (only profile pictures detected)")
                return self._create_error_result("No valid ad creative found - only profile pictures detected")
            
            # Method 2: Look for videos
            creative_data = await self._extract_videos()
            if creative_data:
                logger.info("✅ Found creative via video extraction")
                return self._create_success_result(creative_data, ad_id)
            
            # Method 3: Look for media in page content (filtered)
            creative_data = await self._extract_from_content_filtered()
            if creative_data:
                logger.info("✅ Found creative via filtered content extraction")
                return self._create_success_result(creative_data, ad_id)
            
            logger.warning("⚠️ No ad creative content found with any method")
            return self._create_error_result("No ad creative content found")
            
        except Exception as e:
            logger.error(f"❌ Final scraping error: {e}")
            return self._create_error_result(f"Scraping error: {str(e)}")
        finally:
            await self._cleanup()
    
    async def _extract_best_creative_multi_strategy(self) -> Optional[Dict]:
        """Extract the best creative using multiple strategies"""
        try:
            # Strategy 1: Get all images and score them
            images = await self.page.query_selector_all('img')
            logger.info(f"🔍 Found {len(images)} total images on page")
            
            candidates = []
            
            for i, img in enumerate(images):
                try:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt')
                    class_name = await img.get_attribute('class')
                    
                    # Skip if no src
                    if not src:
                        continue
                    
                    # Must be a Facebook CDN URL
                    if not ('scontent' in src.lower() or 'fbcdn' in src.lower()):
                        continue
                    
                    # Must have a valid image extension
                    if not any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        continue
                    
                    # Score the image
                    score = self._score_image_quality(src)
                    candidates.append({
                        'src': src,
                        'alt': alt,
                        'class': class_name,
                        'score': score,
                        'index': i
                    })
                    logger.info(f"📊 Candidate {len(candidates)}: score={score}, src={src[:100]}...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error analyzing image {i}: {e}")
                    continue
            
            if not candidates:
                logger.warning("⚠️ No candidates found")
                return None
            
            # Sort by score (highest first)
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Get the best candidate
            best_candidate = candidates[0]
            logger.info(f"🎯 Selected best candidate: score={best_candidate['score']}, src={best_candidate['src'][:100]}...")
            
            # If the best candidate is still a profile picture, skip it entirely
            if self._is_profile_picture(best_candidate['src']):
                logger.warning("⚠️ Best candidate is a profile picture, looking for alternatives...")
                
                # Look for non-profile pictures only
                non_profile_candidates = [c for c in candidates if not self._is_profile_picture(c['src'])]
                if non_profile_candidates:
                    best_candidate = non_profile_candidates[0]
                    logger.info(f"🎯 Selected alternative: score={best_candidate['score']}, src={best_candidate['src'][:100]}...")
                else:
                    logger.warning("⚠️ No non-profile picture alternatives found - SKIPPING this URL")
                    return None
            
            return {
                'media_url': best_candidate['src'],
                'media_type': 'image',
                'thumbnail_url': None
            }
            
        except Exception as e:
            logger.error(f"❌ Error extracting best creative: {e}")
            return None
    
    async def _extract_videos(self) -> Optional[Dict]:
        """Extract creative from videos"""
        try:
            # Look for video elements
            videos = await self.page.query_selector_all('video')
            logger.info(f"🔍 Found {len(videos)} videos on page")
            
            for i, video in enumerate(videos):
                try:
                    src = await video.get_attribute('src')
                    poster = await video.get_attribute('poster')
                    
                    if src and self._is_valid_media_url(src):
                        return {
                            'media_url': src,
                            'media_type': 'video',
                            'thumbnail_url': poster if poster else None
                        }
                    elif poster and self._is_valid_media_url(poster):
                        return {
                            'media_url': poster,
                            'media_type': 'image',
                            'thumbnail_url': None
                        }
                except Exception as e:
                    logger.warning(f"⚠️ Error analyzing video {i}: {e}")
                    continue
            
            return None
        except Exception as e:
            logger.error(f"❌ Error extracting videos: {e}")
            return None
    
    async def _extract_from_content_filtered(self) -> Optional[Dict]:
        """Extract creative from page content with filtering"""
        try:
            # Get page content
            content = await self.page.content()
            
            # Look for Facebook CDN URLs
            cdn_patterns = [
                r'https://scontent[^"\']+\.(jpg|jpeg|png|gif|webp|mp4|mov|avi|webm)',
                r'https://fbcdn[^"\']+\.(jpg|jpeg|png|gif|webp|mp4|mov|avi|webm)',
                r'https://video[^"\']+\.(jpg|jpeg|png|gif|webp|mp4|mov|avi|webm)'
            ]
            
            all_matches = []
            for pattern in cdn_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        url = match[0] if match[0] else match[1]
                    else:
                        url = match
                    
                    if self._is_valid_media_url(url):
                        all_matches.append(url)
            
            # Filter out profile pictures and score remaining
            candidates = []
            for url in all_matches:
                if not self._is_profile_picture(url):
                    score = self._score_image_quality(url)
                    candidates.append({'url': url, 'score': score})
            
            if not candidates:
                return None
            
            # Sort by score and get the best one
            candidates.sort(key=lambda x: x['score'], reverse=True)
            best_url = candidates[0]['url']
            
            return {
                'media_url': best_url,
                'media_type': self._determine_media_type(best_url),
                'thumbnail_url': None
            }
        except Exception as e:
            logger.error(f"❌ Error extracting from filtered content: {e}")
            return None
    
    def _is_valid_media_url(self, url: str) -> bool:
        """Check if URL is a valid media URL"""
        if not url or not isinstance(url, str):
            return False
        
        # Check for media extensions
        media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov', '.avi', '.webm']
        url_lower = url.lower()
        
        has_extension = any(ext in url_lower for ext in media_extensions)
        is_facebook_cdn = any(domain in url_lower for domain in ['scontent', 'fbcdn', 'video'])
        
        return has_extension and is_facebook_cdn
    
    def _determine_media_type(self, url: str) -> str:
        """Determine if URL is image or video"""
        if not url:
            return 'image'
        
        url_lower = url.lower()
        video_extensions = ['.mp4', '.mov', '.avi', '.webm']
        
        if any(ext in url_lower for ext in video_extensions):
            return 'video'
        
        return 'image'
    
    def _create_success_result(self, creative_data: Dict, ad_id: str) -> Dict:
        """Create success result"""
        return {
            'success': True,
            'media_type': creative_data['media_type'],
            'media_url': creative_data['media_url'],
            'thumbnail_url': creative_data.get('thumbnail_url'),
            'ad_id': ad_id,
            'error': None
        }
    
    def _create_error_result(self, error_msg: str) -> Dict:
        """Create error result"""
        return {
            'success': False,
            'error': error_msg,
            'media_type': None,
            'media_url': None,
            'thumbnail_url': None,
            'ad_id': None
        }

async def test_final_scraper():
    """Test the final Facebook scraper"""
    scraper = FinalFacebookScraper()
    
    test_url = "https://www.facebook.com/ads/library/?id=1952569905592186"
    
    print(f"🧪 Testing Final Facebook Scraper")
    print(f"📊 Test URL: {test_url}")
    print("🎯 Target: Actual ad creatives (not logos/profile pictures)")
    
    result = await scraper.scrape_facebook_ad_creative(test_url)
    
    print(f"\n📋 Results:")
    print(f"   Success: {result['success']}")
    print(f"   Media Type: {result['media_type']}")
    print(f"   Media URL: {result['media_url']}")
    print(f"   Ad ID: {result['ad_id']}")
    if result['error']:
        print(f"   Error: {result['error']}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_final_scraper())
