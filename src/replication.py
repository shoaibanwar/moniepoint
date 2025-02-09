import aiohttp
import asyncio
import logging
import config
from typing import Union, List, Dict, Any

logging.basicConfig(level=logging.INFO)

class ReplicationManager:
    """Handles asynchronous replication of key-value operations to other nodes."""

    def __init__(self) -> None:
        """Initialize the replication manager with a list of replicas."""
        self.replicas = config.REPLICAS

    async def replicate(self, endpoint: str, json_data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> None:
        """Asynchronously send requests to all replica nodes for consistency."""
        async def send_request(replica: str) -> None:
            url: str = f"http://{replica}/{endpoint}?replication=true"
            logging.info(f"Trying to replicate {url}")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=json_data, timeout=5) as response:
                        if response.status == 200:
                            logging.info(f"Successfully replicated to {replica}")
                        else:
                            logging.warning(f"Replication to {replica} failed with status {response.status}")
            except Exception as e:
                logging.error(f"Failed to replicate to {replica}: {e}")

        # Run replication requests in parallel
        await asyncio.gather(*(send_request(replica) for replica in self.replicas))