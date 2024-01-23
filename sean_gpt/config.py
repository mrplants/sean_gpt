""" Configuration for the app. """
import os

from pydantic_settings import BaseSettings
from pydantic import Field

if 'SEAN_GPT_DEBUG' not in os.environ:
    os.environ['SEAN_GPT_DEBUG'] = 'False'

class Settings(BaseSettings):
    """ Configuration for the app. """
    debug: bool|None = Field(alias='SEAN_GPT_DEBUG')

    # SECRETS
    # Values from secrets need default values for testing because we do not load
    # the secrets file in testing
    jwt_secret_key: str = Field(alias='sean_gpt_jwt_secret_key')
    api_db_user: str = Field(alias='sean_gpt_api_db_user')
    api_db_password: str = Field(alias='sean_gpt_api_db_password')
    openai_api_key: str = Field(alias='sean_gpt_openai_api_key')
    user_admin_phone: str = Field(alias='sean_gpt_user_admin_phone')
    user_admin_password: str = Field(alias='sean_gpt_user_admin_password')
    twilio_test_sid: str = Field( alias='sean_gpt_twilio_test_sid')
    twilio_test_auth_token: str = Field(alias='sean_gpt_twilio_test_auth_token')
    twilio_sid: str = Field( alias='sean_gpt_twilio_sid')
    twilio_auth_token: str = Field(alias='sean_gpt_twilio_auth_token')
    minio_access_key: str = Field(alias='sean_gpt_minio_access_key')
    minio_secret_key: str = Field(alias='sean_gpt_minio_secret_key')

    # NOT SECRETS
    openai_api_url: str = Field(alias='sean_gpt_openai_api_url')

    jwt_algorithm: str = Field(alias='sean_gpt_jwt_algorithm')
    jwt_access_token_expire_minutes: int = Field(alias='sean_gpt_jwt_access_token_expire_minutes')
    jwt_verification_token_expire_minutes: int = (
        Field(alias='sean_gpt_jwt_verification_token_expire_minutes'))

    database_dialect: str = Field(alias='sean_gpt_database_dialect')
    database_driver: str = Field(alias='sean_gpt_database_driver')
    database_host: str = Field(alias='sean_gpt_database_host')
    database_port: str = Field(alias='sean_gpt_database_port')
    database_name: str = Field(alias='sean_gpt_database_name')

    redis_host: str = Field(alias='sean_gpt_redis_host')

    minio_host: str = Field(alias='sean_gpt_minio_host')
    minio_port: str = Field(alias='sean_gpt_minio_port')

    kafka_brokers: str = Field(alias='sean_gpt_kafka_brokers')

    app_phone_number: str = Field(alias='sean_gpt_app_phone_number')
    app_welcome_message: str = Field(alias='sean_gpt_app_welcome_message')
    app_request_referral_message: str = Field(alias='sean_gpt_app_request_referral_message')
    app_no_whatsapp_message: str = Field(alias='sean_gpt_app_no_whatsapp_message')
    app_no_mms_message: str = Field(alias='sean_gpt_app_no_mms_message')
    app_sms_opt_in_message: str = Field(alias='sean_gpt_app_sms_opt_in_message')
    app_ai_system_message: str = Field(alias='sean_gpt_app_ai_system_message')
    app_max_sms_characters: int = Field(alias='sean_gpt_app_max_sms_characters')
    app_chat_history_length: int = Field(alias='sean_gpt_app_chat_history_length')
    app_default_ai_model: str = Field(alias='sean_gpt_app_default_ai_model')
    app_phone_verification_message: str = Field(alias='sean_gpt_app_phone_verification_message')
    app_ws_token_timeout_seconds: int = Field(alias='sean_gpt_app_ws_token_timeout_seconds')

settings = Settings()
