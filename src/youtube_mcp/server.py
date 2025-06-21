"""YouTube MCP Server - Model Context Protocol server for YouTube operations."""

import asyncio
import os
from typing import Any, Dict
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from .youtube_client import YouTubeClient
from .utils import is_valid_youtube_url

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("YouTube MCP")

# Initialize YouTube client
youtube_client = None

def get_youtube_client() -> YouTubeClient:
    """Get or create YouTube client instance."""
    global youtube_client
    if youtube_client is None:
        youtube_client = YouTubeClient()
    return youtube_client


@mcp.tool()
def extract_youtube_captions(video_url: str, language_preference: str = "en") -> Dict[str, Any]:
    """Extract captions/subtitles from a YouTube video.
    
    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
        language_preference: Preferred language code (e.g., 'en', 'es', 'fr'). Defaults to 'en'.
    
    Returns:
        Dictionary containing video information and captions data.
    """
    try:
        if not is_valid_youtube_url(video_url):
            return {
                'error': 'Invalid YouTube URL provided',
                'message': 'Please provide a valid YouTube video URL'
            }
        
        client = get_youtube_client()
        result = client.get_video_captions(video_url, language_preference)
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Failed to extract captions from YouTube video'
        }


@mcp.tool()
def extract_video_topics(video_url: str) -> Dict[str, Any]:
    """Extract topics and sections from a YouTube video description.
    
    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
    
    Returns:
        Dictionary containing video information and extracted topics/sections.
    """
    try:
        if not is_valid_youtube_url(video_url):
            return {
                'error': 'Invalid YouTube URL provided',
                'message': 'Please provide a valid YouTube video URL'
            }
        
        client = get_youtube_client()
        result = client.get_video_topics(video_url)
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Failed to extract topics from YouTube video'
        }


@mcp.tool()
def extract_playlist_titles(playlist_url: str) -> Dict[str, Any]:
    """Extract video titles from a YouTube playlist.
    
    Args:
        playlist_url: YouTube playlist URL (e.g., https://www.youtube.com/playlist?list=PLAYLIST_ID)
    
    Returns:
        Dictionary containing playlist information and video titles.
    """
    try:
        if not is_valid_youtube_url(playlist_url):
            return {
                'error': 'Invalid YouTube URL provided',
                'message': 'Please provide a valid YouTube playlist URL'
            }
        
        if 'list=' not in playlist_url:
            return {
                'error': 'Invalid playlist URL',
                'message': 'URL does not appear to be a YouTube playlist'
            }
        
        client = get_youtube_client()
        result = client.get_playlist_titles(playlist_url)
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Failed to extract titles from YouTube playlist'
        }


def main():
    """Main entry point for the MCP server."""
    # Check for API key
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("Error: YOUTUBE_API_KEY environment variable is required")
        print("Please set your YouTube Data API v3 key from Google Cloud Platform")
        return
    
    try:
        # Test the YouTube client initialization
        get_youtube_client()
        print("YouTube MCP Server starting...")
        print("Available tools:")
        print("  - extract_youtube_captions: Extract captions from YouTube videos")
        print("  - extract_video_topics: Extract topics/sections from video descriptions")
        print("  - extract_playlist_titles: Extract video titles from playlists")
        
        # Run the FastMCP server
        mcp.run(transport="stdio")
        
    except Exception as e:
        print(f"Error starting server: {e}")
        return


if __name__ == "__main__":
    main()