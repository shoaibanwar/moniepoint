import os
import asyncio
import plyvel
import aiofiles 
from cachetools import LRUCache
from config import STORAGE_FILE, WAL_FILE, CACHE_SIZE
import logging
from typing import Optional, Dict, List

logging.basicConfig(level=logging.DEBUG)


class PersistentKVStore:
    """Persistent key-value store using RocksDB with write-ahead logging (WAL) and LRU cache."""

    def __init__(self) -> None:
        """Initialize the database, WAL file, and LRU cache."""
        self.db_path: str = STORAGE_FILE
        self.wal_path: str = WAL_FILE # write-ahead log file for recovery
        self.cache: LRUCache[str, str] = LRUCache(maxsize=CACHE_SIZE)  # In-memory LRU Cache
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.store: Optional[plyvel.DB] = None # plyvel instance for persistent storage

    async def _load_db(self)-> None:
        """Load the database if not already initialized."""

        if self.store is None:
            self.store = plyvel.DB(self.db_path, create_if_missing=True)

    async def put(self, key: str, value: str) -> str:
        """Write key-value pair to RocksDB, WAL, and LRU Cache."""
        await self._load_db()
        await self.loop.run_in_executor(None, self._sync_put, key, value)
        self.cache[key] = value  # Store in LRU cache

        # Append to Write-Ahead Log (WAL) for crash recovery
        async with aiofiles.open(self.wal_path, mode="a") as wal_file:
            await wal_file.write(f"Add == {key} {value}\n")

        logging.debug(f"PUT: {key} -> {value}")
        return "OK"
    
    def _sync_put(self, key: str, value: str) -> None:
        """Synchronous helper function to put data into DB."""
        self.store.put(key.encode(), value.encode())
    
    async def batch_put(self, keys: List[str], values: List[str]) -> str:  
        """Efficiently store multiple key-value pairs in RocksDB."""
        await self._load_db()
        await self.loop.run_in_executor(None, self._sync_batch_put, keys, values)

        wal_entries: List[str] = []
        for key, value in zip(keys, values):
            self.cache[key] = value  # Store in LRU cache
            wal_entries.append(f"Add == {key} {value}\n")  # Prepare WAL entry

        # Append batch writes to WAL file for crash recovery
        async with aiofiles.open(self.wal_path, mode="a") as wal_file:
            await wal_file.writelines(wal_entries)

        logging.debug(f"BATCH PUT: {dict(zip(keys, values))}")
        return "OK"
    
    def _sync_batch_put(self, keys: List[str], values: List[str]) -> None:
        """Synchronous helper function to perform batch put into Plyvel."""
        batch = self.store.write_batch()
        for key, value in zip(keys, values):
            batch.put(key.encode(), value.encode())
        batch.write()
    
    async def read(self, key: str) -> str:
        """Read from LRU cache first, then RocksDB if not found."""
        if key in self.cache:
            logging.debug(f"Cache HIT: {key}")
            return self.cache[key]

        await self._load_db()
        value = await self.loop.run_in_executor(None, self._sync_read, key)

        if value:
            self.cache[key] = value  # Store in LRU cache
            logging.debug(f"DB HIT: {key} -> {value}")
            return value

        logging.debug(f"Key NOT FOUND: {key}")
        return "Key not found"
    
    def _sync_read(self, key: str) -> Optional[str]:
        """Synchronous helper function to read data from Plyvel."""
        value = self.store.get(key.encode())
        if value:
            return value.decode()
        return None

    async def read_key_range(self, start_key: str, end_key: str)-> Dict[str, str]:
        """Retrieve values for keys within the specified range from RocksDB."""
        await self._load_db()
        result: Dict[str, str] = await self.loop.run_in_executor(None, self._sync_read_key_range, start_key, end_key)
        logging.debug(f"READ RANGE: {start_key} -> {end_key}: {result}")
        return result
    
    def _sync_read_key_range(self, start_key: str, end_key: str) -> Dict[str, str]:
        """Synchronous helper function to read key-range data from Plyvel."""
        result: Dict[str, str] = {}
        for key, value in self.store.iterator(start=start_key.encode(), include_value=True):
            key_str = key.decode()
            if key_str > end_key:
                break  # Stop scanning if we go beyond the end key
            if key_str >= start_key:
                result[key_str] = value.decode()
        return result

    async def delete(self, key: str) -> str:
        """Delete key from RocksDB, WAL, and LRU Cache."""
        await self._load_db()
        await self.loop.run_in_executor(None, self._sync_delete, key)
        self.cache.pop(key, None)  # Remove from cache

        # Append to Write-Ahead Log (WAL) for crash recovery
        async with aiofiles.open(self.wal_path, mode="a") as wal_file:
            await wal_file.write(f"Remove == {key} \n")

        logging.debug(f"DELETE: {key}")
        return "OK"
    
    def _sync_delete(self, key: str) -> None:
        """Synchronous helper function to delete data from Plyvel."""
        self.store.delete(key.encode())