"""
RSS Feed Fetcher with PostgreSQL caching
Handles news fetching from multiple sources
"""

import requests
import xmltodict
from datetime import datetime
from typing import List, Dict, Optional
from database.connection import db_manager
from database.models import NewsModel, ActivityModel
from loguru import logger
import streamlit as st
from cachetools import TTLCache
import asyncio
import aiohttp

# Cache for RSS responses (30 minutes)
rss_cache = TTLCache(maxsize=100, ttl=1800)

# News sources configuration
NEWS_SOURCES = {
    "Times of India": {
        "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "category": "General"
    },
    "The Hindu": {
        "url": "https://www.thehindu.com/news/national/feeder/default.rss",
        "category": "Politics"
    },
    "India Today": {
        "url": "https://www.indiatoday.in/rss/home",
        "category": "General"
    },
    "Sports": {
        "url": "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms",
        "category": "Sports"
    },
    "Technology": {
        "url": "https://www.indiatoday.in/technology/rss",
        "category": "Technology"
    },
    "Business": {
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "category": "Business"
    },
    "Entertainment": {
        "url": "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms",
        "category": "Entertainment"
    },
    "Health": {
        "url": "https://www.indiatoday.in/health/rss",
        "category": "Health"
    }
}


class NewsFetcher:
    """Fetch and manage news articles"""

    @staticmethod
    def fetch_rss_feed(url: str, source_name: str, category: str) -> List[Dict]:
        """Fetch RSS feed and parse articles"""
        try:
            # Check cache
            cache_key = f"rss_{url}"
            if cache_key in rss_cache:
                return rss_cache[cache_key]

            # Fetch feed
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(
                    f"Failed to fetch {source_name}: {response.status_code}")
                return []

            # Parse XML
            data = xmltodict.parse(response.content)

            # Extract items
            items = []
            if "rss" in data and "channel" in data["rss"]:
                channel = data["rss"]["channel"]
                if "item" in channel:
                    raw_items = channel["item"]
                    if isinstance(raw_items, dict):
                        raw_items = [raw_items]

                    for item in raw_items[:10]:  # Limit to 10 per source
                        try:
                            # Parse date
                            pub_date = item.get("pubDate", "")
                            try:
                                published_at = datetime.strptime(
                                    pub_date, "%a, %d %b %Y %H:%M:%S %z")
                            except:
                                published_at = datetime.now()

                            article = {
                                "title": item.get("title", "No Title"),
                                "url": item.get("link", "#"),
                                "source": source_name,
                                "category": category,
                                "published_at": published_at,
                                "description": item.get("description", ""),
                                "content": item.get("content:encoded", item.get("description", ""))
                            }

                            # Clean description (remove HTML)
                            if article["description"]:
                                article["description"] = article["description"].split('<')[
                                    0][:300]

                            items.append(article)

                            # Save to database cache
                            NewsModel.save_article(article)

                        except Exception as e:
                            logger.error(
                                f"Error parsing article from {source_name}: {e}")
                            continue

            # Cache results
            rss_cache[cache_key] = items
            logger.info(f"Fetched {len(items)} articles from {source_name}")
            return items

        except Exception as e:
            logger.error(f"Error fetching RSS feed {source_name}: {e}")
            return []

    @staticmethod
    def get_news_for_user(user_id: str, selected_sources: List[str], category: str) -> List[Dict]:
        """Get personalized news for user"""
        all_articles = []

        # Fetch from selected sources
        for source_name in selected_sources:
            if source_name in NEWS_SOURCES:
                source_config = NEWS_SOURCES[source_name]
                articles = NewsFetcher.fetch_rss_feed(
                    source_config["url"],
                    source_name,
                    source_config["category"]
                )
                all_articles.extend(articles)

        # Fetch from category feed
        if category in NEWS_SOURCES:
            source_config = NEWS_SOURCES[category]
            articles = NewsFetcher.fetch_rss_feed(
                source_config["url"],
                category,
                source_config["category"]
            )
            all_articles.extend(articles)

        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        # Log activity
        ActivityModel.log_activity(user_id, 'news_fetched', {
                                   'count': len(unique_articles)})

        return unique_articles[:30]  # Limit to 30 articles

    @staticmethod
    def search_news(query: str, category: str = None) -> List[Dict]:
        """Search news using PostgreSQL full-text search"""
        return NewsModel.search_articles(query, category, limit=20)

# Async version for better performance (optional)


async def fetch_rss_async(session, source_name: str, source_config: Dict):
    """Async RSS fetcher for better performance"""
    try:
        async with session.get(source_config["url"]) as response:
            if response.status == 200:
                content = await response.text()
                data = xmltodict.parse(content)
                # Process data...
                return []
    except Exception as e:
        logger.error(f"Async fetch error for {source_name}: {e}")
        return []


async def fetch_multiple_sources(sources: List[str]):
    """Fetch multiple RSS feeds concurrently"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for source_name in sources:
            if source_name in NEWS_SOURCES:
                tasks.append(fetch_rss_async(
                    session, source_name, NEWS_SOURCES[source_name]))

        results = await asyncio.gather(*tasks)
        return results
