#!/usr/bin/env python3
"""
GitHub Integration - MODULE 4 PHASE 1
Fetches live GitHub stars for both Pinokio forks AND original repositories
Enhances app database with real-time GitHub data
"""

import os
import sys
import json
import re
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import requests
from urllib.parse import urlparse, parse_qs
import hashlib

logger = logging.getLogger(__name__)

class GitHubIntegration:
    """GitHub API integration for live stars and metadata"""
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # GitHub API setup
        self.github_token = os.environ.get('GITHUB_TOKEN')  # Optional for higher rate limits
        self.api_base = "https://api.github.com"
        self.session = requests.Session()
        
        if self.github_token:
            self.session.headers.update({'Authorization': f'token {self.github_token}'})
            logger.info("GitHub token configured - higher rate limits available")
        else:
            logger.info("No GitHub token - using public rate limits (60 requests/hour)")
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.2  # Seconds between requests
        
        # Cache settings
        self.cache_duration = 3600  # 1 hour cache
    
    def _get_cache_path(self, repo_url: str) -> Path:
        """Get cache file path for repository"""
        # Create unique filename from repo URL
        url_hash = hashlib.md5(repo_url.encode()).hexdigest()
        return self.cache_dir / f"github_cache_{url_hash}.json"
    
    def _load_from_cache(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """Load repository data from cache if not expired"""
        cache_path = self._get_cache_path(repo_url)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid
            cache_time = cached_data.get('cached_at', 0)
            if time.time() - cache_time < self.cache_duration:
                logger.debug(f"Using cached data for {repo_url}")
                return cached_data.get('data')
            else:
                logger.debug(f"Cache expired for {repo_url}")
                return None
                
        except Exception as e:
            logger.debug(f"Cache read failed for {repo_url}: {e}")
            return None
    
    def _save_to_cache(self, repo_url: str, data: Dict[str, Any]):
        """Save repository data to cache"""
        cache_path = self._get_cache_path(repo_url)
        
        try:
            cached_data = {
                'data': data,
                'cached_at': time.time(),
                'repo_url': repo_url
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cached_data, f, indent=2)
            
            logger.debug(f"Cached data for {repo_url}")
            
        except Exception as e:
            logger.debug(f"Cache save failed for {repo_url}: {e}")
    
    async def _rate_limit_delay(self):
        """Ensure we don't exceed GitHub rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            delay = self.min_request_interval - elapsed
            await asyncio.sleep(delay)
        self.last_request_time = time.time()
    
    def _extract_repo_info(self, repo_url: str) -> Optional[Tuple[str, str]]:
        """Extract owner and repo name from GitHub URL"""
        try:
            # Handle various GitHub URL formats
            patterns = [
                r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$',
                r'https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, repo_url)
                if match:
                    owner, repo = match.groups()
                    # Remove .git suffix if present
                    if repo.endswith('.git'):
                        repo = repo[:-4]
                    return owner, repo
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract repo info from {repo_url}: {e}")
            return None
    
    async def fetch_repository_data(self, repo_url: str) -> Dict[str, Any]:
        """Fetch comprehensive repository data from GitHub API"""
        try:
            # Check cache first
            cached_data = self._load_from_cache(repo_url)
            if cached_data:
                return cached_data
            
            # Extract repo information
            repo_info = self._extract_repo_info(repo_url)
            if not repo_info:
                logger.warning(f"Invalid GitHub URL: {repo_url}")
                return {'error': 'Invalid GitHub URL'}
            
            owner, repo = repo_info
            
            # Rate limiting
            await self._rate_limit_delay()
            
            # Fetch repository data
            api_url = f"{self.api_base}/repos/{owner}/{repo}"
            
            try:
                response = self.session.get(api_url, timeout=10)
                response.raise_for_status()
                repo_data = response.json()
                
                # Extract relevant information
                github_data = {
                    'stars': repo_data.get('stargazers_count', 0),
                    'forks': repo_data.get('forks_count', 0),
                    'issues': repo_data.get('open_issues_count', 0),
                    'language': repo_data.get('language', 'Unknown'),
                    'description': repo_data.get('description', ''),
                    'topics': repo_data.get('topics', []),
                    'last_updated': repo_data.get('updated_at', ''),
                    'created_at': repo_data.get('created_at', ''),
                    'size': repo_data.get('size', 0),
                    'license': repo_data.get('license', {}).get('name', 'Unknown') if repo_data.get('license') else 'Unknown',
                    'owner': owner,
                    'repo_name': repo,
                    'full_name': repo_data.get('full_name', f'{owner}/{repo}'),
                    'html_url': repo_data.get('html_url', repo_url),
                    'clone_url': repo_data.get('clone_url', repo_url),
                    'fetched_at': time.time()
                }
                
                # Check if this is a fork and try to find original
                if repo_data.get('fork'):
                    original_data = await self._find_original_repository(repo_data.get('parent', {}).get('html_url', ''))
                    if original_data:
                        github_data['original_repo'] = original_data
                        github_data['is_fork'] = True
                
                # Cache the data
                self._save_to_cache(repo_url, github_data)
                
                logger.info(f"Fetched GitHub data for {owner}/{repo}: {github_data['stars']} stars")
                return github_data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"GitHub API request failed for {repo_url}: {e}")
                return {'error': f'API request failed: {e}', 'stars': 0}
                
        except Exception as e:
            logger.error(f"GitHub data fetch failed for {repo_url}: {e}")
            return {'error': str(e), 'stars': 0}
    
    async def _find_original_repository(self, parent_url: str) -> Optional[Dict[str, Any]]:
        """Find original repository data for forks"""
        if not parent_url:
            return None
        
        try:
            # Recursive fetch of parent repository
            original_data = await self.fetch_repository_data(parent_url)
            if 'error' not in original_data:
                return {
                    'stars': original_data.get('stars', 0),
                    'forks': original_data.get('forks', 0),
                    'language': original_data.get('language', 'Unknown'),
                    'last_updated': original_data.get('last_updated', ''),
                    'html_url': parent_url,
                    'full_name': original_data.get('full_name', '')
                }
        except Exception as e:
            logger.debug(f"Failed to fetch original repo data: {e}")
        
        return None
    
    async def enhance_app_database(self, apps_data: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Enhance entire app database with GitHub stars and metadata"""
        try:
            enhanced_apps = {}
            total_apps = len(apps_data)
            processed = 0
            
            if progress_callback:
                progress_callback(f"🌟 Starting GitHub enhancement for {total_apps} apps")
                progress_callback(f"⚡ This will fetch live stars for Pinokio forks AND original repositories")
            
            for app_key, app_data in apps_data.items():
                processed += 1
                app_name = app_data.get('name', app_key)
                
                if progress_callback and processed % 10 == 0:
                    progress_callback(f"📊 Processing GitHub data: {processed}/{total_apps} apps ({(processed/total_apps*100):.1f}%)")
                
                # Get repository URL
                repo_url = app_data.get('clone_url', app_data.get('repo_url', ''))
                
                if repo_url and 'github.com' in repo_url:
                    try:
                        # Fetch GitHub data
                        github_data = await self.fetch_repository_data(repo_url)
                        
                        if 'error' not in github_data:
                            # Enhance app data with GitHub information
                            enhanced_app = {
                                **app_data,  # Keep all original data
                                
                                # Pinokio fork information
                                'pinokio_stars': github_data.get('stars', 0),
                                'pinokio_forks': github_data.get('forks', 0),
                                'pinokio_language': github_data.get('language', 'Unknown'),
                                'pinokio_last_updated': github_data.get('last_updated', ''),
                                'pinokio_license': github_data.get('license', 'Unknown'),
                                'pinokio_topics': github_data.get('topics', []),
                                
                                # Original repository information (if fork)
                                'is_fork': github_data.get('is_fork', False),
                                'original_stars': 0,
                                'original_forks': 0,
                                'original_url': '',
                                'total_stars': github_data.get('stars', 0),  # Will be updated if original found
                                
                                # Enhanced categorization
                                'enhanced_tags': self._generate_smart_tags(app_data, github_data),
                                'quality_score': self._calculate_quality_score(app_data, github_data),
                                'github_data_updated': time.time()
                            }
                            
                            # Add original repository data if it's a fork
                            if github_data.get('original_repo'):
                                original = github_data['original_repo']
                                enhanced_app.update({
                                    'original_stars': original.get('stars', 0),
                                    'original_forks': original.get('forks', 0),
                                    'original_url': original.get('html_url', ''),
                                    'original_language': original.get('language', 'Unknown'),
                                    'original_last_updated': original.get('last_updated', ''),
                                    'total_stars': enhanced_app['pinokio_stars'] + original.get('stars', 0)
                                })
                            
                            enhanced_apps[app_key] = enhanced_app
                            
                            if progress_callback and github_data.get('stars', 0) > 0:
                                total_stars = enhanced_app['total_stars']
                                progress_callback(f"⭐ {app_name}: {total_stars} total stars (Pinokio: {enhanced_app['pinokio_stars']}, Original: {enhanced_app.get('original_stars', 0)})")
                        else:
                            # Keep original data if GitHub fetch failed
                            enhanced_apps[app_key] = {
                                **app_data,
                                'pinokio_stars': 0,
                                'original_stars': 0,
                                'total_stars': 0,
                                'github_error': github_data.get('error', 'Unknown error'),
                                'enhanced_tags': self._generate_smart_tags(app_data, {}),
                                'quality_score': self._calculate_quality_score(app_data, {})
                            }
                    
                    except Exception as e:
                        logger.debug(f"Failed to enhance {app_name}: {e}")
                        enhanced_apps[app_key] = {
                            **app_data,
                            'pinokio_stars': 0,
                            'original_stars': 0,
                            'total_stars': 0,
                            'enhancement_error': str(e)
                        }
                else:
                    # No GitHub URL, keep original data with defaults
                    enhanced_apps[app_key] = {
                        **app_data,
                        'pinokio_stars': 0,
                        'original_stars': 0,
                        'total_stars': 0,
                        'enhanced_tags': self._generate_smart_tags(app_data, {}),
                        'quality_score': self._calculate_quality_score(app_data, {})
                    }
                
                # Small delay to be nice to GitHub API
                if processed % 5 == 0:
                    await asyncio.sleep(0.5)
            
            if progress_callback:
                total_stars = sum(app.get('total_stars', 0) for app in enhanced_apps.values())
                progress_callback(f"🎉 GitHub enhancement complete! Total stars across all apps: {total_stars:,}")
            
            return enhanced_apps
            
        except Exception as e:
            logger.error(f"Database enhancement failed: {e}")
            return apps_data  # Return original data if enhancement fails
    
    def _generate_smart_tags(self, app_data: Dict[str, Any], github_data: Dict[str, Any]) -> List[str]:
        """Generate smart tags based on app data and GitHub information"""
        tags = set()
        
        # Add existing tags
        existing_tags = app_data.get('tags', [])
        if existing_tags:
            tags.update(existing_tags)
        
        # Add category-based tags
        category = app_data.get('category', '')
        if category:
            tags.add(category.lower())
        
        # Add GitHub topics as tags
        github_topics = github_data.get('topics', [])
        tags.update(github_topics)
        
        # Add language-based tags
        language = github_data.get('language', '')
        if language and language != 'Unknown':
            tags.add(f"lang-{language.lower()}")
        
        # Add popularity tags based on stars
        total_stars = github_data.get('stars', 0)
        if total_stars > 1000:
            tags.add('popular')
        elif total_stars > 100:
            tags.add('well-liked')
        elif total_stars > 10:
            tags.add('community-approved')
        
        # Add recency tags
        last_updated = github_data.get('last_updated', '')
        if last_updated:
            try:
                from datetime import datetime, timezone
                updated_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                days_ago = (datetime.now(timezone.utc) - updated_time).days
                
                if days_ago < 30:
                    tags.add('recently-updated')
                elif days_ago < 90:
                    tags.add('actively-maintained')
                elif days_ago > 365:
                    tags.add('legacy')
            except:
                pass
        
        # Add quality tags based on repository metrics
        if github_data.get('license') and github_data['license'] != 'Unknown':
            tags.add('licensed')
        
        if github_data.get('forks', 0) > 10:
            tags.add('community-forked')
        
        # Convert to sorted list
        return sorted(list(tags))
    
    def _calculate_quality_score(self, app_data: Dict[str, Any], github_data: Dict[str, Any]) -> float:
        """Calculate quality score based on multiple factors"""
        score = 0.0
        
        # Base score for being a verified Pinokio app
        if app_data.get('is_pinokio_app', False):
            score += 10.0
        
        # GitHub stars contribution (logarithmic scale)
        stars = github_data.get('stars', 0)
        if stars > 0:
            import math
            score += min(20.0, math.log(stars + 1) * 3)  # Max 20 points for stars
        
        # Maintenance score
        last_updated = github_data.get('last_updated', '')
        if last_updated:
            try:
                from datetime import datetime, timezone
                updated_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                days_ago = (datetime.now(timezone.utc) - updated_time).days
                
                if days_ago < 30:
                    score += 15.0  # Recently updated
                elif days_ago < 90:
                    score += 10.0  # Actively maintained
                elif days_ago < 365:
                    score += 5.0   # Maintained
                # No points for very old repositories
            except:
                pass
        
        # Documentation score
        if app_data.get('description'):
            score += 5.0
        
        # License score
        if github_data.get('license') and github_data['license'] != 'Unknown':
            score += 5.0
        
        # Community engagement score
        forks = github_data.get('forks', 0)
        if forks > 5:
            score += min(10.0, forks * 0.5)  # Max 10 points for forks
        
        # Category bonus
        category = app_data.get('category', '')
        if category in ['IMAGE', 'AUDIO', 'VIDEO', 'LLM']:
            score += 5.0
        
        # Has install script bonus
        if app_data.get('has_install_js') or app_data.get('has_install_json'):
            score += 10.0
        
        # Normalize to 0-100 scale
        return min(100.0, max(0.0, score))
    
    async def enhance_single_app(self, app_data: Dict[str, Any], app_key: str = '') -> Dict[str, Any]:
        """Enhance single app with GitHub data - useful for real-time updates"""
        try:
            repo_url = app_data.get('clone_url', app_data.get('repo_url', ''))
            
            if repo_url and 'github.com' in repo_url:
                github_data = await self.fetch_repository_data(repo_url)
                
                if 'error' not in github_data:
                    enhanced_app = {
                        **app_data,
                        'pinokio_stars': github_data.get('stars', 0),
                        'pinokio_forks': github_data.get('forks', 0),
                        'pinokio_language': github_data.get('language', 'Unknown'),
                        'pinokio_last_updated': github_data.get('last_updated', ''),
                        'pinokio_topics': github_data.get('topics', []),
                        'is_fork': github_data.get('is_fork', False),
                        'enhanced_tags': self._generate_smart_tags(app_data, github_data),
                        'quality_score': self._calculate_quality_score(app_data, github_data),
                        'total_stars': github_data.get('stars', 0)
                    }
                    
                    # Add original repo data if available
                    if github_data.get('original_repo'):
                        original = github_data['original_repo']
                        enhanced_app.update({
                            'original_stars': original.get('stars', 0),
                            'original_url': original.get('html_url', ''),
                            'total_stars': enhanced_app['pinokio_stars'] + original.get('stars', 0)
                        })
                    
                    return enhanced_app
            
            # Return original data if no enhancement possible
            return {
                **app_data,
                'pinokio_stars': 0,
                'original_stars': 0,
                'total_stars': 0,
                'enhanced_tags': self._generate_smart_tags(app_data, {}),
                'quality_score': self._calculate_quality_score(app_data, {})
            }
            
        except Exception as e:
            logger.error(f"Single app enhancement failed: {e}")
            return app_data
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current GitHub API rate limit status"""
        try:
            response = self.session.get(f"{self.api_base}/rate_limit", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'Rate limit check failed: {response.status_code}'}
        except Exception as e:
            return {'error': str(e)}
    
    async def batch_enhance_apps(self, apps_data: Dict[str, Any], batch_size: int = 10, delay: float = 2.0) -> Dict[str, Any]:
        """Enhance apps in batches to respect rate limits"""
        try:
            enhanced_apps = {}
            app_items = list(apps_data.items())
            total_batches = (len(app_items) + batch_size - 1) // batch_size
            
            logger.info(f"Processing {len(app_items)} apps in {total_batches} batches of {batch_size}")
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(app_items))
                batch_apps = app_items[start_idx:end_idx]
                
                logger.info(f"Processing batch {batch_num + 1}/{total_batches}: {len(batch_apps)} apps")
                
                # Process batch concurrently
                tasks = []
                for app_key, app_data in batch_apps:
                    task = self.enhance_single_app(app_data, app_key)
                    tasks.append((app_key, task))
                
                # Wait for batch to complete
                for app_key, task in tasks:
                    enhanced_app = await task
                    enhanced_apps[app_key] = enhanced_app
                
                # Delay between batches
                if batch_num < total_batches - 1:
                    logger.info(f"Waiting {delay} seconds before next batch...")
                    await asyncio.sleep(delay)
            
            logger.info(f"Batch enhancement complete: {len(enhanced_apps)} apps processed")
            return enhanced_apps
            
        except Exception as e:
            logger.error(f"Batch enhancement failed: {e}")
            return apps_data