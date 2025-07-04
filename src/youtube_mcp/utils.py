"""Utility functions for YouTube MCP server."""

import re
from urllib.parse import parse_qs, urlparse


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)",
        r"youtube\.com/v/([^&\n?#]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def extract_playlist_id(url: str) -> str | None:
    """Extract YouTube playlist ID from URL."""
    parsed_url = urlparse(url)

    if "youtube.com" in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)
        if "list" in query_params:
            return query_params["list"][0]

    return None


def is_valid_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube URL."""
    youtube_domains = ["youtube.com", "youtu.be", "www.youtube.com"]

    try:
        parsed = urlparse(url)
        return parsed.netloc in youtube_domains
    except Exception:
        return False


def clean_caption_text(text: str) -> str:
    """Clean caption text by removing timestamps and formatting."""
    # Remove SRT format timestamps (e.g., "00:00:01,234 --> 00:00:05,678")
    text = re.sub(r"\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}", "", text)

    # Remove SRT sequence numbers (lines with just numbers)
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)

    # Remove VTT format timestamps like [00:01:23.456] (fallback)
    text = re.sub(r"\[\d{2}:\d{2}:\d{2}\.\d{3}\]", "", text)

    # Remove HTML tags and styling
    text = re.sub(r"<[^>]+>", "", text)

    # Remove WEBVTT headers and metadata
    text = re.sub(r"^WEBVTT.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^Kind:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^Language:.*$", "", text, flags=re.MULTILINE)

    # Remove empty lines and clean up whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    text = " ".join(lines)

    # Final cleanup of extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
