from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv(dotenv_path="env/.env.secrets")
load_dotenv(dotenv_path="env/.env.local")
load_dotenv(dotenv_path="env/.env")

# In a production environment, there will be no .env or .env.secrets files,
# and the values will be set by the environment variables

class Settings(BaseSettings):
    secret_key: str
    openai_api_key: str
    database_name: str
    database_url: str
    algorithm: str
    openai_api_url: str
    access_token_expire_minutes: int

settings = Settings()