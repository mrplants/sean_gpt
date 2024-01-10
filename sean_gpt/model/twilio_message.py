""" Twilio Message Model """
from typing import Optional, List
from pydantic import BaseModel, Field

class TwilioMessage(BaseModel):
    """
    Model for handling Twilio message data.
    Fields correspond to the data provided by Twilio's messaging service.
    """
    message_sid: str = Field(..., alias='MessageSid')
    sms_sid: str = Field(..., alias='SmsSid')
    account_sid: str = Field(..., alias='AccountSid')
    messaging_service_sid: str = Field(..., alias='MessagingServiceSid')
    from_: str = Field(..., alias='From')  # Note: 'from' is a reserved keyword in Python
    to: str = Field(..., alias='To')
    body: str = Field(..., alias='Body')
    num_media: int = Field(..., alias='NumMedia')
    media_content_type: Optional[List[str]] = Field(None, alias='MediaContentType')
    media_url: Optional[List[str]] = Field(None, alias='MediaUrl')
    from_city: Optional[str] = Field(None, alias='FromCity')
    from_state: Optional[str] = Field(None, alias='FromState')
    from_zip: Optional[str] = Field(None, alias='FromZip')
    from_country: Optional[str] = Field(None, alias='FromCountry')
    to_city: Optional[str] = Field(None, alias='ToCity')
    to_state: Optional[str] = Field(None, alias='ToState')
    to_zip: Optional[str] = Field(None, alias='ToZip')
    to_country: Optional[str] = Field(None, alias='ToCountry')
