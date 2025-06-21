"""Test script for YouTube MCP functions."""

import os
import sys
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from youtube_mcp.youtube_client import YouTubeClient
from youtube_mcp.utils import extract_video_id, extract_playlist_id, is_valid_youtube_url

# Load environment variables
load_dotenv()

def test_utility_functions():
    """Test utility functions."""
    print("=== Testing Utility Functions ===")
    
    # Test video ID extraction
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
    ]
    
    for url in test_urls:
        video_id = extract_video_id(url)
        print(f"URL: {url} -> Video ID: {video_id}")
    
    # Test playlist ID extraction
    playlist_url = "https://www.youtube.com/playlist?list=PLDoPjvoNmBAw_t_XWUFbBX-c9MafPiPLV"
    playlist_id = extract_playlist_id(playlist_url)
    print(f"Playlist URL: {playlist_url} -> Playlist ID: {playlist_id}")
    
    # Test URL validation
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    
    invalid_urls = [
        "https://www.google.com",
        "not-a-url",
        "https://vimeo.com/123456789",
    ]
    
    print("\nValid URLs:")
    for url in valid_urls:
        is_valid = is_valid_youtube_url(url)
        print(f"  {url}: {is_valid}")
    
    print("Invalid URLs:")
    for url in invalid_urls:
        is_valid = is_valid_youtube_url(url)
        print(f"  {url}: {is_valid}")


def test_youtube_client():
    """Test YouTube client functions."""
    print("\n=== Testing YouTube Client ===")
    
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("Error: YOUTUBE_API_KEY not found in environment variables")
        print("Please create a .env file with your YouTube Data API v3 key")
        return
    
    try:
        client = YouTubeClient(api_key)
        print("✓ YouTube client initialized successfully")
        
        # Test with a popular video (Rick Astley - Never Gonna Give You Up)
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        print(f"\nTesting with video: {test_video_url}")
        
        # Test caption extraction
        print("\n--- Testing Caption Extraction ---")
        try:
            captions_result = client.get_video_captions(test_video_url, "en")
            if 'error' in captions_result:
                print(f"Caption extraction failed: {captions_result['error']}")
            else:
                print(f"✓ Video Title: {captions_result.get('video_title', 'Unknown')}")
                print(f"✓ Language Used: {captions_result.get('language_used', 'Unknown')}")
                print(f"✓ Available Languages: {len(captions_result.get('available_languages', []))}")
                print(f"✓ Caption Type: {captions_result.get('caption_type', 'Unknown')}")
                if captions_result.get('captions'):
                    print(f"✓ Caption Text Length: {len(captions_result['captions'])} characters")
                    print(f"✓ Caption Preview: {captions_result['captions'][:100]}...")
                else:
                    print("⚠ No captions available")
        except Exception as e:
            print(f"Caption extraction error: {e}")
        
        # Test topic extraction
        print("\n--- Testing Topic Extraction ---")
        try:
            topics_result = client.get_video_topics(test_video_url)
            if 'error' in topics_result:
                print(f"Topic extraction failed: {topics_result['error']}")
            else:
                print(f"✓ Video Title: {topics_result.get('video_title', 'Unknown')}")
                print(f"✓ Channel: {topics_result.get('channel_title', 'Unknown')}")
                print(f"✓ Topics Found: {len(topics_result.get('topics', []))}")
                print(f"✓ Tags: {len(topics_result.get('tags', []))}")
                
                # Show first few topics if available
                topics = topics_result.get('topics', [])
                if topics:
                    print("✓ Sample Topics:")
                    for i, topic in enumerate(topics[:3]):
                        print(f"    {i+1}. {topic.get('timestamp', 'N/A')}: {topic.get('topic', 'N/A')}")
                else:
                    print("⚠ No topics found in description")
        except Exception as e:
            print(f"Topic extraction error: {e}")
        
        # Test playlist extraction with a small public playlist
        print("\n--- Testing Playlist Extraction ---")
        # Using a small educational playlist as example
        test_playlist_url = "https://www.youtube.com/playlist?list=PLDoPjvoNmBAw_t_XWUFbBX-c9MafPiPLV"
        
        try:
            playlist_result = client.get_playlist_titles(test_playlist_url)
            if 'error' in playlist_result:
                print(f"Playlist extraction failed: {playlist_result['error']}")
            else:
                print(f"✓ Playlist Title: {playlist_result.get('playlist_info', {}).get('title', 'Unknown')}")
                print(f"✓ Total Videos: {playlist_result.get('total_videos', 0)}")
                
                # Show first few videos
                videos = playlist_result.get('videos', [])
                if videos:
                    print("✓ Sample Videos:")
                    for i, video in enumerate(videos[:3]):
                        print(f"    {i+1}. {video.get('title', 'Unknown')}")
                else:
                    print("⚠ No videos found in playlist")
        except Exception as e:
            print(f"Playlist extraction error: {e}")
            
    except Exception as e:
        print(f"Error initializing YouTube client: {e}")


def main():
    """Run all tests."""
    print("YouTube MCP Function Tests")
    print("=" * 50)
    
    test_utility_functions()
    test_youtube_client()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nNote: Some tests may fail if:")
    print("- YouTube API key is not set")
    print("- Network connection issues")
    print("- Videos are private or unavailable")
    print("- API quota limits are exceeded")


if __name__ == "__main__":
    main()