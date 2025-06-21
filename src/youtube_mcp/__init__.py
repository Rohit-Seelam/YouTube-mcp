"""YouTube MCP Server - A Model Context Protocol server for YouTube operations."""

__version__ = "0.1.0"
__author__ = "Rohitseelam"
__email__ = "shreerohit24@gmail.com"

from .youtube_client import YouTubeClient
from .server import main

__all__ = ["YouTubeClient", "main"]