#!/usr/bin/env python3
"""
Backfill TMDB episode counts for existing TV series

This script:
1. Finds all TV series in database without total_episodes
2. Fetches episode counts from TMDB API
3. Updates the database with the data
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
from app.services.tmdb_client import get_tmdb_client
from app.core.config import settings


async def backfill_tmdb_data():
    """Backfill TMDB data for all TV series without episode counts"""
    
    print("=" * 60)
    print("TMDB Backfill Script")
    print("=" * 60)
    print()
    
    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Find all TV series without total_episodes
        query = select(Media).where(
            (Media.type == 'tv_series') &
            (Media.total_episodes == None)
        )
        
        result = await session.execute(query)
        series_list = result.scalars().all()
        
        total_series = len(series_list)
        print(f"Found {total_series} TV series without episode counts")
        print()
        
        if total_series == 0:
            print("✅ All series already have TMDB data!")
            return
        
        # Get TMDB client
        tmdb_client = get_tmdb_client()
        
        # Process each series
        enriched = 0
        not_found = 0
        failed = 0
        
        for idx, media in enumerate(series_list, 1):
            print(f"[{idx}/{total_series}] Processing: {media.title}")
            
            try:
                # Fetch episode data from TMDB
                episode_data = await tmdb_client.get_series_episode_count(media.title)
                
                if episode_data:
                    # Update media with TMDB data
                    media.total_seasons = episode_data['total_seasons']
                    media.total_episodes = episode_data['total_episodes']
                    media.tmdb_id = episode_data['tmdb_id']
                    media.last_tmdb_update = datetime.utcnow()
                    
                    print(f"  ✅ Found: {episode_data['total_episodes']} episodes across {episode_data['total_seasons']} seasons")
                    enriched += 1
                else:
                    print(f"  ⚠️  Not found on TMDB")
                    not_found += 1
                
                # Commit after each update (avoid losing all progress on error)
                await session.commit()
                
                # Small delay to respect TMDB rate limits
                await asyncio.sleep(0.3)  # ~3 requests per second
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed += 1
                await session.rollback()
        
        print()
        print("=" * 60)
        print("Backfill Complete!")
        print("=" * 60)
        print(f"Total series processed: {total_series}")
        print(f"✅ Successfully enriched: {enriched}")
        print(f"⚠️  Not found on TMDB: {not_found}")
        print(f"❌ Failed: {failed}")
        print()
    
    await engine.dispose()


if __name__ == "__main__":
    print()
    print("Starting TMDB backfill...")
    print()
    
    # Check if TMDB API key is configured
    if not settings.TMDB_API_KEY:
        print("❌ ERROR: TMDB_API_KEY not configured!")
        print("   Set TMDB_API_KEY environment variable or add to config")
        sys.exit(1)
    
    print(f"✅ TMDB API key configured")
    print(f"✅ Database: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    print()
    
    # Run the backfill
    asyncio.run(backfill_tmdb_data())
    
    print("Done! You can now refresh your library to see episode counts.")
    print()
