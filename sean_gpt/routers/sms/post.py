from fastapi import APIRouter, Request, HTTPException
from twilio.request_validator import RequestValidator

from ...config import settings

router = APIRouter(
    prefix="/sms",
    tags=["SMS"],
)

@router.post("/")
async def twilio_webhook(request: Request):
    """
    Endpoint to receive Twilio webhooks.

    Validates the incoming request to ensure it's from Twilio and then responds with a static message.

    Args:
        request (Request): The request object containing the data sent by Twilio.

    Returns:
        JSONResponse: A static response message.
    """
    validator = RequestValidator(settings.twilio_auth_token)

    # Prepare validation
    form_data = await request.form()
    request_url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")

    # Validate the request
    if not validator.validate(request_url, form_data, signature):
        raise HTTPException(status_code=400, detail="Invalid request signature")

    # Process the valid request here
    print("Validated Twilio request:", form_data)

    # Respond with a static message
    return {"message": "Received your request!"}