#!/usr/bin/env python3
"""
Backfill TMDB episode counts for existing TV series (WITHOUT CACHE)

This version disables Redis caching to test TMDB integration independently.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.db.models import Media
from app.core.config import settings
import httpx
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple TMDB client without Redis cache
class SimpleTMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def search_tv(self, query: str):
        """Search for TV series"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/search/tv",
                params={
                    'api_key': self.api_key,
                    'query': query
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            logger.error(f"TMDB search error: {e}")
            return []
    
    async def get_tv_details(self, tv_id: int):
        """Get TV series details"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/tv/{tv_id}",
                params={'api_key': self.api_key}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"TMDB details error: {e}")
            return None
    
    async def get_series_episode_count(self, series_name: str):
        """Get episode count for series"""
        try:
            # Search
            results = await self.search_tv(series_name)
            if not results:
                return None
            
            # Get details
            tv_id = results[0].get('id')
            details = await self.get_tv_details(tv_id)
            if not details:
                return None
            
            total_seasons = details.get('number_of_seasons', 0)
            total_episodes = details.get('number_of_episodes', 0)
            
            if total_episodes > 0:
                return {
                    'total_seasons': total_seasons,
                    'total_episodes': total_episodes,
                    'tmdb_id': tv_id
                }
            return None
        except Exception as e:
            logger.error(f"Error getting episode count: {e}")
            return None
    
    async def close(self):
        await self.client.aclose()


async def backfill_tmdb_data():
    """Backfill TMDB data without Redis cache"""
    
    print("=" * 60)
    print("TMDB Backfill Script (No Cache)")
    print("=" * 60)
    print()
    
    # Check API key
    if not settings.TMDB_API_KEY:
        print("[ERROR] TMDB_API_KEY not configured!")
        return
    
    print(f"[OK] TMDB API key configured")
    print(f"[OK] Database: {settings.DATABASE_URL.split('@')[-1]}")
    print()
    
    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create simple TMDB client (no cache)
    tmdb = SimpleTMDBClient(settings.TMDB_API_KEY)
    
    async with async_session() as session:
        # Find TV series without episode counts
        query = select(Media).where(
            (Media.type == 'tv_series') &
            (Media.total_episodes == None)
        )
        
        result = await session.execute(query)
        series_list = result.scalars().all()
        
        total = len(series_list)
        print(f"Found {total} TV series without episode counts")
        print()
        
        if total == 0:
            print("[OK] All series have TMDB data!")
            return
        
        enriched = 0
        not_found = 0
        failed = 0
        
        for idx, media in enumerate(series_list, 1):
            print(f"[{idx}/{total}] {media.title}")
            
            try:
                episode_data = await tmdb.get_series_episode_count(media.title)
                
                if episode_data:
                    media.total_seasons = episode_data['total_seasons']
                    media.total_episodes = episode_data['total_episodes']
                    media.tmdb_id = episode_data['tmdb_id']
                    media.last_tmdb_update = datetime.utcnow()
                    
                    print(f"  [OK] {episode_data['total_episodes']} episodes, {episode_data['total_seasons']} seasons")
                    enriched += 1
                    await session.commit()
                else:
                    print(f"  [WARNING] Not found on TMDB")
                    not_found += 1
                
                # Rate limit
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"  [ERROR] {e}")
                failed += 1
                await session.rollback()
        
        print()
        print("=" * 60)
        print(f"Processed: {total}")
        print(f"[OK] Enriched: {enriched}")
        print(f"[WARNING] Not found: {not_found}")
        print(f"[ERROR] Failed: {failed}")
        print("=" * 60)
    
    await tmdb.close()
    await engine.dispose()


if __name__ == "__main__":
    print()
    asyncio.run(backfill_tmdb_data())
    print()
