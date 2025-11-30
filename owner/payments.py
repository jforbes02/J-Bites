import os
import stripe
from dotenv import load_dotenv
load_dotenv()
stripe.api_key = os.getenv('SECRET_STR_KEY')

class StripeService:
    @staticmethod
    def create_checkout(order_id: int, items: list, phone:str, success_url:str, cancel_url:str) -> str:
        try:
            line_items = []
            for item in items:
                line_items.append({
                    'price_data':{
                        'currency': 'USD',
                        'product_data':{
                            'name': item['name'],
                        },
                        'unit_amount': int(item['price'] * 100),
                    },
                    'quantity': item['quantity'],
                })
            session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=line_items,
                    mode='payment',
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata={
                        'phone': phone,
                        'order_id': order_id
                    }
                )
            return session.url
        except stripe.error.StripeError as e:
            raise Exception(f"Checkout creation failed: {e}")

    @staticmethod
    def create_refund(pay_intent_id: str):
        try:
            refund = stripe.Refund.create(
                payment_intent=pay_intent_id
            )
            return refund.amount / 100
        except stripe.error.StripeError as e:
            raise Exception(f"Refund creation failed: {e}")