# Low-Level Architecture Guide: MCP vs HTTP Communication

## Table of Contents

### Initial Questions
1. [HTTP Server vs stdio Process Architecture](#1-http-server-vs-stdio-process-architecture)
2. [REST Endpoints vs MCP Tools](#2-rest-endpoints-vs-mcp-tools)
3. [Process Communication Mechanisms](#3-process-communication-mechanisms)
4. [MCP Protocol Restrictions](#4-mcp-protocol-restrictions)
5. [Testing Mechanisms: curl/Postman vs Claude Desktop](#5-testing-mechanisms-curlpostman-vs-claude-desktop)

### Follow-up Questions
6. [JSON Processing in stdio Communication](#6-json-processing-in-stdio-communication)
7. [HTTP Request Format and Structure](#7-http-request-format-and-structure)
8. [Kernel Memory Buffers](#8-kernel-memory-buffers)
9. [What is Flask?](#9-what-is-flask)
10. [GET/POST vs JSON-RPC Methods](#10-getpost-vs-json-rpc-methods)
11. [curl's Relationship to HTTP Methods](#11-curls-relationship-to-http-methods)
12. [GET vs POST Parameter Handling](#12-get-vs-post-parameter-handling)
13. [TCP/IP vs SSL/TLS Encryption](#13-tcpip-vs-ssltls-encryption)
14. [MCP Method Discovery & JSON-RPC Structure Formation](#14-mcp-method-discovery--json-rpc-structure-formation)
15. [TCP/IP Visual Representation](#15-tcpip-visual-representation)

### Additional Clarifications
16. [Additional Clarifications](#16-additional-clarifications)
17. [Summary - Key Architectural Insights](#summary---key-architectural-insights)

---

## 1. HTTP Server vs stdio Process Architecture

**Original Questions:** "HTTP server and stdio process, what's the difference between http and https, How are stdin and stdout defined internally?"

### HTTP Server (Network-Based Communication)

**What it is:** A program that listens on a network port for incoming connections

```python
# Basic HTTP server example
import socket

# Create a socket (network endpoint)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 8000))  # Listen on port 8000
server_socket.listen(5)  # Allow 5 pending connections

print("HTTP Server listening on localhost:8000")

while True:
    # Wait for a client to connect
    client_socket, address = server_socket.accept()
    print(f"Connection from {address}")
    
    # Read the HTTP request
    request = client_socket.recv(1024).decode()
    print("Received:", request)
    
    # Send HTTP response
    response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello World!"
    client_socket.send(response.encode())
    client_socket.close()
```

**How clients connect:**
```bash
# From anywhere on the network:
curl http://localhost:8000
# Browser can visit: http://localhost:8000
```

### stdio Process (Pipe-Based Communication)

**What it is:** A program that reads from stdin and writes to stdout (no network)

```python
# Basic stdio process example
import sys
import json

print("stdio process started", file=sys.stderr)  # Debug to stderr

while True:
    try:
        # Read a line from stdin
        line = sys.stdin.readline().strip()
        if not line:
            break
            
        # Parse JSON input
        request = json.loads(line)
        print(f"Received: {request}", file=sys.stderr)
        
        # Process and respond via stdout
        response = {"result": f"Processed: {request['data']}"}
        print(json.dumps(response))  # Goes to stdout
        sys.stdout.flush()  # Ensure it's sent immediately
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
```

**How clients connect:**
```bash
# Only through process pipes:
echo '{"data": "hello"}' | python stdio_process.py
# No network access - only parent process can communicate
```

### HTTP vs HTTPS

```python
# HTTP (unencrypted)
import socket
request = "GET /api/data HTTP/1.1\r\nHost: example.com\r\n\r\n"
# Raw text sent over network - anyone can read it

# HTTPS (encrypted with TLS/SSL)
import ssl
context = ssl.create_default_context()
with socket.create_connection(('example.com', 443)) as sock:
    with context.wrap_socket(sock, server_hostname='example.com') as ssock:
        ssock.send(request.encode())
        # Encrypted before sending - only server can decrypt
```

### stdin/stdout - Operating System Level Definition

**At the OS level**, every process gets 3 file descriptors:

```c
// In C (how the OS actually implements this):
#define STDIN_FILENO  0    // File descriptor 0
#define STDOUT_FILENO 1    // File descriptor 1  
#define STDERR_FILENO 2    // File descriptor 2

// When you start any program:
int main() {
    // fd 0 (stdin)  - automatically connected to keyboard/pipe
    // fd 1 (stdout) - automatically connected to terminal/pipe  
    // fd 2 (stderr) - automatically connected to terminal
}
```

**In Python, these become:**

```python
import sys

# These are file objects wrapping the OS file descriptors:
sys.stdin   # Wraps file descriptor 0
sys.stdout  # Wraps file descriptor 1
sys.stderr  # Wraps file descriptor 2

# Reading from stdin (blocking operation):
line = sys.stdin.readline()  # Waits until something is written to fd 0

# Writing to stdout:
sys.stdout.write("Hello")    # Writes to fd 1
print("Hello")               # Same as above + newline

# Writing to stderr:
sys.stderr.write("Error!")   # Writes to fd 2
```

---

## 2. REST Endpoints vs MCP Tools

**Original Questions:** "What are REST endpoints? How are they different from MCP tools, why did they get the name ENDPOINTS?"

### Why Called "ENDPOINTS"?

**Endpoint = "End Point of Communication"** - literally where your request "ends up"

```python
# HTTP REST Server - Creates multiple endpoints
from flask import Flask
app = Flask(__name__)

# ENDPOINT 1: http://localhost:5000/users
@app.route('/users', methods=['GET'])
def get_users():
    return {"users": ["alice", "bob"]}

# ENDPOINT 2: http://localhost:5000/users/123  
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return {"user": f"user_{user_id}"}

# ENDPOINT 3: http://localhost:5000/videos/captions
@app.route('/videos/captions', methods=['POST'])
def get_captions():
    return {"captions": "extracted text"}

app.run(host='localhost', port=5000)
```

**Each endpoint is a unique URL that accepts specific HTTP methods:**
- `GET /users` - Different from `POST /users`
- `GET /users/123` - Different from `GET /users/456`
- Each has its own URL path, HTTP method, parameters

### MCP Tools - Different Architecture

```python
# MCP Server - Creates tools (not endpoints)
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("My Server")

# TOOL 1: extract_youtube_captions
@mcp.tool()
def extract_youtube_captions(video_url: str, lang: str = "en"):
    return {"captions": "extracted text"}

# TOOL 2: extract_video_topics  
@mcp.tool()
def extract_video_topics(video_url: str):
    return {"topics": ["intro", "main", "conclusion"]}

# TOOL 3: extract_playlist_titles
@mcp.tool()
def extract_playlist_titles(playlist_url: str):
    return {"titles": ["video1", "video2"]}

mcp.run(transport="stdio")  # No network, no URLs
```

**Key Differences:**

| REST Endpoints | MCP Tools |
|---------------|-----------|
| **Location**: URLs (`/api/users`) | **Name**: Function names (`extract_captions`) |
| **Access**: HTTP methods (GET/POST) | **Access**: JSON-RPC method calls |
| **Discovery**: Documentation/OpenAPI | **Discovery**: `tools/list` command |
| **Parameters**: URL params + body | **Parameters**: Function arguments |

### How They're Called Differently

**REST Endpoint Call:**
```bash
# HTTP request to a specific URL endpoint
curl -X POST http://localhost:5000/videos/captions \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtu.be/abc", "language": "en"}'
```

**MCP Tool Call:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "extract_youtube_captions",
    "arguments": {
      "video_url": "https://youtu.be/abc", 
      "lang": "en"
    }
  },
  "id": 1
}
```

---

## 3. Process Communication Mechanisms

**Original Question:** "How will the data be communication with these processes like above."

### Network Communication (HTTP)

```python
# Data flows through network stack:
[Your App] → [OS Network Stack] → [Network Card] → [Internet] → [Remote Server]

# Example - HTTP client sending data:
import requests

# This creates a TCP connection across the network:
response = requests.post('http://example.com/api', 
                        json={'data': 'hello'})

# Internally this does:
# 1. DNS lookup: example.com → IP address
# 2. TCP handshake: establish connection
# 3. HTTP request: send headers + body
# 4. Wait for HTTP response
# 5. TCP teardown: close connection
```

### Process Communication (Pipes)

```python
# Data flows through OS kernel buffers:
[Parent Process] ↔ [OS Kernel Pipe Buffer] ↔ [Child Process]

# Example - Your MCP server communication:
import subprocess
import json

# Claude Desktop does this:
process = subprocess.Popen([
    'uv', 'run', 'python', '-m', 'youtube_mcp.server'
], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Send JSON-RPC to your server:
request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
process.stdin.write(json.dumps(request).encode() + b'\n')
process.stdin.flush()

# Read response from your server:
response_line = process.stdout.readline()
response = json.loads(response_line.decode())
```

### Visual Comparison

**HTTP Communication:**
```
[Browser/curl] ──TCP/IP──→ [Network] ──TCP/IP──→ [Web Server]
     ↑                                              ↓
   Request                                      Response
```

**stdio Communication:**
```
[Claude Desktop] ──pipe──→ [OS Kernel] ──pipe──→ [MCP Server]
       ↑                                         ↓
   JSON-RPC Request                        JSON-RPC Response
```

---

## 4. MCP Protocol Restrictions

**Original Question:** "Why are you saying Only MCP clients can call, is there any underlying protocol? Where is it defined exactly."

### The MCP Protocol Definition

**MCP is defined in official specifications:**
- **GitHub**: https://github.com/modelcontextprotocol/specification
- **Official Docs**: https://spec.modelcontextprotocol.io/

**Key Protocol Requirements:**

```typescript
// From MCP spec - exact message format required:
interface JSONRPCRequest {
  jsonrpc: "2.0";           // Must be exactly "2.0"
  method: string;           // Must be valid MCP method
  params?: object;          // Optional parameters
  id: string | number;      // Request ID for correlation
}

interface JSONRPCResponse {
  jsonrpc: "2.0";
  result?: any;             // Success result
  error?: JSONRPCError;     // Error details
  id: string | number;      // Matching request ID
}
```

### Why Random Programs Can't Call MCP Servers

**1. Transport Layer Requirement:**
```python
# MCP servers ONLY accept stdio transport:
mcp.run(transport="stdio")  # No HTTP, no TCP sockets

# You cannot do this:
# curl http://localhost:8000/tools  ❌ - No HTTP server
# telnet localhost 8000             ❌ - No TCP server
```

**2. Process Parent-Child Relationship:**
```python
# Only the parent process can communicate with child via pipes:

# ✅ Claude Desktop can do this (parent):
process = subprocess.Popen(['your-mcp-server'], 
                          stdin=PIPE, stdout=PIPE)

# ❌ Random program cannot access existing pipes:
# No way to "connect" to running MCP server from outside
```

**3. Exact Protocol Compliance:**
```python
# MCP servers expect EXACT JSON-RPC format:

# ✅ Valid MCP request:
{"jsonrpc": "2.0", "method": "tools/list", "id": 1}

# ❌ Invalid requests that will fail:
{"method": "tools/list"}                    # Missing jsonrpc field
{"jsonrpc": "1.0", "method": "tools/list"}  # Wrong version
"GET /tools HTTP/1.1"                      # HTTP format
```

### What Makes a Program an "MCP Client"

**An MCP client must:**

```python
# 1. Spawn MCP server as child process
import subprocess
server = subprocess.Popen(['mcp-server'], stdin=PIPE, stdout=PIPE)

# 2. Send proper JSON-RPC initialization
init_msg = {
    "jsonrpc": "2.0",
    "method": "initialize", 
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "my-client", "version": "1.0"}
    },
    "id": 0
}
server.stdin.write(json.dumps(init_msg).encode() + b'\n')

# 3. Handle JSON-RPC responses properly
response = json.loads(server.stdout.readline())
if "error" in response:
    handle_error(response["error"])
else:
    handle_result(response["result"])

# 4. Maintain bidirectional JSON-RPC communication
# 5. Handle server lifecycle (startup, shutdown, errors)
```

---

## 5. Testing Mechanisms: curl/Postman vs Claude Desktop

**Original Question:** "What happens exactly in curl/Postman testing and Claude Desktop testing internally"

### curl/Postman Testing (HTTP Server)

**What happens internally when you run `curl`:**

```bash
curl -X POST http://localhost:5000/api/captions \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtu.be/abc"}'
```

**Step-by-step internal process:**

```python
# 1. curl creates a TCP socket
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 2. curl connects to server
sock.connect(('localhost', 5000))

# 3. curl formats HTTP request
http_request = """POST /api/captions HTTP/1.1\r
Host: localhost:5000\r
Content-Type: application/json\r
Content-Length: 41\r
\r
{"video_url": "https://youtu.be/abc"}"""

# 4. curl sends raw bytes over network
sock.send(http_request.encode())

# 5. curl reads HTTP response
response = sock.recv(4096).decode()
print(response)
# HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"captions": "..."}

# 6. curl closes connection
sock.close()
```

**What your HTTP server sees:**
```python
# Your Flask/FastAPI server receives:
@app.post("/api/captions")
def get_captions(request_data: dict):
    # request_data = {"video_url": "https://youtu.be/abc"}
    return {"captions": "extracted text"}
```

### Claude Desktop Testing (MCP Server)

**What happens internally when Claude calls your MCP tool:**

```python
# 1. Claude Desktop has already spawned your server as child process
# (This happened when Claude Desktop started)

# 2. Claude Desktop creates JSON-RPC request
request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "extract_youtube_captions",
        "arguments": {"video_url": "https://youtu.be/abc"}
    },
    "id": 42
}

# 3. Claude Desktop writes to your server's stdin
your_server_process.stdin.write(json.dumps(request).encode() + b'\n')
your_server_process.stdin.flush()

# 4. Your FastMCP server receives and processes
# (This is handled automatically by FastMCP framework)

# 5. Claude Desktop reads from your server's stdout
response_line = your_server_process.stdout.readline()
response = json.loads(response_line.decode())
# {"jsonrpc": "2.0", "result": {"captions": "..."}, "id": 42}

# 6. Connection stays open for next request (no disconnect)
```

**What your MCP server sees:**
```python
@mcp.tool()
def extract_youtube_captions(video_url: str):
    # video_url = "https://youtu.be/abc"
    # FastMCP automatically parsed JSON-RPC and called this function
    return {"captions": "extracted text"}
```

### Key Differences in Testing

| curl/Postman (HTTP) | Claude Desktop (MCP) |
|---------------------|---------------------|
| **Connection**: New TCP connection per request | **Connection**: Persistent stdin/stdout pipes |
| **Protocol**: HTTP request/response | **Protocol**: JSON-RPC over stdio |
| **Discovery**: Manual URL knowledge | **Discovery**: Automatic via `tools/list` |
| **Authentication**: Headers/tokens | **Authentication**: Process ownership |
| **Errors**: HTTP status codes | **Errors**: JSON-RPC error objects |
| **Testing Tools**: Any HTTP client | **Testing Tools**: Only MCP clients |

---

## 6. JSON Processing in stdio Communication

**Question:** "Explain this part, can't understand how a client request is processed exactly, I just understood client sends json input to the running piped stdio process. What is the difference between json loads and json dumps ? Does the request from client's end come to stdin fd as json or as text ?"

### json.loads vs json.dumps - The Conversion Process

```python
import json

# json.dumps = Convert Python object TO JSON string
python_dict = {"name": "alice", "age": 25}
json_string = json.dumps(python_dict)
print(json_string)  # '{"name": "alice", "age": 25}'
print(type(json_string))  # <class 'str'>

# json.loads = Convert JSON string TO Python object  
json_text = '{"name": "bob", "score": 100}'
python_object = json.loads(json_text)
print(python_object)  # {'name': 'bob', 'score': 100}
print(type(python_object))  # <class 'dict'>
```

### How Data Flows Through stdin/stdout

**Client sends data as TEXT (not binary JSON):**

```python
# What Claude Desktop actually sends to your stdin:
text_data = '{"jsonrpc": "2.0", "method": "tools/call", "id": 1}\n'
# This is a STRING, not a JSON object

# Your server receives this as text and must parse it:
import sys
import json

while True:
    # Read TEXT from stdin
    line = sys.stdin.readline()  # Returns: '{"jsonrpc": "2.0", ...}\n'
    print(f"Raw input type: {type(line)}")  # <class 'str'>
    print(f"Raw input: {line}")
    
    if not line.strip():
        break
    
    # Convert TEXT to Python object
    request = json.loads(line.strip())  # Now it's a dict
    print(f"Parsed type: {type(request)}")  # <class 'dict'>
    print(f"Parsed object: {request}")
    
    # Process the request
    result = {"result": f"Processed: {request.get('method', 'unknown')}"}
    
    # Convert Python object back to TEXT
    response_text = json.dumps(result)  # Back to string
    print(f"Response type: {type(response_text)}")  # <class 'str'>
    
    # Send TEXT to stdout
    print(response_text)  # Sends string to stdout
    sys.stdout.flush()   # Force immediate write
```

**Visual Data Flow:**
```
Claude Desktop: {"method": "tools/call"}  (Python dict)
       ↓ json.dumps()
Claude Desktop: '{"method": "tools/call"}' (JSON string)
       ↓ write to stdin
Your Server stdin: '{"method": "tools/call"}' (raw text)
       ↓ json.loads()  
Your Server: {"method": "tools/call"}  (Python dict)
       ↓ process
Your Server: {"result": "success"}  (Python dict)
       ↓ json.dumps()
Your Server stdout: '{"result": "success"}' (JSON string) 
       ↓ read from stdout
Claude Desktop: '{"result": "success"}' (raw text)
       ↓ json.loads()
Claude Desktop: {"result": "success"}  (Python dict)
```

---

## 7. HTTP Request Format and Structure

**Question:** "Here I understood that in https we encode the request. I did not understand the request part exactly which now has Get /api/data and something more. How this request is different from the original request you gave?"

### Understanding the HTTP Request Format

**The HTTP request I showed is the COMPLETE, RAW format that travels over the network:**

```python
# This is the EXACT text sent over the network:
request = "GET /api/data HTTP/1.1\r\nHost: example.com\r\n\r\n"
```

**Let's break it down line by line:**

```python
# Line 1: REQUEST LINE
"GET /api/data HTTP/1.1\r\n"
#  ^     ^         ^
#  |     |         HTTP version
#  |     Path/URL on the server
#  HTTP Method

# Line 2: HEADERS
"Host: example.com\r\n"
#  ^              ^
#  Header name    Header value

# Line 3: END OF HEADERS (empty line)
"\r\n"

# (No body for GET requests)
```

**Complete breakdown with visualization:**

```python
import socket

# STEP 1: What your browser/curl actually sends:
raw_http_request = """GET /api/data HTTP/1.1\r
Host: example.com\r
User-Agent: Mozilla/5.0\r
Accept: application/json\r
\r
"""

print("Raw HTTP request:")
print(repr(raw_http_request))  # Shows \r\n characters

# STEP 2: What the server receives:
def simple_http_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8000))
    server_socket.listen(1)
    
    while True:
        client_socket, address = server_socket.accept()
        
        # This receives the EXACT raw text above:
        request = client_socket.recv(1024).decode()
        print("Server received EXACTLY this:")
        print(repr(request))
        # Output: 'GET /api/data HTTP/1.1\r\nHost: example.com\r\n\r\n'
        
        # Server must parse this manually or use a framework
        lines = request.split('\r\n')
        method, path, version = lines[0].split(' ')
        print(f"Method: {method}, Path: {path}, Version: {version}")
        
        client_socket.close()

# The difference from my previous example:
# Previous: Showed what server receives (raw text)
# HTTPS example: Showed what gets encrypted (same raw text)
```

**HTTPS vs HTTP - Same Request, Different Transport:**

```python
# HTTP: Raw text sent directly
request_text = "GET /api/data HTTP/1.1\r\nHost: example.com\r\n\r\n"
socket.send(request_text.encode())  # Sent as plain text

# HTTPS: Same text, but encrypted first
request_text = "GET /api/data HTTP/1.1\r\nHost: example.com\r\n\r\n"
encrypted_data = ssl_encrypt(request_text.encode())  # Encrypted
ssl_socket.send(encrypted_data)  # Sent as encrypted bytes
```

---

## 8. Kernel Memory Buffers

**Question:** "What's a buffer in kernel memory ?"

**A buffer is temporary storage space in the computer's memory managed by the operating system.**

```python
# Think of a buffer like a mailbox:
# - Has limited space
# - Stores messages temporarily  
# - One process puts messages in, another takes them out

# Kernel buffer for pipes:
import os

# When you create a pipe:
read_fd, write_fd = os.pipe()

# The OS creates a buffer in kernel memory:
# ┌─────────────────────────────────────┐
# │ KERNEL BUFFER (typically 64KB)     │
# │ [data][data][data][empty space]     │
# │  ↑                           ↑     │
# │ read position              write   │
# │                          position  │
# └─────────────────────────────────────┘

# Process A writes data:
os.write(write_fd, b"Hello from A")
# Buffer now: [Hello from A][empty space]

# Process B reads data:
data = os.read(read_fd, 1024)  # Reads "Hello from A"
# Buffer now: [empty space]
```

**Real example showing buffer behavior:**

```python
import subprocess
import time

# Create a subprocess that will fill the buffer
proc = subprocess.Popen(['python', '-c', '''
import sys
# Write a lot of data to stdout
for i in range(1000):
    print(f"Line {i} with some data")
    sys.stdout.flush()
'''], stdout=subprocess.PIPE)

# The kernel creates a buffer between processes
# If we don't read, the buffer fills up and the child process blocks

time.sleep(2)  # Let child write to buffer

# Now read from the buffer:
output, _ = proc.communicate()
print(f"Read {len(output)} bytes from kernel buffer")
```

---

## 9. What is Flask?

**Question:** "What is flask ?"

**Flask is a Python web framework that makes creating HTTP servers easy.**

```python
# Without Flask - Raw HTTP server (complex):
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 5000))
server_socket.listen(5)

while True:
    client_socket, address = server_socket.accept()
    request = client_socket.recv(1024).decode()
    
    # Parse HTTP manually:
    lines = request.split('\r\n')
    method, path, version = lines[0].split(' ')
    
    if path == '/users' and method == 'GET':
        response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"users\": []}"
    else:
        response = "HTTP/1.1 404 Not Found\r\n\r\nNot Found"
    
    client_socket.send(response.encode())
    client_socket.close()

# With Flask - Same functionality (simple):
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify({"users": []})

app.run(host='localhost', port=5000)
```

**Flask handles all the HTTP complexity:**
- Parsing HTTP requests
- Routing URLs to functions  
- Creating HTTP responses
- Managing connections
- Error handling

---

## 10. GET/POST vs JSON-RPC Methods

**Question:** "Difference between GET and POST Methods and how do they differ from JSON-RPC methods?"

### HTTP Methods (GET/POST)

**HTTP methods define HOW you access a resource:**

```python
# GET - Retrieve data (read-only)
# Request format:
"GET /api/users HTTP/1.1\r\nHost: example.com\r\n\r\n"

# POST - Send data to server (create/modify)  
# Request format:
"""POST /api/users HTTP/1.1\r
Host: example.com\r
Content-Type: application/json\r
Content-Length: 25\r
\r
{"name": "alice"}"""

# PUT - Replace entire resource
"PUT /api/users/123 HTTP/1.1\r\n..."

# DELETE - Remove resource
"DELETE /api/users/123 HTTP/1.1\r\n..."
```

**Each HTTP method is a different PROTOCOL OPERATION:**

```python
from flask import Flask, request
app = Flask(__name__)

# Same URL, different methods = different functions
@app.route('/users', methods=['GET'])
def get_users():
    return {"users": ["alice", "bob"]}

@app.route('/users', methods=['POST']) 
def create_user():
    user_data = request.json  # Gets data from POST body
    return {"created": user_data["name"]}

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    return {"deleted": user_id}
```

### JSON-RPC Methods

**JSON-RPC methods are FUNCTION NAMES in a message:**

```python
# All JSON-RPC requests look the same, only "method" changes:

# Method 1: tools/list
{
  "jsonrpc": "2.0",
  "method": "tools/list",    # ← This is the "method"
  "params": {},
  "id": 1
}

# Method 2: tools/call  
{
  "jsonrpc": "2.0", 
  "method": "tools/call",    # ← Different method name
  "params": {
    "name": "extract_captions",
    "arguments": {"url": "..."}
  },
  "id": 2
}

# Method 3: Custom method
{
  "jsonrpc": "2.0",
  "method": "my_custom_function",  # ← Any function name
  "params": {"param1": "value"},
  "id": 3
}
```

**Key Differences:**

| HTTP Methods | JSON-RPC Methods |
|-------------|-----------------|
| **Purpose**: Protocol operations (GET/POST/PUT/DELETE) | **Purpose**: Function names (any name you want) |
| **Location**: HTTP header (`GET /path`) | **Location**: JSON message (`"method": "function_name"`) |
| **Fixed set**: Only ~9 standard methods | **Unlimited**: Any function name |
| **Parameters**: URL + headers + body | **Parameters**: `"params"` field only |
| **Transport**: Always HTTP | **Transport**: Any (stdio, HTTP, WebSocket) |

---

## 11. curl's Relationship to HTTP Methods

**Question:** "How curl is linked to the GET and POST method calls?"

**curl is an HTTP client that can use any HTTP method:**

```bash
# curl defaults to GET method:
curl http://example.com/api/users
# Sends: "GET /api/users HTTP/1.1\r\nHost: example.com\r\n\r\n"

# curl with explicit GET:
curl -X GET http://example.com/api/users
# Same as above

# curl with POST method:
curl -X POST http://example.com/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "alice"}'
# Sends: "POST /api/users HTTP/1.1\r\nHost: example.com\r\nContent-Type: application/json\r\n\r\n{\"name\": \"alice\"}"

# curl with other methods:
curl -X PUT http://example.com/api/users/123
curl -X DELETE http://example.com/api/users/123
curl -X PATCH http://example.com/api/users/123
```

**What curl actually does internally:**

```python
# This is what curl does when you run:
# curl -X POST http://example.com/api -d '{"name": "alice"}'

import socket

# 1. Parse the URL
host = "example.com"
port = 80
path = "/api"

# 2. Create HTTP request with specified method
http_request = f"""POST {path} HTTP/1.1\r
Host: {host}\r
Content-Type: application/json\r
Content-Length: 16\r
\r
{{"name": "alice"}}"""

# 3. Send over TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, port))
sock.send(http_request.encode())

# 4. Read response
response = sock.recv(4096).decode()
print(response)
sock.close()
```

---

## 12. GET vs POST Parameter Handling

**Question:** "How are the parameters sent in GET and post differently ? is there a concept of header and body here ?"

### GET Parameters (URL Query String)

```bash
# GET - Parameters in URL
curl "http://example.com/api/search?query=python&limit=10&page=1"

# Raw HTTP request:
"""GET /api/search?query=python&limit=10&page=1 HTTP/1.1\r
Host: example.com\r
\r
"""
# Notice: NO BODY, parameters in URL
```

**Server receives parameters from URL:**

```python
from flask import Flask, request
app = Flask(__name__)

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query')    # Gets 'python'
    limit = request.args.get('limit')    # Gets '10' 
    page = request.args.get('page')      # Gets '1'
    return {"results": f"Searching for {query}"}
```

### POST Parameters (Request Body)

```bash
# POST - Parameters in body
curl -X POST http://example.com/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "alice", "age": 25}'

# Raw HTTP request:
"""POST /api/users HTTP/1.1\r
Host: example.com\r
Content-Type: application/json\r
Content-Length: 25\r
\r
{"name": "alice", "age": 25}"""
#  ↑
# Body starts here
```

**Server receives parameters from body:**

```python
@app.route('/api/users', methods=['POST'])
def create_user():
    name = request.json.get('name')    # Gets 'alice' from body
    age = request.json.get('age')      # Gets 25 from body
    return {"created": f"User {name}"}
```

### Headers vs Body Concept

```python
# HTTP request structure:
"""
REQUEST LINE:    POST /api/users HTTP/1.1\r\n
HEADERS:         Host: example.com\r\n
                 Content-Type: application/json\r\n
                 Authorization: Bearer token123\r\n
EMPTY LINE:      \r\n
BODY:            {"name": "alice", "age": 25}
"""

# Headers = metadata about the request
# Body = actual data being sent
```

**Example showing both:**

```python
from flask import Flask, request
app = Flask(__name__)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    # From headers:
    content_type = request.headers.get('Content-Type')
    auth_token = request.headers.get('Authorization')
    
    # From body:
    file_data = request.json.get('file_content')
    filename = request.json.get('filename')
    
    return {
        "content_type": content_type,  # From header
        "filename": filename           # From body
    }
```

---

## 13. TCP/IP vs SSL/TLS Encryption

**Question:** "does TCP has encryption off unlike ssl, sorry is TCP related to IP I'm confused on the terms, am.i thinking TCL?"

**You're thinking correctly! TCP is related to IP. Let me clarify the layers:**

### Network Stack Layers

```python
# The network stack (from bottom to top):
"""
Layer 4: APPLICATION  →  HTTP, HTTPS, FTP, SMTP
Layer 3: TRANSPORT    →  TCP, UDP  
Layer 2: INTERNET     →  IP (Internet Protocol)
Layer 1: PHYSICAL     →  Ethernet, WiFi
"""

# TCP/IP = TCP + IP working together
# SSL/TLS = Encryption layer that sits BETWEEN TCP and HTTP
```

### TCP vs TCP+SSL

```python
# TCP (no encryption):
import socket

# Raw TCP connection:
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('example.com', 80))  # Port 80 = HTTP
sock.send(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
data = sock.recv(1024)
print(data)  # Anyone monitoring network can read this

# TCP + SSL (encrypted):
import ssl

# SSL-wrapped TCP connection:
context = ssl.create_default_context()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_sock = context.wrap_socket(sock, server_hostname='example.com')
ssl_sock.connect(('example.com', 443))  # Port 443 = HTTPS
ssl_sock.send(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
data = ssl_sock.recv(1024)
print(data)  # Network monitoring shows encrypted gibberish
```

### Visual Representation

```python
# HTTP (TCP without encryption):
[Browser] ──TCP──→ [Internet] ──TCP──→ [Server]
           ↑                    ↑
    Plain text data      Plain text data
    Anyone can read      Anyone can read

# HTTPS (TCP with SSL encryption):
[Browser] ──TCP+SSL──→ [Internet] ──TCP+SSL──→ [Server]
           ↑                          ↑
    Encrypted data             Encrypted data
    Looks like random bytes    Server decrypts
```

**Key Points:**
- **TCP** = Reliable transport protocol (ensures data arrives)
- **IP** = Internet addressing (how to find the destination)  
- **SSL/TLS** = Encryption layer (protects data in transit)
- **HTTP** = Application protocol (web requests/responses)
- **HTTPS** = HTTP + SSL (encrypted web traffic)

---

## 14. MCP Method Discovery & JSON-RPC Structure Formation

**Question:** "What are different methods that my Claude desktop have access to ? /ttol/list /tools call ? I want to understand how claude desktop or my llm knows what structure my mcp server expects and how internally that specific json npc structure forms ?"

### Available MCP Methods (Standard Protocol)

**Claude Desktop knows these EXACT methods from the MCP specification:**

```python
# Standard MCP methods that Claude Desktop expects:
MCP_METHODS = {
    "initialize": "Handshake when connection starts",
    "tools/list": "Get list of available tools",
    "tools/call": "Execute a specific tool",
    "prompts/list": "Get available prompts", 
    "prompts/get": "Get a specific prompt",
    "resources/list": "Get available resources",
    "resources/read": "Read a specific resource"
}
```

### How Claude Desktop Discovers Your Tools

**Step-by-step discovery process:**

```python
# 1. Claude Desktop starts your server and sends:
initialize_request = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "claude-ai", "version": "0.1.0"}
    },
    "id": 1
}

# 2. Your FastMCP server responds:
initialize_response = {
    "jsonrpc": "2.0", 
    "result": {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": {"name": "YouTube MCP", "version": "1.0"}
    },
    "id": 1
}

# 3. Claude Desktop asks for tool list:
tools_list_request = {
    "jsonrpc": "2.0",
    "method": "tools/list", 
    "params": {},
    "id": 2
}

# 4. Your server responds with tool metadata:
tools_list_response = {
    "jsonrpc": "2.0",
    "result": {
        "tools": [
            {
                "name": "extract_youtube_captions",
                "description": "Extract captions/subtitles from a YouTube video...",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "video_url": {"type": "string", "title": "Video Url"},
                        "language_preference": {
                            "type": "string", 
                            "title": "Language Preference",
                            "default": "en"
                        }
                    },
                    "required": ["video_url"]
                }
            }
        ]
    },
    "id": 2
}
```

### How FastMCP Generates Tool Metadata

**Your code gets automatically transformed:**

```python
# Your function:
@mcp.tool()
def extract_youtube_captions(video_url: str, language_preference: str = "en") -> dict[str, Any]:
    """Extract captions/subtitles from a YouTube video.
    
    Args:
        video_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
        language_preference: Preferred language code (e.g., 'en', 'es', 'fr'). Defaults to 'en'.
    
    Returns:
        Dictionary containing video information and captions data.
    """
    pass

# FastMCP automatically creates:
tool_metadata = {
    "name": "extract_youtube_captions",        # From function name
    "description": "Extract captions/subtitles...",  # From docstring
    "inputSchema": {                           # From type hints
        "type": "object",
        "properties": {
            "video_url": {
                "type": "string",              # From str type hint
                "title": "Video Url"
            },
            "language_preference": {
                "type": "string",              # From str type hint
                "title": "Language Preference",
                "default": "en"                # From default value
            }
        },
        "required": ["video_url"]              # Parameters without defaults
    }
}
```

### How Claude Forms JSON-RPC Calls

**When you say "Extract captions from this video", Claude:**

```python
# 1. Claude's AI reasoning:
# "User wants captions, I have extract_youtube_captions tool"

# 2. Claude looks at tool schema:
# - name: "extract_youtube_captions"  
# - required: ["video_url"]
# - optional: ["language_preference"]

# 3. Claude extracts parameters from your message:
# video_url = "https://youtu.be/abc123"
# language_preference = "en" (default or inferred)

# 4. Claude creates JSON-RPC call:
tool_call = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "extract_youtube_captions",
        "arguments": {
            "video_url": "https://youtu.be/abc123",
            "language_preference": "en"
        }
    },
    "id": 42
}

# 5. FastMCP receives this and calls your function:
# extract_youtube_captions(video_url="https://youtu.be/abc123", language_preference="en")
```

**The magic is in the schema matching** - Claude uses your function's type hints and docstring to understand exactly how to call your tools!

---

## 15. TCP/IP Visual Representation

**Question:** "Why TCP/IP is shown twice in the visual representation of HTTP"

**TCP/IP appears twice because it represents the SAME protocol stack on both ends:**

```python
# Why TCP/IP appears twice:
"""
[Client Side]          [Network]          [Server Side]
┌─────────────┐                          ┌─────────────┐
│ Application │                          │ Application │
│   (Browser) │                          │ (Web Server)│
├─────────────┤                          ├─────────────┤
│    HTTP     │                          │    HTTP     │
├─────────────┤                          ├─────────────┤
│    TCP      │ ←─── Network ────→       │    TCP      │
├─────────────┤                          ├─────────────┤
│     IP      │                          │     IP      │
├─────────────┤                          ├─────────────┤
│  Ethernet   │                          │  Ethernet   │
└─────────────┘                          └─────────────┘
      ↑                                         ↑
   Same stack                              Same stack
   on client                               on server
"""
```

**Both client and server need the full network stack:**

```python
# Client side (your browser):
browser_stack = {
    "Application": "Render webpage",
    "HTTP": "Format web requests", 
    "TCP": "Reliable delivery",
    "IP": "Routing across internet",
    "Ethernet": "Local network transmission"
}

# Server side (web server):
server_stack = {
    "Application": "Process web requests",
    "HTTP": "Parse web requests",
    "TCP": "Reliable delivery", 
    "IP": "Routing across internet",
    "Ethernet": "Local network transmission"
}

# The "TCP/IP" notation means both TCP AND IP layers
# Both sides need both layers to communicate
```

---

## 16. Additional Clarifications

### Question 1: Python Dict vs JSON String in Claude Desktop Communication

**Question:** "Could you explain what happens here, why is there dict and string both formats in claude desktop steps"

**The key insight: Programs work with objects internally, but can only send TEXT through pipes/networks.**

```python
# Step-by-step breakdown of what happens:

# STEP 1: Claude Desktop creates a Python dictionary (in memory)
request_data = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "extract_captions"},
    "id": 1
}
print(type(request_data))  # <class 'dict'>
print(request_data)        # {'jsonrpc': '2.0', 'method': 'tools/call', ...}

# STEP 2: Convert to JSON string (for transmission)
json_string = json.dumps(request_data)
print(type(json_string))   # <class 'str'>
print(json_string)         # '{"jsonrpc": "2.0", "method": "tools/call", ...}'

# STEP 3: Write string to stdin (only strings can go through pipes)
your_server_process.stdin.write(json_string.encode())  # Convert to bytes
your_server_process.stdin.write(b'\n')  # Add newline
your_server_process.stdin.flush()

# Why both formats?
# - Dict: Easy to work with in Python code (access fields, modify values)
# - String: Only format that can travel through stdin/stdout pipes
```

**Visual representation:**
```
Claude Desktop Memory:    {"method": "tools/call"}     (Python dict - easy to use)
                                    ↓ json.dumps()
Claude Desktop Buffer:    '{"method": "tools/call"}'   (JSON string - ready to send)
                                    ↓ write to stdin
Pipe (OS Kernel):         '{"method": "tools/call"}'   (Raw text bytes)
                                    ↓ read from stdout  
Your Server Buffer:       '{"method": "tools/call"}'   (JSON string - received)
                                    ↓ json.loads()
Your Server Memory:       {"method": "tools/call"}     (Python dict - easy to use)
```

**Why this conversion is necessary:**

```python
# You CANNOT send Python objects directly through pipes:
# process.stdin.write({"key": "value"})  # ❌ TypeError: dict not supported

# You CAN only send strings/bytes:
# process.stdin.write('{"key": "value"}')  # ✅ Works

# That's why every network/pipe communication requires serialization:
# Python Object → JSON String → Send → Receive → JSON String → Python Object
```

### Question 2: Significance of \r in HTTP Requests

**Question:** "What is the significance of \r in the request?"

**\r\n represents line endings in HTTP protocol - it's how HTTP separates different parts of the message.**

```python
# HTTP Protocol REQUIRES \r\n (CRLF - Carriage Return + Line Feed)
# This comes from old typewriter/terminal standards

# What \r and \n mean:
# \r = Carriage Return (move cursor to beginning of line)
# \n = Line Feed (move cursor down one line)
# \r\n = Complete line ending (move to beginning of next line)

# Example HTTP request breakdown:
http_request = """GET /api/data HTTP/1.1\r\nHost: example.com\r\nContent-Type: application/json\r\n\r\nRequest Body"""

# Let's break this down:
print(repr(http_request))
# 'GET /api/data HTTP/1.1\r\nHost: example.com\r\nContent-Type: application/json\r\n\r\nRequest Body'

# Each \r\n separates:
lines = http_request.split('\r\n')
print("Request Line:", lines[0])     # GET /api/data HTTP/1.1
print("Header 1:", lines[1])         # Host: example.com  
print("Header 2:", lines[2])         # Content-Type: application/json
print("Empty Line:", lines[3])       # (empty - separates headers from body)
print("Body:", lines[4])             # Request Body
```

**Why \r\n specifically?**

```python
# Different systems use different line endings:
# Unix/Linux:   \n   (just Line Feed)
# Windows:      \r\n (Carriage Return + Line Feed)  
# Old Mac:      \r   (just Carriage Return)

# HTTP standard chose \r\n for compatibility across all systems
# Web servers EXPECT \r\n - using just \n might cause issues

# Example of what happens with wrong line endings:
correct_request = "GET /api HTTP/1.1\r\nHost: example.com\r\n\r\n"
wrong_request = "GET /api HTTP/1.1\nHost: example.com\n\n"

# Some servers might:
# - Reject wrong_request entirely
# - Parse it incorrectly
# - Treat headers as part of the body
```

**Real example showing the difference:**

```python
import socket

def send_http_request(host, port, request):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.send(request.encode())
    response = sock.recv(1024).decode()
    sock.close()
    return response

# Correct HTTP request with \r\n:
correct = "GET / HTTP/1.1\r\nHost: httpbin.org\r\n\r\n"

# Incorrect request with just \n:
incorrect = "GET / HTTP/1.1\nHost: httpbin.org\n\n"

# The server expects \r\n format
```

### Question 3: POST Request Body Structure

**Question:** Looking at the POST request structure and asking for clarification.

**The structure shows how POST requests carry data in the body, separate from headers:**

```bash
# Complete POST request structure:
curl -X POST http://example.com/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "alice", "age": 25}'

# This creates the following raw HTTP request:
"""
POST /api/users HTTP/1.1\r
Host: example.com\r
Content-Type: application/json\r
Content-Length: 25\r
\r
{"name": "alice", "age": 25}
"""
```

**Breaking down each part:**

```python
# REQUEST LINE (what operation, where, which HTTP version)
"POST /api/users HTTP/1.1\r\n"
#  ^      ^          ^
#  |      |          HTTP version
#  |      Path on server
#  HTTP method

# HEADERS (metadata about the request)
"Host: example.com\r\n"                    # Which server
"Content-Type: application/json\r\n"       # What type of data in body
"Content-Length: 25\r\n"                   # How many bytes in body

# EMPTY LINE (required separator between headers and body)
"\r\n"

# BODY (the actual data being sent)
'{"name": "alice", "age": 25}'              # JSON payload
```

**Why POST uses body instead of URL:**

```python
# GET request - parameters in URL:
"GET /api/users?name=alice&age=25 HTTP/1.1\r\n"
# Problems: URL length limits, visible in logs, no complex data

# POST request - parameters in body:
"""
POST /api/users HTTP/1.1\r
Content-Type: application/json\r
\r
{"name": "alice", "age": 25, "address": {"street": "123 Main", "city": "NYC"}}
"""
# Advantages: No length limit, private, supports complex nested data
```

### Question 4: curl Command Line Options Explained

**Question:** "What does -X, -H and -d mean?"

**These are curl command-line flags that specify different parts of the HTTP request:**

```bash
curl -X POST http://example.com/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "alice", "age": 25}'
```

**Breaking down each flag:**

```bash
# -X METHOD (specify HTTP method)
-X POST        # Use POST method instead of default GET
-X GET         # Explicitly use GET (default)
-X PUT         # Use PUT method  
-X DELETE      # Use DELETE method
-X PATCH       # Use PATCH method

# Without -X, curl defaults to GET:
curl http://example.com              # Same as: curl -X GET http://example.com
```

```bash
# -H "Header: Value" (add HTTP headers)
-H "Content-Type: application/json"     # Tell server we're sending JSON
-H "Authorization: Bearer token123"     # Add authentication
-H "Accept: application/xml"            # Tell server we want XML response
-H "User-Agent: MyApp/1.0"             # Identify our application

# You can add multiple headers:
curl -H "Content-Type: application/json" \
     -H "Authorization: Bearer abc123" \
     -H "Accept: application/json" \
     http://example.com
```

```bash
# -d "data" (add data to request body)
-d '{"name": "alice"}'                   # Send JSON data
-d "name=alice&age=25"                   # Send form data
-d @filename.json                        # Send data from file

# When you use -d, curl automatically:
# 1. Changes method to POST (if not specified)
# 2. Adds Content-Length header
# 3. Sets Content-Type to application/x-www-form-urlencoded (unless overridden)
```

**Complete examples with explanations:**

```bash
# Example 1: Simple POST with JSON
curl -X POST \                           # Use POST method
     -H "Content-Type: application/json" \    # Tell server it's JSON
     -d '{"name": "alice"}' \            # Send this JSON data
     http://example.com/api/users

# Creates this HTTP request:
"""
POST /api/users HTTP/1.1
Host: example.com
Content-Type: application/json
Content-Length: 16

{"name": "alice"}
"""

# Example 2: GET with authentication header
curl -X GET \                            # Use GET method (optional)
     -H "Authorization: Bearer token123" \    # Add auth header
     http://example.com/api/users/123

# Creates this HTTP request:
"""
GET /api/users/123 HTTP/1.1
Host: example.com
Authorization: Bearer token123

"""

# Example 3: Multiple headers and form data
curl -X POST \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -H "Accept: application/json" \
     -d "username=alice&password=secret" \
     http://example.com/login

# Creates this HTTP request:
"""
POST /login HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded
Accept: application/json
Content-Length: 29

username=alice&password=secret
"""
```

**Summary of curl flags:**
- **-X**: What HTTP method to use (GET, POST, PUT, DELETE, etc.)
- **-H**: Add headers (metadata about the request)
- **-d**: Add data to the request body (automatically makes it POST)

---

## Summary - Key Architectural Insights

You now understand the fundamental differences between **network-based** and **process-based** communication:

### Network Communication (HTTP/HTTPS)
- **Data format**: Raw text HTTP requests with headers + body
- **Transport**: TCP/IP network stack with optional SSL encryption  
- **Discovery**: Manual URL knowledge or API documentation
- **Parameters**: URL query strings (GET) or request body (POST)
- **Tools**: curl, Postman, browsers can access

### Process Communication (MCP/JSON-RPC)
- **Data format**: JSON-RPC messages over stdin/stdout pipes
- **Transport**: OS kernel buffers (no network)
- **Discovery**: Automatic via `tools/list` method
- **Parameters**: Structured JSON in `params` field
- **Tools**: Only MCP clients (like Claude Desktop) can access

### The Magic of Your MCP Server
1. **FastMCP** automatically converts your Python functions into MCP tools
2. **Type hints** become JSON schema for parameter validation
3. **Docstrings** become tool descriptions for Claude's AI
4. **Claude's AI** uses schemas to form perfect JSON-RPC calls
5. **stdio pipes** enable secure, local-only communication

Your YouTube MCP server is essentially a **function library** that Claude can call through structured messaging - much more elegant than traditional HTTP APIs!

---

## References

- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **JSON-RPC 2.0 Specification**: https://www.jsonrpc.org/specification
- **HTTP/1.1 Specification**: https://tools.ietf.org/html/rfc7231
- **TCP/IP Protocol Suite**: https://tools.ietf.org/html/rfc793