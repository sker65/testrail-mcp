"""Simple script to test the TestRail MCP server."""
import json
import subprocess
import sys

def test_mcp_server():
    """Test the TestRail MCP server by sending some basic commands."""
    # Start the MCP server as a subprocess
    process = subprocess.Popen(
        ["python", "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Send an initialize message
    initialize_message = {"type": "initialize"}
    print(f"Sending: {json.dumps(initialize_message)}")
    process.stdin.write(json.dumps(initialize_message) + "\n")
    process.stdin.flush()
    
    # Read the response
    response = json.loads(process.stdout.readline())
    print(f"Received: {json.dumps(response, indent=2)}")
    
    # Send a list_tools message
    list_tools_message = {"type": "list_tools"}
    print(f"Sending: {json.dumps(list_tools_message)}")
    process.stdin.write(json.dumps(list_tools_message) + "\n")
    process.stdin.flush()
    
    # Read the response
    response = json.loads(process.stdout.readline())
    print(f"Received: {json.dumps(response, indent=2)}")
    
    # Clean up
    process.terminate()
    process.wait()

if __name__ == "__main__":
    test_mcp_server()
