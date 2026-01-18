"""Trending image fetcher from various sources"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime


class ImageFetcher:
    """Fetch trending images from various sources"""
    
    def __init__(self):
        self.pexels_api_key = None  # Optional: Set via env variable
        self.unsplash_api_key = None  # Optional: Set via env variable
    
    def fetch_reddit_images(self, subreddit: str = "pics", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch trending images from Reddit
        
        Args:
            subreddit: Subreddit name (default: "pics")
            limit: Number of posts to fetch
            
        Returns:
            List of image dictionaries with url, title, author
        """
        images = []
        
        try:
            # Reddit JSON API (no auth required for public subreddits)
            url = f"https://www.reddit.com/r/{subreddit}/hot.json"
            headers = {"User-Agent": "InstaForge/1.0"}
            params = {"limit": limit}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                
                # Only include image posts
                url_ext = post_data.get("url", "")
                if any(url_ext.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                    images.append({
                        "url": post_data.get("url"),
                        "title": post_data.get("title", ""),
                        "author": post_data.get("author", ""),
                        "score": post_data.get("score", 0),
                        "created": datetime.fromtimestamp(post_data.get("created_utc", 0)),
                        "source": "reddit",
                        "subreddit": subreddit,
                    })
        
        except Exception as e:
            print(f"Error fetching Reddit images: {e}")
        
        return images[:limit]
    
    def fetch_unsplash_images(self, query: str = "nature", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch trending images from Unsplash
        
        Note: Requires Unsplash API key (optional)
        Without API key, returns empty list with instructions
        
        Args:
            query: Search query
            limit: Number of images to fetch
            
        Returns:
            List of image dictionaries
        """
        images = []
        
        if not self.unsplash_api_key:
            # Return instructions instead of failing
            return [{
                "url": None,
                "title": "Unsplash API key required",
                "instruction": "Get API key from https://unsplash.com/developers",
                "source": "unsplash",
            }]
        
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {"Authorization": f"Client-ID {self.unsplash_api_key}"}
            params = {"query": query, "per_page": limit}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for photo in data.get("results", []):
                images.append({
                    "url": photo.get("urls", {}).get("regular"),
                    "title": photo.get("description") or photo.get("alt_description", ""),
                    "author": photo.get("user", {}).get("name", ""),
                    "likes": photo.get("likes", 0),
                    "created": datetime.fromisoformat(photo.get("created_at", "").replace("Z", "+00:00")),
                    "source": "unsplash",
                })
        
        except Exception as e:
            print(f"Error fetching Unsplash images: {e}")
        
        return images[:limit]
    
    def fetch_pexels_images(self, query: str = "nature", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch trending images from Pexels
        
        Note: Requires Pexels API key (optional)
        Without API key, returns empty list with instructions
        
        Args:
            query: Search query
            limit: Number of images to fetch
            
        Returns:
            List of image dictionaries
        """
        images = []
        
        if not self.pexels_api_key:
            return [{
                "url": None,
                "title": "Pexels API key required",
                "instruction": "Get API key from https://www.pexels.com/api/",
                "source": "pexels",
            }]
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_api_key}
            params = {"query": query, "per_page": limit}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for photo in data.get("photos", []):
                images.append({
                    "url": photo.get("src", {}).get("large"),
                    "title": photo.get("alt", ""),
                    "author": photo.get("photographer", ""),
                    "created": None,  # Pexels doesn't provide creation date
                    "source": "pexels",
                })
        
        except Exception as e:
            print(f"Error fetching Pexels images: {e}")
        
        return images[:limit]
    
    def fetch_trending_images(self, source: str = "reddit", **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch trending images from specified source
        
        Args:
            source: "reddit", "unsplash", or "pexels"
            **kwargs: Additional arguments for specific fetchers
            
        Returns:
            List of image dictionaries
        """
        if source == "reddit":
            subreddit = kwargs.get("subreddit", "pics")
            limit = kwargs.get("limit", 10)
            return self.fetch_reddit_images(subreddit, limit)
        
        elif source == "unsplash":
            query = kwargs.get("query", "nature")
            limit = kwargs.get("limit", 10)
            return self.fetch_unsplash_images(query, limit)
        
        elif source == "pexels":
            query = kwargs.get("query", "nature")
            limit = kwargs.get("limit", 10)
            return self.fetch_pexels_images(query, limit)
        
        else:
            return []
