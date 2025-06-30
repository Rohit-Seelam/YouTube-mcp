# YouTube MCP Project Log

## Project Overview

This is a YouTube MCP (Model Context Protocol) server that provides three main tools for extracting information from YouTube videos and playlists:

1. **Extract YouTube Captions** - Retrieve captions/subtitles from YouTube videos (multi-language support)
2. **Extract Video Topics** - Extract topics/sections from YouTube video descriptions 
3. **Extract Playlist Titles** - Get titles and metadata from all videos in a YouTube playlist

**Current Status**: Phase 2 Complete - MCP Server Implementation ✅  
**Next Phase**: Phase 3 - Claude Desktop Integration & Testing

## Phase Completion Log

### Phase 0: Project Documentation ✅ (Completed)
- **Objective**: Establish comprehensive project plan and documentation
- **Key Deliverables**:
  - Updated CLAUDE.md with complete project roadmap
  - Defined 3-phase development approach
  - Established project structure and dependencies

### Phase 1: Project Setup & Basic Python Functions ✅ (Completed)
- **Objective**: Set up project foundation and implement core YouTube functionality
- **Key Deliverables**:
  - Initialized UV-based Python project
  - Added core dependencies (mcp, yt-dlp, google-api-python-client, python-dotenv)
  - Created YouTube API client with GCP authentication
  - Implemented 3 core functions for captions, topics, and playlist extraction
  - Created comprehensive test script for function validation

### Phase 2: MCP Server Implementation ✅ (Just Completed)
- **Objective**: Wrap functions as MCP tools and create functional server
- **Key Achievements**:
  - ✅ Created FastMCP server with proper configuration
  - ✅ Wrapped all 3 functions as MCP tools with @mcp.tool() decorators
  - ✅ Configured pyproject.toml with correct entry points
  - ✅ Added comprehensive logging and debug capabilities
  - ✅ Implemented robust error handling and input validation
  - ✅ Successfully tested server startup and functionality

## Critical Issues Encountered & Resolutions

### Issue 1: RuntimeWarning on Server Startup
**Problem**: `'youtube_mcp.server' found in sys.modules after import of package 'youtube_mcp', but prior to execution`

**Root Cause**: Circular import in `__init__.py` - importing `main` from `server.py` caused module to load prematurely

**Solution**: Removed `from .server import main` from `__init__.py`, keeping only essential exports

**MCP Used**: Perplexity MCP for research on Python import warnings

### Issue 2: Duplicate FastMCP Initialization Logs
**Problem**: Server initialization messages appeared twice in logs

**Root Cause**: FastMCP server was being initialized both at module level and during function execution

**Solution**: Removed redundant initialization logging, consolidated to single initialization message in main()

### Issue 3: Google API Cache Discovery Warning
**Problem**: `file_cache is only supported with oauth2client<4.0.0` warning on every API call

**Root Cause**: google-api-python-client trying to use deprecated caching mechanism

**Solution**: Added `cache_discovery=False` parameter to `build()` call in YouTubeClient

## Technical Decisions & Architecture

### FastMCP Framework Choice
- **Decision**: Use FastMCP from MCP Python SDK
- **Rationale**: Official framework with excellent documentation and active development
- **Alternative Considered**: Building custom MCP server from scratch

### Error Handling Strategy
- **Approach**: Multi-layered error handling
  - Input validation at tool level
  - API error handling in client classes
  - Exception logging with detailed context
- **Benefit**: Robust error reporting for debugging and user feedback

### Logging Architecture
- **Implementation**: Python's built-in logging with structured format
- **Features**: 
  - INFO level for operation tracking
  - DEBUG level for detailed troubleshooting (controlled by DEBUG env var)
  - ERROR level for failures with context
- **Tool Integration**: Logs available for MCP debugging and monitoring

### Project Structure Decisions
- **Module Organization**: Separated concerns into distinct files
  - `server.py`: MCP server and tool definitions
  - `youtube_client.py`: YouTube API integration
  - `utils.py`: Helper functions for URL parsing and text processing
- **Configuration**: Environment-based configuration with .env support
- **Testing**: Separate test suite for function validation

## Code Quality & Standards

### Formatting & Linting
- **Tools Used**: Black (formatting) + Ruff (linting)
- **Standards Applied**: 
  - Modern Python type hints (dict instead of Dict)
  - Proper import organization
  - 100-character line length
- **Acceptable Deviations**: 
  - F-string logging (acceptable for MCP server context)
  - Global variable usage for client singleton (intentional pattern)

### Type Safety
- **Approach**: Modern Python typing with union syntax (str | None vs Optional[str])
- **Coverage**: Full type hints for all public functions and methods

## Current Capabilities

### Working Features
1. **Caption Extraction**: 
   - Multi-language support with fallback logic
   - Auto-generated and manual caption detection
   - Clean text output with timestamp/formatting removal

2. **Topic Extraction**:
   - Regex-based timestamp pattern detection
   - Fallback to bullet point and numbered list parsing
   - Structured topic output with timestamps

3. **Playlist Processing**:
   - Paginated API calls for large playlists
   - Complete video metadata extraction
   - Playlist information and statistics

### MCP Integration
- **Tools Registered**: 3 functional MCP tools
- **Transport**: stdio (ready for Claude Desktop)
- **Validation**: Input URL validation and error reporting
- **Logging**: Comprehensive operation tracking

## Known Limitations

### API Dependencies
- **YouTube Data API**: Requires valid API key and quota management
- **Rate Limiting**: Subject to YouTube API rate limits and quotas
- **Private Content**: Cannot access private or restricted videos

### Caption Limitations
- **Availability**: Depends on video having captions (auto or manual)
- **Language Support**: Limited to YouTube's supported caption languages
- **Quality**: Auto-generated captions may have accuracy issues

### Topic Extraction Constraints
- **Pattern Dependent**: Relies on common timestamp and formatting patterns
- **Description Quality**: Effectiveness depends on well-structured video descriptions
- **False Positives**: May extract unrelated timestamp-like patterns

## Technical Learnings

### MCP Development Insights
1. **Server Initialization**: Keep module-level initialization minimal to avoid import issues
2. **Tool Registration**: Use descriptive docstrings - they become tool descriptions in MCP
3. **Error Handling**: Return structured error dictionaries rather than raising exceptions
4. **Logging Strategy**: Implement comprehensive logging for debugging MCP interactions

### YouTube API Best Practices
1. **Cache Management**: Disable discovery cache to avoid version warnings
2. **Quota Awareness**: Structure API calls to minimize quota usage
3. **Pagination**: Always handle pagination for playlist operations
4. **Error Handling**: Distinguish between API errors and network issues

### Python Project Structure
1. **Import Management**: Avoid circular imports in __init__.py files
2. **Type Annotations**: Use modern syntax for better IDE support
3. **Configuration**: Environment-based config with sensible defaults
4. **Testing**: Separate test utilities from production code

## Development Tools & Workflow

### Package Management
- **UV**: Modern Python package manager for fast dependency resolution
- **Benefits**: Faster than pip, better dependency locking, integrated virtual environments

### Code Quality Tools
- **Black**: Consistent code formatting with 100-char line length
- **Ruff**: Fast Python linter with comprehensive rule set
- **Integration**: Both tools configured in pyproject.toml

### MCP Testing
- **Local Testing**: Direct server execution with `uv run python -m youtube_mcp.server`
- **Validation**: Function-level testing before MCP integration
- **Debug Mode**: Environment variable control for detailed logging

### Phase 3: Claude Desktop Integration & Testing ✅ (Completed)
- **Objective**: Successfully integrate MCP server with Claude Desktop and validate all functionality
- **Key Achievements**:
  - ✅ Configured Claude Desktop integration with absolute path resolution
  - ✅ **Critical Fix**: Resolved MCP protocol violations (stdout contamination)
  - ✅ Successfully tested all 3 MCP tools through Claude Desktop interface
  - ✅ Validated error handling scenarios (invalid URLs, private videos)
  - ✅ Created comprehensive end-user documentation (README.md)
  - ✅ Established troubleshooting guide based on real issues encountered

## Critical Issues Encountered & Resolutions (Phase 3)

### Issue 1: "spawn uv ENOENT" Error on Claude Desktop Launch
**Problem**: Claude Desktop could not find the `uv` command when launching the MCP server

**Root Cause**: GUI applications on macOS don't inherit shell PATH environment variables

**Solution**: 
- Used absolute path to uv executable: `/Users/rohitseelam/.local/bin/uv`
- Found path using `which uv` command
- Updated claude_desktop_config.json with full path

**Research Method**: Used Perplexity MCP to investigate common MCP deployment issues

### Issue 2: MCP Protocol Violations - JSON Parsing Errors  
**Problem**: Claude Desktop showing JSON parsing errors:
- `Unexpected token 'd', "[download]"... is not valid JSON`
- `Unexpected token 'A', "Available tools:" is not valid JSON`

**Root Cause**: MCP server writing non-JSON output to stdout, violating MCP protocol

**Technical Analysis**:
- MCP expects only JSON-RPC messages on stdout
- Our server had `print()` statements in main() function
- yt-dlp was outputting download progress to stdout

**Solution**:
1. **Removed all print() statements** from `server.py:197-201` and error handling sections
2. **Enhanced yt-dlp silencing** by adding:
   - `"noprogress": True` - Prevents `[download]` messages
   - `"no_color": True` - Removes color codes
   - `"extract_flat": False` - Ensures proper processing
3. **Redirected all debugging output** to stderr via logger

**Research Method**: Used Perplexity MCP to understand MCP protocol requirements and common violations

**Files Modified**:
- `src/youtube_mcp/server.py` - Removed print statements (lines 197-201, 185-186, 210)
- `src/youtube_mcp/youtube_client.py` - Enhanced yt-dlp options (lines 47-49)

### Testing Results
**All Tools Validated Successfully**:
- ✅ `extract_youtube_captions` - Multi-language caption extraction
- ✅ `extract_video_topics` - Topic/timestamp parsing from descriptions  
- ✅ `extract_playlist_titles` - Playlist video metadata extraction
- ✅ Error handling for invalid URLs, private videos, missing captions

**Integration Quality**:
- ✅ Clean Claude Desktop startup with no errors
- ✅ Proper JSON-RPC communication
- ✅ Structured error responses for edge cases
- ✅ Comprehensive logging for debugging

## Next Steps (Phase 4 - Future Scope)

### Distribution Strategy Decision
1. **Option A**: Keep Local - Share as Git repository with absolute path configuration
2. **Option B**: Publish to PyPI - Package with `uv build` & `uv publish` for easy installation
3. **Option C**: Hybrid Approach - Support both local development and PyPI distribution

### Potential Enhancements
1. **Caching**: Implement response caching for repeated requests
2. **Batch Operations**: Support multiple video/playlist processing
3. **Output Formats**: Add structured output options (JSON, CSV)
4. **Authentication**: Consider OAuth for increased API quotas

## Project Metrics

### Development Timeline
- **Phase 0**: ~1 session (Documentation setup)
- **Phase 1**: ~2 sessions (Core functionality implementation)  
- **Phase 2**: ~1 session (MCP server implementation + debugging)
- **Phase 3**: ~1 session (Claude Desktop integration + critical fixes)
- **Total**: ~5 development sessions

### Code Statistics
- **Python Files**: 4 core modules + 1 test file
- **Dependencies**: 4 core + 3 dev dependencies
- **MCP Tools**: 3 functional tools
- **Test Coverage**: Comprehensive function-level testing

### Technical Debt
- **Minimal**: Clean architecture with proper separation of concerns
- **Maintenance**: Standard Python project with modern tooling
- **Documentation**: Well-documented code with comprehensive project docs

---

*This log serves as a comprehensive record of the YouTube MCP project development through Phase 3. The project is now fully functional with Claude Desktop integration. For current project status and instructions, refer to CLAUDE.md.*