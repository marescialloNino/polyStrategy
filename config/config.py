import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_PATH = "polymarket_data.db"

# WebSocket Publisher Configuration
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8765

# ClobClient API Credentials
CLOB_HOST = "http://localhost:8080"  # Adjust if needed
API_KEY = os.getenv("CLOB_API_KEY")
PRIVATE_KEY = os.getenv("PK")
