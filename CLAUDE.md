# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube MCP (Model Context Protocol) server that provides three main tools:
1. **Extract YouTube Captions** - Retrieve entire captions from YouTube videos (multi-language support)
2. **Extract Video Topics** - Extract description topics/sections from YouTube videos  
3. **Extract Playlist Titles** - Get titles of all videos in a YouTube playlist

## Development Plan

### Phase 0: Project Documentation ✓
- [x] Update CLAUDE.md with comprehensive project plan

### Phase 1: Project Setup & Basic Python Functions
- [x] Initialize project with UV
- [x] Add dependencies (mcp, yt-dlp, google-api-python-client, python-dotenv)
- [x] Setup project structure and environment configuration
- [x] Create YouTube API client with GCP API key authentication
- [x] Implement 3 core functions for captions, topics, and playlist extraction
- [x] Create test script to validate all functions work independently

### Phase 2: MCP Server Implementation ✓
- [x] Create MCP server using FastMCP from python-sdk
- [x] Configure pyproject.toml with proper entry points
- [x] Wrap functions as MCP tools
- [x] Add proper error handling and validation
- [x] Add logging and debug capabilities
- [x] Test MCP server locally

### Phase 3: Claude Desktop Integration & Testing
- [ ] Configure Claude Desktop for local MCP server
- [ ] Test MCP server with Claude Desktop integration
- [ ] Test various scenarios (public/private videos, different languages, playlist sizes)
- [ ] Create documentation for setup and usage

## Project Structure

```
Youtube MCP/
├── src/
│   └── youtube_mcp/
│       ├── __init__.py        # Clean package exports
│       ├── server.py          # FastMCP server with 3 tools
│       ├── youtube_client.py  # YouTube API wrapper
│       └── utils.py           # Helper functions
├── tests/
│   └── test_functions.py      # Comprehensive function tests
├── .env                       # Environment variables (API keys)
├── .gitignore                 # Git ignore patterns
├── CLAUDE.md                  # Project instructions for Claude
├── PROJECT_LOG.md             # Detailed development progress log
├── Learnings.md               # Development learnings and notes
├── README.md                  # User documentation
├── pyproject.toml             # UV/Python project configuration
└── uv.lock                    # Auto-generated lock file
```

## Commands

### Development Setup
```bash
# Initialize project
uv init youtube-mcp && cd youtube-mcp

# Add dependencies
uv add mcp yt-dlp google-api-python-client python-dotenv
uv add --dev pytest black ruff

# Run tests
uv run python tests/test_functions.py

# Run MCP server locally
uv run python -m youtube_mcp.server
```

### Testing and Validation
```bash
# Run all tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .
```

## Dependencies

### Core Dependencies
- `mcp>=1.4.0` - MCP Python SDK
- `yt-dlp` - Video/caption extraction
- `google-api-python-client` - YouTube Data API v3
- `python-dotenv` - Environment variable management

### Development Dependencies
- `pytest` - Testing framework
- `black` - Code formatting
- `ruff` - Fast Python linter

## Architecture

### Core Functions
1. **`get_video_captions(video_url, language_preference=None)`**
   - Uses yt-dlp to extract captions/subtitles
   - Supports multiple languages including auto-generated captions
   - Returns structured caption data

2. **`get_video_topics(video_url)`**
   - Uses YouTube Data API v3 to get video metadata
   - Extracts topics/sections from video descriptions
   - Parses structured description content

3. **`get_playlist_titles(playlist_url)`**
   - Uses YouTube Data API v3 to fetch playlist items
   - Handles pagination for large playlists
   - Returns list of video titles and metadata

### MCP Tools
- **`extract_youtube_captions`** - Input: video_url, language_preference
- **`extract_video_topics`** - Input: video_url  
- **`extract_playlist_titles`** - Input: playlist_url

### Error Handling
- Private video detection
- API quota management
- Invalid URL validation
- Network error resilience

## Environment Setup

### Required Environment Variables
```bash
# YouTube Data API v3 key from Google Cloud Platform
YOUTUBE_API_KEY=your_api_key_here

# Optional: Default language preference for captions
DEFAULT_CAPTION_LANGUAGE=en
```

### Claude Desktop Configuration
For local development, add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "youtube-mcp": {
      "command": "uv",
      "args": [
        "--directory", 
        "/absolute/path/to/youtube-mcp",
        "run",
        "python",
        "-m",
        "youtube_mcp.server"
      ]
    }
  }
}
```

## Distribution Options (Decision Pending)

### Option A: Keep Local
- Use absolute path configuration in Claude Desktop
- Share as Git repository
- Users clone and configure their own paths

### Option B: Publish to PyPI
- Package and publish with `uv build` & `uv publish`
- Users install with `uvx youtube-mcp`
- Simple Claude Desktop config

### Option C: Hybrid Approach
- Develop locally with absolute paths
- Publish for easy sharing later
- Support both installation methods