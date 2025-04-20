# TestRail MCP Server

[![smithery badge](https://smithery.ai/badge/@sker65/testrail-mcp)](https://smithery.ai/server/@sker65/testrail-mcp)

A Model Context Protocol (MCP) server for TestRail that allows interaction with TestRail's core entities through a standardized protocol.

## Features

- Authentication with TestRail API
- Access to TestRail entities:
  - Projects
  - Cases
  - Runs
  - Results
  - Datasets
- Full support for the Model Context Protocol
- Compatible with any MCP client (Claude Desktop, Cursor, Winsurf, etc.)

## Installation

### Installing via Smithery

To install testrail-mcp for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@sker65/testrail-mcp):

```bash
npx -y @smithery/cli install @sker65/testrail-mcp --client claude
```

### Manual Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/testrail-mcp.git
   cd testrail-mcp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

## Configuration

The TestRail MCP server requires specific environment variables to authenticate with your TestRail instance. These must be set before running the server.

1. Create a `.env` file in the root directory of the project:
   ```
   TESTRAIL_URL=https://your-instance.testrail.io
   TESTRAIL_USERNAME=your-email@example.com
   TESTRAIL_API_KEY=your-api-key
   ```

   **Important Notes:**
   - `TESTRAIL_URL` should be the full URL to your TestRail instance (e.g., `https://example.testrail.io`)
   - `TESTRAIL_USERNAME` is your TestRail email address used for login
   - `TESTRAIL_API_KEY` is your TestRail API key (not your password)
     - To generate an API key, log in to TestRail, go to "My Settings" > "API Keys" and create a new key

2. Verify that the configuration is loaded correctly:
   ```bash
   uvx testrail-mcp --config
   ```
   
   This will display your TestRail configuration information, including your URL, username, and the first few characters of your API key for verification.

If you're using this server with a client like Claude Desktop or Cursor, make sure the environment variables are accessible to the process running the server. You may need to set these variables in your system environment or ensure they're loaded from the `.env` file.

## Usage

### Running the Server

The server can be run directly using the installed script:

```bash
uvx testrail-mcp
```

This will start the MCP server in stdio mode, which can be used with MCP clients that support stdio communication.

### Using with MCP Clients

#### Claude Desktop

In Claude Desktop, add a new server with the following configuration:

```json
{
  "mcpServers": {
    "testrail": {
      "command": "uvx",
      "args": [
        "testrail-mcp"
      ],
      "env": {
        "TESTRAIL_URL": "https://your-instance.testrail.io",
        "TESTRAIL_USERNAME": "your-email@example.com",
        "TESTRAIL_API_KEY": "your-api-key"
      }
    }
  }
}
```

#### Cursor

In Cursor, add a new custom tool with the following configuration:

```json
{
  "name": "TestRail MCP",
  "command": "uvx",
  "args": [
    "testrail-mcp"
  ],
  "communication": "stdio",
  "env": {
    "TESTRAIL_URL": "https://your-instance.testrail.io",
    "TESTRAIL_USERNAME": "your-email@example.com",
    "TESTRAIL_API_KEY": "your-api-key"
  }
}
```

#### Winsurf

In Winsurf, add a new tool with the following configuration:

```json
{
  "name": "TestRail MCP",
  "command": "uvx",
  "args": [
    "testrail-mcp"
  ],
  "protocol": "mcp",
  "env": {
    "TESTRAIL_URL": "https://your-instance.testrail.io",
    "TESTRAIL_USERNAME": "your-email@example.com",
    "TESTRAIL_API_KEY": "your-api-key"
  }
}
```

#### Testing with MCP Inspector

For testing and debugging, you can use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector \
  -e TESTRAIL_URL=<your-url> \
  -e TESTRAIL_USERNAME=<your-username> \
  -e TESTRAIL_API_KEY=<your-api-key> \
  uvx testrail-mcp
```

This will open a web interface where you can explore and test all the available tools and resources.

## Development

This server is built using:

- [FastMCP](https://github.com/jlowin/fastmcp) - A Python framework for building MCP servers
- [Requests](https://requests.readthedocs.io/) - For HTTP communication with TestRail API
- [python-dotenv](https://github.com/theskumar/python-dotenv) - For environment variable management

## License

MIT
