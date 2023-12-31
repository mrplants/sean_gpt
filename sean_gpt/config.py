from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv(dotenv_path="env/.env.backend_secrets")
load_dotenv(dotenv_path="env/.env.db_secrets")
load_dotenv(dotenv_path="env/.env.local")
load_dotenv(dotenv_path="env/.env")

# In a production environment, there will be no .env or .env.secrets files,
# and the values will be set by the environment variables

class Settings(BaseSettings):
    debug: bool = False

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    verification_token_expire_minutes: int
    
    admin_phone: str
    admin_password: str

    api_db_dialect: str
    api_db_driver: str
    api_db_host: str
    api_db_port: str
    api_db_name: str
    api_db_user: str
    api_db_password: str

    redis_host: str

    openai_api_url: str
    openai_api_key: str

    twilio_test_sid: str
    twilio_test_auth_token: str
    twilio_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    twilio_welcome_message: str
    twilio_request_referral_message: str
    twilio_only_sms_message: str

    chat_history_length: int

settings = Settings()

class Constants(BaseSettings):
    phone_verification_message: str

constants = Constants()