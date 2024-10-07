
import os
from fastapi import APIRouter, status, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from app.routers.users import get_current_user
from typing import Annotated
import stripe
from app.utils import fulfill_checkout
from dotenv import load_dotenv
from ..app_data.schemas import UserAuthenticate


load_dotenv()
CLIENT_DOMAINS = os.getenv('CLIENT_DOMAIN').split(',')
WEBHOOK_SECRET_KEY = os.getenv('WEBHOOK_SECRET_KEY')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

router = APIRouter()

@router.post('/create-checkout-session/')
def create_checkout_session(
    current_user: Annotated[UserAuthenticate, Depends(get_current_user)],
    request: Request
):
    product_id = os.getenv('STRIPE_PRICE_ID')
    url = request.headers.get('X-Session-URL')
    if url.endswith('/'):
        url = url.rstrip('/')

    if not any(url.startswith(domain) for domain in CLIENT_DOMAINS):
        raise HTTPException(status_code=400, detail="Invalid return URL")

    try:
        session = stripe.checkout.Session.create(
            ui_mode = 'embedded',
            customer_email=current_user.email,
            line_items=[
                {
                    'price': product_id,
                    'quantity': 1,
                },
            ],
            mode='payment',
            # return_url=CLIENT_DOMAIN + '/checkout?session_id={CHECKOUT_SESSION_ID}',

            return_url=url + ('&' if '?' in url else '?') + 'session_id={CHECKOUT_SESSION_ID}',

            automatic_tax={'enabled': True},
        )
    except Exception as e:
        return str(e)

    return JSONResponse(status_code=status.HTTP_200_OK, content={"clientSecret": session.client_secret})

@router.get('/session-status')
def session_status(current_user: Annotated[UserAuthenticate, Depends(get_current_user)], session_id: str):
  session = stripe.checkout.Session.retrieve(session_id)

  return JSONResponse(status_code=status.HTTP_200_OK, content={"status": session.status, "customer_email": session.customer_details.email})




@router.post('/webhook')
async def webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET_KEY
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] in ['checkout.session.completed', 'checkout.session.async_payment_succeeded']:
        await fulfill_checkout.fulfill_checkout(event['data']['object']['id'])

    return JSONResponse(status_code=200, content={"message": "Webhook received"})