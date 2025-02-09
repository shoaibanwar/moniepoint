import os
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()

# Database file for persistent storage
STORAGE_FILE: str = os.getenv("STORAGE_FILE", "/data/kvstore.db")

# Write-Ahead Log (WAL) file for crash recovery
WAL_FILE: str = os.getenv("WAL_FILE", "/data/kvstore.wal")

# LRU Cache size for optimizing read performance
CACHE_SIZE: int = int(os.getenv("CACHE_SIZE", 1000))  # LRU Cache size

# Get replica nodes
REPLICAS: List[str] = os.getenv("REPLICAS", "").split(",")