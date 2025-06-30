"""YouTube MCP Server - Model Context Protocol server for YouTube operations."""

import logging
import os
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .utils import is_valid_youtube_url
from .youtube_client import YouTubeClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Set debug level if specified in environment
if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")

# Initialize FastMCP server
mcp = FastMCP("YouTube MCP")

# Initialize YouTube client
youtube_client = None


def get_youtube_client() -> YouTubeClient:
    """Get or create YouTube client instance."""
    global youtube_client
    if youtube_client is None:
        logger.info("Initializing YouTube client")
        try:
            youtube_client = YouTubeClient()
            logger.info("YouTube client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube client: {e}")
            raise
    return youtube_client


@mcp.tool()
def extract_youtube_captions(video_url: str, language_preference: str = "en") -> dict[str, Any]:
    """Extract captions/subtitles from a YouTube video.

    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
        language_preference: Preferred language code (e.g., 'en', 'es', 'fr'). Defaults to 'en'.

    Returns:
        Dictionary containing video information and captions data.
    """
    logger.info(
        f"extract_youtube_captions called with URL: {video_url}, language: {language_preference}",
    )

    try:
        if not is_valid_youtube_url(video_url):
            logger.warning(f"Invalid YouTube URL provided: {video_url}")
            return {
                "error": "Invalid YouTube URL provided",
                "message": "Please provide a valid YouTube video URL",
            }

        client = get_youtube_client()
        logger.debug(f"Extracting captions for video: {video_url}")
        result = client.get_video_captions(video_url, language_preference)

        if "error" in result:
            logger.error(f"Caption extraction failed: {result.get('error', 'Unknown error')}")
        else:
            logger.info(
                f"Successfully extracted captions for video: {result.get('video_title', 'Unknown')}",
            )

        return result

    except Exception as e:
        logger.error(f"Exception in extract_youtube_captions: {e!s}")
        return {"error": str(e), "message": "Failed to extract captions from YouTube video"}


@mcp.tool()
def extract_video_topics(video_url: str) -> dict[str, Any]:
    """Extract topics and sections from a YouTube video description.

    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)

    Returns:
        Dictionary containing video information and extracted topics/sections.
    """
    logger.info(f"extract_video_topics called with URL: {video_url}")

    try:
        if not is_valid_youtube_url(video_url):
            logger.warning(f"Invalid YouTube URL provided: {video_url}")
            return {
                "error": "Invalid YouTube URL provided",
                "message": "Please provide a valid YouTube video URL",
            }

        client = get_youtube_client()
        logger.debug(f"Extracting topics for video: {video_url}")
        result = client.get_video_topics(video_url)

        if "error" in result:
            logger.error(f"Topic extraction failed: {result.get('error', 'Unknown error')}")
        else:
            topics_count = len(result.get("topics", []))
            logger.info(
                f"Successfully extracted {topics_count} topics for video: {result.get('video_title', 'Unknown')}",
            )

        return result

    except Exception as e:
        logger.error(f"Exception in extract_video_topics: {e!s}")
        return {"error": str(e), "message": "Failed to extract topics from YouTube video"}


@mcp.tool()
def extract_playlist_titles(playlist_url: str) -> dict[str, Any]:
    """Extract video titles from a YouTube playlist.

    Args:
        playlist_url: YouTube playlist URL (e.g., https://www.youtube.com/playlist?list=PLAYLIST_ID)

    Returns:
        Dictionary containing playlist information and video titles.
    """
    logger.info(f"extract_playlist_titles called with URL: {playlist_url}")

    try:
        if not is_valid_youtube_url(playlist_url):
            logger.warning(f"Invalid YouTube URL provided: {playlist_url}")
            return {
                "error": "Invalid YouTube URL provided",
                "message": "Please provide a valid YouTube playlist URL",
            }

        if "list=" not in playlist_url:
            logger.warning(f"URL does not contain playlist parameter: {playlist_url}")
            return {
                "error": "Invalid playlist URL",
                "message": "URL does not appear to be a YouTube playlist",
            }

        client = get_youtube_client()
        logger.debug(f"Extracting playlist titles for: {playlist_url}")
        result = client.get_playlist_titles(playlist_url)

        if "error" in result:
            logger.error(f"Playlist extraction failed: {result.get('error', 'Unknown error')}")
        else:
            video_count = result.get("total_videos", 0)
            playlist_title = result.get("playlist_info", {}).get("title", "Unknown")
            logger.info(
                f"Successfully extracted {video_count} videos from playlist: {playlist_title}",
            )

        return result

    except Exception as e:
        logger.error(f"Exception in extract_playlist_titles: {e!s}")
        return {"error": str(e), "message": "Failed to extract titles from YouTube playlist"}


def main():
    """Main entry point for the MCP server."""
    logger.info("YouTube MCP Server main() called")

    # Check for API key
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logger.error("YOUTUBE_API_KEY environment variable is required")
        print("Error: YOUTUBE_API_KEY environment variable is required")
        print("Please set your YouTube Data API v3 key from Google Cloud Platform")
        return

    try:
        logger.info("FastMCP server initialized successfully")

        # Test the YouTube client initialization
        logger.info("Testing YouTube client initialization")
        get_youtube_client()

        logger.info("YouTube MCP Server starting...")
        print("YouTube MCP Server starting...")
        print("Available tools:")
        print("  - extract_youtube_captions: Extract captions from YouTube videos")
        print("  - extract_video_topics: Extract topics/sections from video descriptions")
        print("  - extract_playlist_titles: Extract video titles from playlists")

        # Run the FastMCP server
        logger.info("Starting FastMCP server with stdio transport")
        mcp.run(transport="stdio")
        logger.info("FastMCP server started successfully")

    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"Error starting server: {e}")
        return


if __name__ == "__main__":
    main()
