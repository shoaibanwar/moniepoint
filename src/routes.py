from fastapi import FastAPI, Query
import asyncio
from storage import PersistentKVStore
from replication import ReplicationManager
from pydantic import BaseModel
from typing import List
from typing import List, Dict, Any


class KeyValuePair(BaseModel):
    key: str
    value: str

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI()
    store = PersistentKVStore()
    replication_manager = ReplicationManager()

    @app.post("/put")
    async def put(data: KeyValuePair, replication: bool = Query(False)) -> Dict[str, Any]:
        """
        Store a single key-value pair in RocksDB.

        - `data`: JSON body containing the `key` and `value`.
        - `replication`: If `True`, this request is a replication request.
        """
        key, value = data.key, data.value

        if not key or not value:
            return {"error": "Key and Value are required"}, 400
        
        result: str = await store.put(key, value)

        # Replicate only if it's NOT a replication request
        if not replication:
            asyncio.create_task(replication_manager.replicate("put", data.dict()))
        return {"status": result}

    @app.get("/read/{key}")
    async def read(key: str) -> Dict[str, Any]:
        """
        Retrieve a value from RocksDB by key.

        - `key`: The key to look up.
        """
        value: str = await store.read(key)
        return {"value": value}

    @app.get("/readrange")
    async def read_range(start_key: str, end_key: str) -> Dict[str, str]:
        """
        Retrieve all key-value pairs within a specified range.

        - `start_key`: The start of the key range.
        - `end_key`: The end of the key range.
        """
        if not start_key or not end_key:
            return {"error": "Invalid request, missing start_key or end_key"}, 400

        result: Dict[str, str] = await store.read_key_range(start_key, end_key)
        return result

    @app.post("/batchput")
    async def batch_put(data: List[KeyValuePair], replication: bool = Query(False)) -> Dict[str, Any]:
        """
        Store multiple key-value pairs in RocksDB efficiently.

        - `data`: A list of `KeyValuePair` objects.
        - `replication`: If `True`, this request is a replication request.
        """
        keys = [item.key for item in data]
        values = [item.value for item in data]

        if not keys or not values or len(keys) != len(values):
            return {"error": "Invalid request, keys and values must be lists of the same length"}, 400

        response: str = await store.batch_put(keys, values)

        if not replication:
            asyncio.create_task(replication_manager.replicate("batchput", [item.dict() for item in data]))

        return {"message": response}

    @app.post("/delete")
    async def delete(data:  Dict[str, str], replication: bool = Query(False)) -> Dict[str, Any]:
        """
        Delete a key from RocksDB.

        - `data`: JSON body containing the `key`.
        - `replication`: If `True`, this request is a replication request.
        """
        key = data.get("key")
        if not key:
            return {"error": "Key is required"}, 400
        
        result: str = await store.delete(key)

        if not replication:
            asyncio.create_task(replication_manager.replicate("delete", {"key": key})) 
        return {"status": result}

    return app
