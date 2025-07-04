# YouTube MCP Server

A Model Context Protocol (MCP) server for YouTube operations that provides tools to extract captions, topics, and playlist information from YouTube videos.

## Features

- **Extract YouTube Captions**: Retrieve captions/subtitles from YouTube videos with multi-language support
- **Extract Video Topics**: Parse video descriptions to extract topics, sections, and timestamps  
- **Extract Playlist Titles**: Get titles and metadata from all videos in a YouTube playlist

## Requirements

- Python 3.11 or higher
- YouTube Data API v3 key from Google Cloud Platform
- UV package manager (recommended)
- Claude Desktop (for MCP integration)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Youtube MCP"
```

### 2. Install Dependencies with UV

```bash
uv sync
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### Getting a YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API Key)
5. Copy the API key to your `.env` file

## Claude Desktop Configuration

### 1. Locate Claude Desktop Config

The config file is located at:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

### 2. Add MCP Server Configuration

Add the following to your Claude Desktop config:

```json
{
  "mcpServers": {
    "youtube-mcp": {
      "command": "/Users/yourusername/.local/bin/uv",
      "args": [
        "--directory",
        "/absolute/path/to/Youtube MCP",
        "run",
        "python",
        "-m",
        "youtube_mcp.server"
      ]
    }
  }
}
```

**Important Notes:**
- Replace `/Users/yourusername/.local/bin/uv` with your actual uv path (find with `which uv`)
- Replace `/absolute/path/to/Youtube MCP` with the full path to your project
- Use absolute paths only - relative paths will not work

### 3. Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

## Usage

### Testing the Installation

First, test the core functions independently:

```bash
uv run python tests/test_functions.py
```

### Using with Claude Desktop

Once configured, you can use the YouTube MCP tools directly in Claude Desktop conversations:

#### Extract YouTube Captions

```
Extract captions from https://www.youtube.com/watch?v=VIDEO_ID in Spanish
```

**Parameters:**
- `video_url`: YouTube video URL (required)
- `language_preference`: Language code like 'en', 'es', 'fr' (optional, defaults to 'en')

#### Extract Video Topics

```
Extract topics and timestamps from https://www.youtube.com/watch?v=VIDEO_ID
```

**Parameters:**
- `video_url`: YouTube video URL (required)

#### Extract Playlist Titles

```
Get all video titles from https://www.youtube.com/playlist?list=PLAYLIST_ID
```

**Parameters:**
- `playlist_url`: YouTube playlist URL (required)

## Supported URL Formats

The server accepts various YouTube URL formats:

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/playlist?list=PLAYLIST_ID`
- URLs with additional parameters (e.g., `&si=...`, `&t=...`)

## Error Handling

The server gracefully handles:

- ❌ Invalid YouTube URLs
- ❌ Private or unavailable videos  
- ❌ Videos without captions
- ❌ API quota limits
- ❌ Network connectivity issues
- ❌ Malformed playlist URLs

All errors return structured responses with helpful error messages.

## Project Structure

```
Youtube MCP/
├── src/
│   └── youtube_mcp/
│       ├── __init__.py        # Package exports
│       ├── server.py          # FastMCP server with 3 tools
│       ├── youtube_client.py  # YouTube API wrapper
│       └── utils.py           # Helper functions
├── tests/
│   └── test_functions.py      # Comprehensive function tests
├── .env                       # Environment variables (API keys)
├── .gitignore                 # Git ignore patterns
├── CLAUDE.md                  # Project instructions for Claude
├── PROJECT_LOG.md             # Development progress log
├── README.md                  # This file
├── pyproject.toml             # UV/Python project configuration
└── uv.lock                    # Auto-generated lock file
```

## Development

### Running Tests

```bash
# Test core functions
uv run python tests/test_functions.py

# Run pytest (if available)
uv run pytest
```

### Code Quality

```bash
# Format code
uv run black .

# Lint code  
uv run ruff check .
```

### Manual Server Testing

You can run the MCP server standalone for testing:

```bash
uv run python -m youtube_mcp.server
```

## Troubleshooting

### Common Issues

**1. "spawn uv ENOENT" Error**
- Use absolute path to uv in Claude Desktop config
- Find uv path with: `which uv`

**2. JSON Parsing Errors**
- Ensure no print statements in server code
- All output to stdout must be valid JSON

**3. "YOUTUBE_API_KEY environment variable is required"**
- Check `.env` file exists and has correct API key
- Verify API key is valid in Google Cloud Console

**4. Server Not Responding**
- Restart Claude Desktop completely
- Check MCP server logs in Claude Desktop settings

### Viewing Logs

Claude Desktop logs are available in:
- **macOS**: Claude Desktop Settings → Developer → View Logs
- Look for `[youtube-mcp]` entries

## API Limits

YouTube Data API v3 has quotas:
- Default: 10,000 units per day
- Video metadata: ~1-5 units per request
- Playlist items: ~1 unit per 50 videos

Monitor usage in [Google Cloud Console](https://console.cloud.google.com/).

## Technical Details

- **MCP Protocol**: Uses stdio transport for Claude Desktop integration
- **FastMCP**: Built with FastMCP framework for robust MCP server functionality
- **yt-dlp**: Powers caption extraction with multi-language support
- **YouTube API v3**: Handles video metadata and playlist operations
- **Error Handling**: Multi-layered approach with structured error responses

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `uv sync`
4. Make changes and test thoroughly
5. Run code quality checks: `uv run black .` and `uv run ruff check .`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) for the excellent MCP framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for reliable YouTube caption extraction
- [Model Context Protocol](https://modelcontextprotocol.io/) for the standardized AI tool integration