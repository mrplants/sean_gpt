from .config import settings
from sqlmodel import create_engine, Session, select
from .model.authentication.user import UserData

# dialect+driver://username:password@host:port/database
database_url = f"{settings.api_db_dialect}{settings.api_db_driver}://{settings.api_db_user}:{settings.api_db_password}@{settings.api_db_host}:{settings.api_db_port}/{settings.api_db_name}"
print(database_url)
db_engine = create_engine(database_url, echo=settings.debug)