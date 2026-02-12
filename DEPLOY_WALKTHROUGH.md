# Deploying miniOrange MCP Server with FastMCP

This guide explains how to deploy and run the miniOrange MCP server using the `fastmcp` library.

## Prerequisites

Ensure you have Python installed and the required dependencies:

```bash
pip install -r requirements.txt
```

This will install `fastmcp`, `mistralai`, `python-dotenv`, and other dependencies.

## Key Changes

1.  **New Server Implementation**: Created `fastmcp_app.py` which uses the `fastmcp` library to define the MCP server and tools. This replaces the complex manual implementation in `stdio_server.py` and the HTTP-based `server.py`.
2.  **Simplified Logic**: The server now directly exposes tools using the `@mcp.tool()` decorator, handling JSON-RPC automatically.
3.  **Updated Dependencies**: Added `fastmcp` to `requirements.txt`.

## Running the Server Locally

You can run the server directly from the command line:

```bash
python fastmcp_app.py
```

By default, this runs the server in standard input/output (stdio) mode, which is suitable for connecting to MCP clients like Claude Desktop.

## Connecting to Claude Desktop

To use this server with Claude Desktop, add the following configuration to your `claude_desktop_config.json`:

1.  Open or create `%APPDATA%\Claude\claude_desktop_config.json`.
2.  Add the `miniOrange` server configuration:

```json
{
  "mcpServers": {
    "miniOrange": {
      "command": "python",
      "args": [
        "c:\\Users\\miniOrange\\Desktop\\miniOrange-Fastmcp\\fastmcp_app.py"
      ],
      "env": {
        "MISTRAL_API_KEY": "your_actual_api_key_here"
      }
    }
  }
}
```

Make sure to replace `"your_actual_api_key_here"` with your valid Mistral API key if it's not set in your system environment variables.

## Testing with Inspector

You can also use the MCP Inspector to test the tools interactively:

```bash
npx @modelcontextprotocol/inspector python fastmcp_app.py
```

This will open a web interface where you can browse and call the available tools (`get_miniorange_guide`, `generate_walkthrough`, `search_docs`).
