from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from .config import settings

client = AsyncIOMotorClient(settings.database_url)
db = AIOEngine(client=client, database=settings.database_name)