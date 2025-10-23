from pymongo import MongoClient
from app.config import settings
import asyncio

class MongoDB:
    def __init__(self):
        self.client = None
        self.database = None

    def connect(self):
        if self.client is None:
            self.client = MongoClient(settings.MONGODB_URL)
            self.database = self.client[settings.DATABASE_NAME]
            print("✅ Connected to MongoDB")

    def get_collection(self, collection_name: str):
        if self.database is None:
            self.connect()
        return self.database[collection_name]

    def close(self):
        if self.client:
            self.client.close()
            print("❌ Disconnected from MongoDB")

# Global MongoDB instance
mongodb = MongoDB()

# Async wrapper for database operations
async def run_async(func, *args):
    return await asyncio.get_event_loop().run_in_executor(None, func, *args)
