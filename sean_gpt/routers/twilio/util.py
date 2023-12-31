from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator

from ...config import settings

async def validate_twilio(request: Request):
    validator = RequestValidator(settings.twilio_auth_token)

    # Get the full URL that Twilio requested
    url = str(request.url)

    # Get the POST parameters
    form = await request.form()
    parameters = dict(form)

    # Get the signature from the `X-Twilio-Signature` header
    signature = request.headers.get('X-Twilio-Signature', '')

    # Validate the request
    if not validator.validate(url, parameters, signature):
        raise HTTPException(status_code=400, detail="Invalid Twilio Signature")
