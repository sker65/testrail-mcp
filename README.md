# TestRail MCP Server

This is a Model Context Protocol (MCP) server for TestRail that allows you to interact with TestRail through LLM applications. The server supports authentication and provides tools for working with TestRail entities including cases, runs, datasets, and results.

## Setup

1. Install dependencies using `uv`:
   ```
   uv pip install -e .
   ```

   If you don't have `uv` installed, you can install it following the instructions at [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).

2. Create a `.env` file with your TestRail credentials:
   ```
   TESTRAIL_URL=https://your-instance.testrail.io
   TESTRAIL_USERNAME=your-email@example.com
   TESTRAIL_API_KEY=your-api-key
   ```

3. Run the server:
   ```
   python main.py
   ```

   This will start the MCP server in stdio mode, which can be used with MCP clients that support stdio communication.

## Using with MCP Clients

This server implements the Model Context Protocol (MCP) over stdio, making it compatible with various MCP clients:

- **Claude Desktop**: You can install this server in Claude Desktop using the "Install Server" feature
- **MCP Inspector**: For testing, you can use the MCP Inspector tool with the `--stdio` flag
- **Other MCP Clients**: Any client that supports the MCP protocol over stdio can connect to this server

## Features

- Authentication with TestRail
- Access to TestRail cases, runs, datasets, projects and results
- Full support for the Model Context Protocol
