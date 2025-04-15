# TestRail MCP Server

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
   python -c "from testrail_mcp.config import TESTRAIL_URL, TESTRAIL_USERNAME, TESTRAIL_API_KEY; print(f'URL: {TESTRAIL_URL}, Username: {TESTRAIL_USERNAME}, API Key: {TESTRAIL_API_KEY[:5]}...')"
   ```
   
   This should print your TestRail URL, username, and the first few characters of your API key.

If you're using this server with a client like Claude Desktop or Cursor, make sure the environment variables are accessible to the process running the server. You may need to set these variables in your system environment or ensure they're loaded from the `.env` file.

## Usage

### Running the Server

```bash
python main.py
```

This will start the MCP server in stdio mode, which can be used with MCP clients that support stdio communication.

### Using with MCP Clients

#### Claude Desktop

1. Open Claude Desktop
2. Go to Settings > Servers
3. Click "Install Server"
4. Navigate to your project directory and select the `main.py` file
5. Claude Desktop will now be able to use your TestRail MCP server

#### Cursor

1. Open Cursor
2. Go to Settings > AI > Custom Tools
3. Click "Add Tool"
4. Configure the tool:
   - Name: TestRail MCP
   - Command: `python /path/to/testrail-mcp/main.py`
   - Communication: Stdio
5. Save the configuration

#### Winsurf

1. Open Winsurf
2. Go to Settings > Tools
3. Click "Add Tool"
4. Configure the tool:
   - Name: TestRail MCP
   - Command: `python /path/to/testrail-mcp/main.py`
   - Protocol: MCP
5. Save the configuration

#### Testing with MCP Inspector

For testing and debugging, you can use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector stdio -- python main.py
```

This will open a web interface where you can explore and test all the available tools and resources.

## Development

This server is built using:

- [FastMCP](https://github.com/jlowin/fastmcp) - A Python framework for building MCP servers
- [Requests](https://requests.readthedocs.io/) - For HTTP communication with TestRail API
- [python-dotenv](https://github.com/theskumar/python-dotenv) - For environment variable management

## License

MIT
