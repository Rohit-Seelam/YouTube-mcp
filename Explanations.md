# Client file Explanation

⏺ Perfect! Let me explain each detail with concrete examples.

## 1. with tempfile.TemporaryDirectory() as temp_dir:

**What it does:**
```python
# Creates a temporary folder like: /tmp/tmp_abc123xyz/
# Assigns the path to temp_dir variable
# When the 'with' block exits, AUTOMATICALLY deletes the entire folder
```

**Example:**
```python
import tempfile
import os

with tempfile.TemporaryDirectory() as temp_dir:
    print(f"Temp folder created: {temp_dir}")
    # temp_dir might be: "/tmp/tmp_k8j2n9x1/"

    # Create a file inside
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, 'w') as f:
        f.write("Hello")

    print(f"File exists: {os.path.exists(test_file)}")  # True

# When we exit the 'with' block, the folder and ALL files inside are deleted
print(f"Folder exists: {os.path.exists(temp_dir)}")  # False
```

## 2. Exact Location of Downloaded Subtitles

**Line 41:** `'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s')`

**Example:**
- temp_dir = /tmp/tmp_abc123/
- Video title = "How I'd Learn AI in 2025"
- Language = "en"
- Final file path: /tmp/tmp_abc123/How I'd Learn AI in 2025.en.srt

**The path construction:**
```python
# temp_dir = "/tmp/tmp_abc123/"
# os.path.join(temp_dir, '%(title)s.%(ext)s') becomes:
# "/tmp/tmp_abc123/%(title)s.%(ext)s"

# yt-dlp replaces:
# %(title)s → "How I'd Learn AI in 2025"
# %(ext)s → "en.srt"
# Final: "/tmp/tmp_abc123/How I'd Learn AI in 2025.en.srt"
```

## 3. Language Selection Logic (lines 64-70)

```python
target_lang = language_preference or 'en'  # User wants "en"
all_captions = {
    'en': [...],           # English
    'en-US': [...],        # English (US)
    'es': [...],           # Spanish
    'fr': [...]            # French
}

# Step 1: Exact match
if target_lang in all_captions:          # if "en" in dict
    chosen_lang = target_lang            # chosen_lang = "en" ✓

# Step 2: Partial match (if exact fails)
elif any(lang.startswith(target_lang) for lang in all_captions):
    # Checks: does "en-US".startswith("en")? → True
    chosen_lang = next(lang for lang in all_captions if lang.startswith(target_lang))
    # chosen_lang = "en-US"

# Step 3: Fallback (if nothing matches)
else:
    chosen_lang = list(all_captions.keys())[0]  # First available language
    # chosen_lang = "en" (whatever comes first)
```

**Real example:**
```python
# User wants "en", available: ["en-GB", "es", "fr"]
target_lang = "en"

# Step 1: "en" in ["en-GB", "es", "fr"]? → False
# Step 2: Does any start with "en"? "en-GB".startswith("en") → True
# Result: chosen_lang = "en-GB"
```

## 4. with yt_dlp.YoutubeDL(ydl_opts) as ydl:

**What it does:**
```python
# Similar to file opening, but for yt-dlp objects
# Creates a yt-dlp downloader instance
# Automatically cleans up resources when done
```

**Equivalent without 'with':**
```python
# Without 'with' (manual cleanup)
ydl = yt_dlp.YoutubeDL(ydl_opts)
try:
    info = ydl.extract_info(url, download=False)
finally:
    ydl.close()  # Manual cleanup

# With 'with' (automatic cleanup)
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)
    # Automatically calls ydl.close() when exiting
```

## 5. Automatic File Deletion (No Manual Code Needed!)

The magic is in the `with tempfile.TemporaryDirectory()`:

```python
def get_video_captions(self, ...):
    with tempfile.TemporaryDirectory() as temp_dir:  # Creates temp folder
        # ... download subtitles to temp_dir ...

        # Read the subtitle file
        with open(subtitle_files[0], 'r') as f:
            caption_text = f.read()

        return {
            'captions': caption_text,
            # ...
        }
    # ← HERE: Python automatically deletes temp_dir and ALL files inside

    # No manual deletion needed!
```

**Timeline:**
1. Function starts → Temp folder created: /tmp/tmp_abc123/
2. yt-dlp downloads → File created: /tmp/tmp_abc123/video.en.srt
3. We read the file → Caption text extracted
4. Function ends → Python automatically deletes /tmp/tmp_abc123/ and everything inside

## 6. lang_base = chosen_lang.split('-')[0]

**Purpose:** Handle language codes with country variants

**Examples:**
```python
# Example 1: Full language code
chosen_lang = "en-US"
lang_base = chosen_lang.split('-')[0]  # "en"

# Example 2: Simple language code  
chosen_lang = "fr"
lang_base = chosen_lang.split('-')[0]  # "fr"

# Example 3: Multiple parts
chosen_lang = "zh-Hans-CN"
lang_base = chosen_lang.split('-')[0]  # "zh"
```

**Why we need this (lines 82-86):**
```python
# First try: Look for exact language file
subtitle_files = glob.glob(os.path.join(temp_dir, f'*.{chosen_lang}.srt'))
# Looking for: "video.en-US.srt"

if not subtitle_files:
    # Maybe yt-dlp saved it as just "en" instead of "en-US"
    lang_base = chosen_lang.split('-')[0]  # "en-US" → "en"
    subtitle_files = glob.glob(os.path.join(temp_dir, f'*.{lang_base}.srt'))
    # Now looking for: "video.en.srt"
```

**Real scenario:**
- User requests: language_preference = "en-US"
- yt-dlp might save file as: video.en.srt (without country code)
- First search fails: *.en-US.srt → Nothing found
- Fallback search succeeds: *.en.srt → File found!

This makes our code robust to yt-dlp's file naming variations.

---

# Server file Explanation

⏺ I'll give you a comprehensive, line-by-line explanation of server.py as if you're completely new to programming and MCP (Model Context Protocol).

## Complete Breakdown of server.py

### File Header & Documentation (Lines 1-2)

```python
"""YouTube MCP Server - Model Context Protocol server for YouTube operations."""
```
- **What it is:** This is a "docstring" - a description of what this file does
- **Purpose:** Tells anyone reading the code that this file creates an MCP server specifically for YouTube operations
- **MCP Explained:** Think of MCP as a way for AI assistants (like Claude) to use external tools. This file creates those tools.

### Import Statements (Lines 3-11)

These lines bring in external code libraries that our program needs:

```python
import logging
import os
from typing import Any
```
- **logging:** Built-in Python library for recording what happens when the program runs (like a diary)
- **os:** Built-in Python library for interacting with the operating system (reading environment variables, file paths, etc.)
- **typing import Any:** Helps with type hints - tells Python what kind of data to expect

```python
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
```
- **dotenv:** External library that reads .env files (where we store secret API keys)
- **FastMCP:** The main framework that makes it easy to create MCP servers

```python
from .utils import is_valid_youtube_url
from .youtube_client import YouTubeClient
```
- **.utils:** Our own helper functions (the dot means "from this same package")
- **.youtube_client:** Our own class that handles YouTube API calls

### Environment Setup (Lines 13-14)

```python
# Load environment variables
load_dotenv()
```
- **What it does:** Reads the .env file and loads any variables (like API keys) into the program
- **Why needed:** We store sensitive information like YouTube API keys in .env files instead of hard-coding them

### Logging Configuration (Lines 16-27)

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
```
- **What it does:** Sets up a logging system to track what happens when the program runs
- **level=logging.INFO:** Only log important events and errors (not every tiny detail)
- **format=...:** How log messages should look (timestamp, file name, severity level, actual message)
- **handlers=[logging.StreamHandler()]:** Send log messages to the console/terminal. StreamHandler() ensures you can see the logs in your terminal/console. it makes your logs visible in the terminal where you run the server
- **logger = logging.getLogger(__name__):** Create a logger specifically for this file

```python
if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")
```
- **What it does:** If someone sets DEBUG=true in their environment, show much more detailed logs
- **os.getenv("DEBUG", ""):** Look for a "DEBUG" environment variable, return empty string if not found
- **.lower() in ("true", "1", "yes"):** Check if the value means "yes" in various formats

### Server Initialization (Lines 29-33)

```python
# Initialize FastMCP server
mcp = FastMCP("YouTube MCP")

# Initialize YouTube client
youtube_client = None
```
- **mcp = FastMCP("YouTube MCP"):** Create the main MCP server with name "YouTube MCP"
- **youtube_client = None:** Start with no YouTube client - we'll create it later when needed (lazy loading)

### Client Management Function (Lines 36-47)

```python
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
```
- **Purpose:** This is called the "Singleton Pattern" - ensures we only create one YouTube client
- **global youtube_client:** Tells Python we want to modify the global variable, not create a local one
- **if youtube_client is None::** Only create the client if we haven't already
- **try/except:** If creating the client fails, log the error and stop the program
- **raise:** Re-throw the exception so the calling code knows something went wrong

### First MCP Tool: Extract Captions (Lines 50-88)

```python
@mcp.tool()
def extract_youtube_captions(video_url: str, language_preference: str = "en") -> dict[str, Any]:
```
- **@mcp.tool():** This "decorator" tells FastMCP "make this function available as an MCP tool"
- **Function parameters:**
  - **video_url: str** - Must be a string (text)
  - **language_preference: str = "en"** - Optional parameter, defaults to English
- **-> dict[str, Any]:** Returns a dictionary (key-value pairs) with string keys and any type of values

```python
    """Extract captions/subtitles from a YouTube video.
    
    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
        language_preference: Preferred language code (e.g., 'en', 'es', 'fr'). Defaults to 'en'.
    
    Returns:
        Dictionary containing video information and captions data.
    """
```
- **Docstring:** Documents what the function does - this becomes the tool description in MCP

**Function Body Breakdown:**
```python
logger.info(f"extract_youtube_captions called with URL: {video_url}, language: {language_preference}")
```
- **Log the function call:** Record when someone uses this tool and with what parameters

```python
try:
    if not is_valid_youtube_url(video_url):
        logger.warning(f"Invalid YouTube URL provided: {video_url}")
        return {
            "error": "Invalid YouTube URL provided",
            "message": "Please provide a valid YouTube video URL",
        }
```
- **Input validation:** Check if the URL is actually a YouTube URL
- **Error handling:** If invalid, return an error dictionary instead of crashing

```python
    client = get_youtube_client()
    logger.debug(f"Extracting captions for video: {video_url}")
    result = client.get_video_captions(video_url, language_preference)
```
- **Get the client:** Use our singleton function to get the YouTube client
- **Do the work:** Call the actual caption extraction method
- **Debug logging:** Record what we're doing (only shows if DEBUG is enabled)

```python
    if "error" in result:
        logger.error(f"Caption extraction failed: {result.get('error', 'Unknown error')}")
    else:
        logger.info(f"Successfully extracted captions for video: {result.get('video_title', 'Unknown')}")

    return result
```
- **Check the result:** See if the extraction worked or failed
- **Log appropriately:** Error log if failed, success log if worked
- **Return the result:** Give back whatever the YouTube client returned

```python
except Exception as e:
    logger.error(f"Exception in extract_youtube_captions: {e!s}")
    return {"error": str(e), "message": "Failed to extract captions from YouTube video"}
```
- **Catch any unexpected errors:** If anything goes wrong that we didn't plan for
- **{e!s}:** Convert the exception to a string for logging
- **Return error:** Instead of crashing, return a friendly error message

### Second MCP Tool: Extract Topics (Lines 91-127)

This follows the exact same pattern as the captions tool:
1. Log the function call
2. Validate the URL
3. Get the YouTube client
4. Do the work (extract topics from video description)
5. Log success/failure
6. Return the result
7. Handle any unexpected errors

**The only differences:**
- Calls `client.get_video_topics()` instead of captions
- Logs the number of topics found
- No language preference parameter

### Third MCP Tool: Extract Playlist (Lines 130-174)

Same pattern again, but with an extra validation:
```python
if "list=" not in playlist_url:
    logger.warning(f"URL does not contain playlist parameter: {playlist_url}")
    return {
        "error": "Invalid playlist URL",
        "message": "URL does not appear to be a YouTube playlist",
    }
```
- **Extra check:** Make sure the URL actually contains "list=" (indicating it's a playlist URL)
- **Playlist-specific logging:** Logs playlist title and video count on success

### Main Server Function (Lines 177-211)

```python
def main():
    """Main entry point for the MCP server."""
    logger.info("YouTube MCP Server main() called")
```
- **Entry point:** This function starts everything up
- **Log startup:** Record that the server is starting

```python
    # Check for API key
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logger.error("YOUTUBE_API_KEY environment variable is required")
        print("Error: YOUTUBE_API_KEY environment variable is required")
        print("Please set your YouTube Data API v3 key from Google Cloud Platform")
        return
```
- **Critical check:** Make sure the YouTube API key is set
- **User-friendly error:** If no API key, explain what's needed and stop

```python
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
```
- **Startup sequence:** Test that everything works before starting the server
- **User feedback:** Show what tools are available

```python
        # Run the FastMCP server
        logger.info("Starting FastMCP server with stdio transport")
        mcp.run(transport="stdio")
        logger.info("FastMCP server started successfully")
```
- **Start the server:** `mcp.run(transport="stdio")` starts the MCP server
- **stdio transport:** Means the server communicates through standard input/output (good for Claude Desktop)

```python
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"Error starting server: {e}")
        return
```
- **Handle startup errors:** If anything goes wrong during startup, log it and exit gracefully

### Script Execution (Lines 214-215)

```python
if __name__ == "__main__":
    main()
```
- **Python idiom:** This runs main() only if the file is executed directly (not imported)
- **Why needed:** Allows the file to be both a module (importable) and a script (runnable)

## Key Concepts Summary:

1. **MCP Tools:** Functions decorated with `@mcp.tool()` become available to AI assistants
2. **Error Handling:** Always return error dictionaries instead of crashing
3. **Logging:** Track everything that happens for debugging
4. **Singleton Pattern:** Only create one YouTube client instance
5. **Input Validation:** Always check if inputs are valid before processing
6. **Environment Variables:** Store sensitive data like API keys separately
7. **Graceful Degradation:** Handle errors in a user-friendly way

This server acts as a bridge between Claude (or other AI assistants) and YouTube's APIs, providing three specific tools for extracting different types of information from YouTube content.

---

# MCP Server Architecture & Communication Deep Dive

## 1. Server Execution Model: How, Where, and When Your MCP Server Runs

### Where Is the Server Running?

Your MCP server runs as a **child process** of Claude Desktop on your local machine. Here's the execution flow:

```
Your Machine
├── Claude Desktop (Parent Process)
│   ├── Claude Desktop UI (Frontend)
│   ├── MCP Client (Built into Claude Desktop)
│   └── Child Processes:
│       ├── youtube-mcp server ← YOUR SERVER RUNS HERE
│       ├── exa-mcp server
│       ├── context7-mcp server
│       └── perplexity-mcp server
```

**Physical Location**: Your server runs in a Python process on your local machine, NOT in the cloud.

### How Does the Server Start?

When Claude Desktop launches, it reads `claude_desktop_config.json` and executes this command:

```bash
/Users/rohitseelam/.local/bin/uv --directory "/Users/rohitseelam/Projects/Youtube MCP" run python -m youtube_mcp.server
```

**Step-by-step execution:**
1. **Claude Desktop reads config** → Finds "youtube-mcp" entry
2. **Spawns child process** → Runs the UV command above
3. **UV activates project** → Sets up virtual environment and dependencies
4. **Python executes** → `python -m youtube_mcp.server` 
5. **Your main() function runs** → Server starts and connects to Claude Desktop
6. **stdio pipes established** → Communication channel created

### How Long Will the Server Run?

Your MCP server runs for the **entire duration that Claude Desktop is open**:

```
Timeline:
📱 Claude Desktop starts → 🚀 MCP servers start → 💬 Chat sessions → 🔄 Server stays alive → 📱 Claude Desktop quits → 💀 All MCP servers terminate
```

**Key Points:**
- **Persistent**: Server stays running between conversations
- **Session-independent**: Same server instance handles multiple chats
- **Automatic lifecycle**: You don't manually start/stop it
- **Graceful shutdown**: When Claude Desktop quits, all child processes are terminated

### Server State Management

```python
# Your server maintains state across requests:
youtube_client = None  # Global variable persists

def get_youtube_client():
    global youtube_client
    if youtube_client is None:  # Only create once
        youtube_client = YouTubeClient()  # Stays alive for all requests
    return youtube_client
```

**What this means:**
- **First tool call**: Creates YouTube client, authenticates with API
- **Subsequent calls**: Reuses same client (faster, efficient)
- **Memory persistence**: Variables stay in memory until Claude Desktop closes

## 2. Standard Input/Output (stdin/stdout) Deep Dive

### What Exactly Is stdout?

**stdout** (Standard Output) is one of three default communication channels every program has:

```
Every Program Has:
├── stdin  (Standard Input)  ← Receives data
├── stdout (Standard Output) ← Sends main output  
└── stderr (Standard Error)  ← Sends error messages
```

**Think of it like plumbing:**
- **stdin** = Water coming IN to your house
- **stdout** = Main water going OUT (to garden/usage)
- **stderr** = Sewage going OUT (separate drain for problems)

### How stdout Works in MCP

In your MCP server:

```python
# ❌ WRONG - Breaks MCP protocol:
print("Starting server...")  # Goes to stdout - Claude Desktop tries to parse as JSON

# ✅ CORRECT - Respects MCP protocol:
logger.info("Starting server...")  # Goes to stderr - Claude Desktop ignores
```

**Why This Matters:**

```
MCP Protocol Rules:
stdout = ONLY JSON-RPC messages
stderr = Logs, debugging, human-readable text
```

**Visual Flow:**
```
[Claude Desktop] ←--JSON-RPC--→ [Your MCP Server]
                     stdout           stdout
                 
[Claude Desktop Logs] ←--Text--→ [Your MCP Server]
                         stderr          stderr
```

### The stdout Contamination Problem We Fixed

**What was happening:**
```python
# In your main() function:
print("YouTube MCP Server starting...")     # ❌ Plain text to stdout
print("Available tools:")                   # ❌ Plain text to stdout
mcp.run(transport="stdio")                  # ✅ JSON to stdout
```

**Claude Desktop received:**
```
YouTube MCP Server starting...              ← Tried to parse as JSON → ERROR
Available tools:                            ← Tried to parse as JSON → ERROR
{"jsonrpc": "2.0", "method": "initialize"}  ← Valid JSON → SUCCESS
```

**After our fix:**
```python
# Now only JSON goes to stdout:
logger.info("YouTube MCP Server starting...")  # → stderr (safe)
logger.info("Available tools:")                # → stderr (safe)
mcp.run(transport="stdio")                     # → stdout (JSON only)
```

## 3. MCP Protocol Data Flow & Metadata

### Data Types Transferred Between Claude Desktop and Your Server

The communication uses **JSON-RPC 2.0** protocol with specific message types:

#### A. Client → Server Messages

**1. Initialization:**
```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "claude-ai",
      "version": "0.1.0"
    }
  }
}
```

**2. Tool Discovery:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**3. Tool Execution:**
```json
{
  "jsonrpc": "2.0",
  "id": 21,
  "method": "tools/call",
  "params": {
    "name": "extract_youtube_captions",
    "arguments": {
      "video_url": "https://youtu.be/eiKkZNmaJYk",
      "language_preference": "en"
    }
  }
}
```

#### B. Server → Client Messages

**1. Initialization Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "experimental": {},
      "prompts": {"listChanged": false},
      "resources": {"subscribe": false, "listChanged": false},
      "tools": {"listChanged": false}
    },
    "serverInfo": {
      "name": "YouTube MCP",
      "version": "1.9.4"
    }
  }
}
```

**2. Tool List Response (Metadata for Each Tool):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "extract_youtube_captions",
        "description": "Extract captions/subtitles from a YouTube video.\n\nArgs:\n  video_url: YouTube video URL\n  language_preference: Language code (optional)\n\nReturns:\n  Dictionary with video info and captions",
        "inputSchema": {
          "type": "object",
          "properties": {
            "video_url": {
              "type": "string",
              "title": "Video Url"
            },
            "language_preference": {
              "type": "string",
              "title": "Language Preference",
              "default": "en"
            }
          },
          "required": ["video_url"],
          "title": "extract_youtube_captionsArguments"
        }
      }
    ]
  }
}
```

### Tool Metadata Breakdown

**Yes, there is metadata for each tool!** Claude Desktop receives:

1. **Tool Name**: `"extract_youtube_captions"`
2. **Description**: Your function's docstring
3. **Input Schema**: Automatically generated from your function signature
   - Parameter types (`string`, `integer`, etc.)
   - Required vs optional parameters
   - Default values
   - Parameter descriptions

**How FastMCP Generates This:**
```python
@mcp.tool()
def extract_youtube_captions(video_url: str, language_preference: str = "en") -> dict[str, Any]:
    """Extract captions/subtitles from a YouTube video.
    
    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
        language_preference: Preferred language code (e.g., 'en', 'es', 'fr'). Defaults to 'en'.
    
    Returns:
        Dictionary containing video information and captions data.
    """
```

**FastMCP automatically creates:**
- `name`: From function name
- `description`: From docstring
- `inputSchema`: From type hints (`str`, `str = "en"`)
- `required`: From parameters without defaults (`video_url`)
- `optional`: From parameters with defaults (`language_preference`)

## 4. Visual Communication Flow

### Complete MCP Communication Lifecycle

```
┌─────────────────┐    1. Config Read     ┌─────────────────┐
│   Claude        │ ──────────────────→   │   Your MCP      │
│   Desktop       │                       │   Server        │
│                 │    2. Process Spawn   │                 │
│                 │ ──────────────────→   │                 │
│                 │                       │                 │
│                 │    3. Initialize      │                 │
│                 │ ──────────────────→   │                 │
│                 │ ←─────────────────    │   (main() runs) │
│                 │    4. Tools/List      │                 │
│                 │                       │                 │
│  ┌─────────────┐│    5. Tool Call       │┌─────────────┐  │
│  │Claude Thinks││ ──────────────────→   ││Tool Function│  │
│  │"I need      ││                       ││Executes     │  │
│  │ captions"   ││ ←─────────────────    ││& Returns    │  │
│  └─────────────┘│    6. Tool Result     │└─────────────┘  │
│                 │                       │                 │
│                 │    7. More calls...   │                 │
│                 │ ←────────────────→    │                 │
│                 │                       │                 │
│                 │    8. Claude Quits    │                 │
│                 │ ──────────────────→   │   Process Dies  │
└─────────────────┘                       └─────────────────┘
```

### Data Flow Example: Caption Extraction

```
1. User types: "Extract captions from https://youtu.be/VIDEO_ID"

2. Claude Desktop thinks: "I need to call extract_youtube_captions tool"

3. JSON-RPC Message (Claude → Your Server):
   {
     "method": "tools/call",
     "params": {
       "name": "extract_youtube_captions", 
       "arguments": {"video_url": "https://youtu.be/VIDEO_ID"}
     }
   }

4. Your Server Processes:
   ├── Validates URL
   ├── Gets YouTube client
   ├── Calls yt-dlp
   ├── Downloads captions
   └── Returns structured data

5. JSON-RPC Response (Your Server → Claude):
   {
     "result": {
       "video_id": "VIDEO_ID",
       "video_title": "Amazing Video",
       "captions": "Hello, welcome to this video...",
       "language_used": "en",
       "caption_type": "manual"
     }
   }

6. Claude Desktop receives data and shows user the captions
```

### Server Lifecycle in Detail

```
Phase 1: Startup (When Claude Desktop Opens)
┌─────────────────────────────────────────────────────────┐
│ 1. Claude Desktop reads claude_desktop_config.json     │
│ 2. Spawns: uv run python -m youtube_mcp.server        │
│ 3. Your main() function executes                       │
│ 4. Environment variables loaded (.env)                 │
│ 5. FastMCP server initializes                          │
│ 6. YouTube client prepared (but not created yet)       │
│ 7. Server sends "initialize" response to Claude        │
│ 8. Claude Desktop marks server as "ready"              │
└─────────────────────────────────────────────────────────┘

Phase 2: Operation (During Conversations)
┌─────────────────────────────────────────────────────────┐
│ • Server stays alive in background                     │
│ • Responds to tool/list requests (sends metadata)      │
│ • Responds to tool/call requests (executes functions)  │
│ • Maintains state (YouTube client instance)            │
│ • Logs everything to stderr                            │
└─────────────────────────────────────────────────────────┘

Phase 3: Shutdown (When Claude Desktop Closes)
┌─────────────────────────────────────────────────────────┐
│ 1. Claude Desktop sends termination signal             │
│ 2. Your Python process receives signal                 │
│ 3. Python cleanup happens automatically                │
│ 4. YouTube client connections close                    │
│ 5. Process terminates                                  │
└─────────────────────────────────────────────────────────┘
```

## Key Insights Summary

1. **Server Location**: Runs as child process on your local machine, not in cloud
2. **Server Lifetime**: Starts with Claude Desktop, ends when it closes
3. **stdout Protocol**: Must be pure JSON-RPC, no plain text allowed
4. **Tool Metadata**: Automatically generated from your function signatures and docstrings
5. **State Persistence**: Your server remembers things between tool calls
6. **Communication**: Bidirectional JSON-RPC over stdin/stdout pipes

This architecture makes MCP servers very efficient - they start once, stay ready, and handle multiple requests without restart overhead.