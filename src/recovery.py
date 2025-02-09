import os
import asyncio
import aiofiles
import logging
from storage import PersistentKVStore  # Import the KV Store

# Configure logging for recovery process
logging.basicConfig(level=logging.INFO)

class WALRecovery:
    """Handles Write-Ahead Log (WAL) recovery to restore lost writes after a crash."""

    def __init__(self) -> None:
        """Initialize WALRecovery with its own PersistentKVStore and event loop."""
        self.store: PersistentKVStore = PersistentKVStore() 
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.wal_path: str = self.store.wal_path 

    async def recover_from_wal(self) -> None:
        """Replay WAL entries to restore lost writes after a crash."""
        await self.store._load_db()

        if not os.path.exists(self.wal_path):
            logging.info("No WAL file found. Skipping recovery.")
            return

        async with aiofiles.open(self.wal_path, mode="r") as wal_file:
            async for line in wal_file:
                parts: list[str] = line.strip().split(" == ", 1)

                if len(parts) != 2:
                    logging.warning(f"Skipping malformed WAL entry: {line.strip()}")
                    continue

                action, key_value = parts

                if action == "Add":
                    key, value = key_value.split(" ", 1)
                    await self.loop.run_in_executor(None, self.store._sync_put, key, value)
                elif action == "Remove":
                    key = key_value.strip()
                    await self.loop.run_in_executor(None, self.store._sync_delete, key)
                else:
                    logging.warning(f"Unknown WAL action: {action}")

        logging.info("Successfully recovered from WAL.")

    def run_recovery(self) -> None:
        """Start WAL recovery in an asynchronous event loop."""
        logging.info("Starting WAL recovery process...")
        self.loop.run_until_complete(self.recover_from_wal())

# Run WAL recovery when this script is executed
if __name__ == "__main__":
    recovery: WALRecovery = WALRecovery()
    recovery.run_recovery()
