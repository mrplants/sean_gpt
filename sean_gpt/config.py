from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv(dotenv_path="env/.env.backend_secrets")
load_dotenv(dotenv_path="env/.env.db_secrets")
load_dotenv(dotenv_path="env/.env.local")
load_dotenv(dotenv_path="env/.env")

# In a production environment, there will be no .env or .env.secrets files,
# and the values will be set by the environment variables

class Settings(BaseSettings):
    secret_key: str
    openai_api_key: str
    algorithm: str
    openai_api_url: str
    access_token_expire_minutes: int
    debug: bool = False
    admin_phone: str
    admin_password: str
    api_db_dialect: str
    api_db_driver: str
    api_db_host: str
    api_db_port: str
    api_db_name: str
    api_db_user: str
    api_db_password: str

settings = Settings()