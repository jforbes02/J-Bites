import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
)

TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


def send_sms(to_phone: str, message: str):
    """
    Send SMS from your Twilio number to customer's number

    Args:
        to_phone: Customer's phone (e.g., "555-1234" or "+15551234567")
        message: Text message to send
    """
    try:
        # Format customer's phone number (add +1 for US)
        if not to_phone.startswith('+'):
            # Remove dashes, spaces, parentheses from #
            clean_phone = to_phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            to_phone = f'+1{clean_phone}'

        # Sends SMS FROM Twilio # to customer
        msg = client.messages.create(
            to=to_phone,  # Customer's phone
            from_=TWILIO_NUMBER,  # Twilio number
            body=message
        )

        print(f"✅ SMS sent to {to_phone}")
        print(f"   Message SID: {msg.sid}")
        return msg.sid

    except Exception as e:
        print(f"❌ Failed to send SMS: {str(e)}")
        return None


# Your notification functions (unchanged)
def notify_order_confirmed(phone: str, order_id: int, total: float):
    message = f"🍔 J-Bites Order #{order_id} confirmed! Total: ${total:.2f}. We're preparing your food!"
    return send_sms(phone, message)


def notify_order_ready(phone: str, order_id: int):
    message = f"✅ Your J-Bites order #{order_id} is ready for pickup!"
    return send_sms(phone, message)


def notify_order_cancelled(phone: str, order_id: int, refund: float = None):
    if refund:
        message = f"✅ J-Bites order #{order_id} cancelled. Refund of ${refund:.2f} has been processed to your original payment method. Please allow 5-10 business days."
    else:
        message = f"❌ J-Bites order #{order_id} cancelled."
    return send_sms(phone, message)
