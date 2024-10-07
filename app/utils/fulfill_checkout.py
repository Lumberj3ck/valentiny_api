import stripe
import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.app_data import crud, models
from dotenv import load_dotenv
from app.dependencies import get_db

load_dotenv()

stripe.api_key = 'sk_test_51Ncm9BGG1bSL8LD46f2FvpybkOVix2n625jJhyJBTXY3MxFb3fmklHb13CJFXpfXMeglmZbOco1yq8pkcTDIshIm00lQku1pCA'

async def fulfill_checkout(session_id: str):
    print("Fulfilling Checkout Session", session_id)
    product_id = os.getenv('STRIPE_PRODUCT_ID')

    db = next(get_db())

    # Make this function safe to run multiple times, even concurrently
    try:
        # Check if fulfillment has already been performed
        existing_fulfillment = crud.get_fulfillment_by_session_id(db, session_id)
        if existing_fulfillment:
            print(f"Fulfillment already performed for session {session_id}")
            return

        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=['line_items']
        )

        if session.payment_status != 'unpaid':
            for item in session.line_items.data:
                if item.price.product == product_id:
                    crud.grant_user_website_upload(db, session.customer_details.email, item.quantity)

                print(f"Fulfilling item: {item.description}")

            fulfillment = models.Fulfillment(
                session_id=session_id,
                status='completed',
                customer_email=session.customer_details.email
            )
            db.add(fulfillment)
            db.commit()

            print(f"Fulfillment completed for session {session_id}")
        else:
            print(f"Payment not completed for session {session_id}")

    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error fulfilling checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()