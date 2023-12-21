from .config import settings

from sqlmodel import Field, SQLModel, create_engine


client = AsyncIOMotorClient(settings.database_url)
db = AIOEngine(client=client, database=settings.database_name)