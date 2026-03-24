import json
import os
import asyncio
from typing import Any

# =========================
# OPTIONAL MONGO
# =========================
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

MONGO_URI = os.getenv("MONGO_URI", "")


# =========================
# JSON DATABASE
# =========================
class JSONDatabase:
    def __init__(self, filename="userbot.db.json"):
        self.filename = filename
        self._lock = asyncio.Lock()
        self._cache = None

    async def _load(self):
        async with self._lock:
            if self._cache is not None:
                return self._cache

            if os.path.exists(self.filename):
                try:
                    with open(self.filename, "r") as f:
                        self._cache = json.load(f)
                except Exception:
                    self._cache = {}
            else:
                self._cache = {}

            return self._cache

    async def _save(self, data):
        async with self._lock:
            self._cache = data
            with open(self.filename, "w") as f:
                json.dump(data, f, indent=2)

    async def get(self, collection, key, default=None):
        data = await self._load()
        return data.get(collection, {}).get(key, default)

    async def set(self, collection, key, value):
        data = await self._load()

        if collection not in data:
            data[collection] = {}

        data[collection][key] = value
        await self._save(data)

    async def delete(self, collection, key):
        data = await self._load()

        if collection in data and key in data[collection]:
            del data[collection][key]
            await self._save(data)

    async def keys(self, collection):
        data = await self._load()
        return list(data.get(collection, {}).keys())

    async def get_collection(self, collection):
        data = await self._load()
        return data.get(collection, {})


# =========================
# MONGO DATABASE
# =========================
class MongoDatabase:
    def __init__(self, uri: str):
        self.client = AsyncIOMotorClient(uri)

        if "/" in uri.rsplit("/", 1)[-1]:
            self.db = self.client.get_default_database()
        else:
            self.db = self.client["userbot"]

        self.collections = {}

    async def _get_collection(self, name):
        if name not in self.collections:
            self.collections[name] = self.db[name]
        return self.collections[name]

    async def get(self, collection, key, default=None):
        coll = await self._get_collection(collection)
        doc = await coll.find_one({"_id": key})
        return doc["value"] if doc else default

    async def set(self, collection, key, value):
        coll = await self._get_collection(collection)
        await coll.update_one(
            {"_id": key},
            {"$set": {"value": value}},
            upsert=True
        )

    async def delete(self, collection, key):
        coll = await self._get_collection(collection)
        await coll.delete_one({"_id": key})

    async def keys(self, collection):
        coll = await self._get_collection(collection)
        return [doc["_id"] async for doc in coll.find()]

    async def get_collection(self, collection):
        coll = await self._get_collection(collection)
        result = {}
        async for doc in coll.find():
            result[doc["_id"]] = doc["value"]
        return result


# =========================
# SELECT BACKEND
# =========================
if MONGO_URI and MONGO_AVAILABLE:
    _db = MongoDatabase(MONGO_URI)
else:
    _db = JSONDatabase()


# =========================
# PUBLIC API
# =========================
async def get(collection: str, key: str, default=None):
    return await _db.get(collection, key, default)


async def set(collection: str, key: str, value: Any):
    await _db.set(collection, key, value)


async def delete(collection: str, key: str):
    await _db.delete(collection, key)


async def keys(collection: str):
    return await _db.keys(collection)


async def get_collection(collection: str):
    return await _db.get_collection(collection)


# =========================
# DEFAULT COLLECTION
# =========================
store_col = "stored_data"