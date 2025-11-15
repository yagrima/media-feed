#!/usr/bin/env python3
"""
Test why Felix Lobrecht doesn't have TMDB data
"""
import httpx
import asyncio
import os

async def test_felix():
    api_key = os.environ.get('TMDB_API_KEY', 'e12b73358b4ea2e981180ac122b4b2a3')
    client = httpx.AsyncClient()
    
    titles = [
        "Felix Lobrecht LIVE - Kenn ick!",
        "Felix Lobrecht Kenn ick",
        "Kenn ick",
        "Felix Lobrecht"
    ]
    
    print("=" * 60)
    print("Testing TMDB search for Felix Lobrecht")
    print("=" * 60)
    print()
    
    for title in titles:
        print(f"Searching: '{title}'")
        print("-" * 60)
        
        # Search as TV Series
        resp = await client.get('https://api.themoviedb.org/3/search/tv', params={
            'api_key': api_key,
            'query': title
        })
        tv_results = resp.json()
        tv_count = len(tv_results.get('results', []))
        print(f"  TV Series: {tv_count} results")
        if tv_results.get('results'):
            for i, result in enumerate(tv_results['results'][:3], 1):
                print(f"    {i}. {result['name']} (ID: {result['id']})")
        
        # Search as Movie
        resp2 = await client.get('https://api.themoviedb.org/3/search/movie', params={
            'api_key': api_key,
            'query': title
        })
        movie_results = resp2.json()
        movie_count = len(movie_results.get('results', []))
        print(f"  Movies: {movie_count} results")
        if movie_results.get('results'):
            for i, result in enumerate(movie_results['results'][:3], 1):
                print(f"    {i}. {result['title']} (ID: {result['id']})")
        
        print()
    
    await client.aclose()
    
    print("=" * 60)
    print("Conclusion:")
    print("If 0 TV results but >0 Movie results:")
    print("  -> It's categorized as Movie on TMDB, not TV Series")
    print("  -> Should be imported as 'movie' type, not 'tv_series'")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_felix())
