"""Configuration module for TestRail MCP server."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# TestRail configuration
TESTRAIL_URL = os.getenv('TESTRAIL_URL')
TESTRAIL_USERNAME = os.getenv('TESTRAIL_USERNAME')
TESTRAIL_API_KEY = os.getenv('TESTRAIL_API_KEY')

# HTTP tuning (optional). Timeouts are in seconds.
TESTRAIL_CONNECT_TIMEOUT = float(os.getenv('TESTRAIL_CONNECT_TIMEOUT', '10'))
TESTRAIL_READ_TIMEOUT = float(os.getenv('TESTRAIL_READ_TIMEOUT', '60'))
TESTRAIL_MAX_RETRIES = int(os.getenv('TESTRAIL_MAX_RETRIES', '3'))
TESTRAIL_BACKOFF_BASE = float(os.getenv('TESTRAIL_BACKOFF_BASE', '1'))

# Validate configuration
if not all([TESTRAIL_URL, TESTRAIL_USERNAME, TESTRAIL_API_KEY]):
    raise ValueError(
        "Missing TestRail configuration. Please set TESTRAIL_URL, "
        "TESTRAIL_USERNAME, and TESTRAIL_API_KEY environment variables."
    )