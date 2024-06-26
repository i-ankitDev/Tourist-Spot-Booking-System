import random
from twilio.rest import Client

def generate_otp(length=6):
    """Generate a random OTP of the specified length."""
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

def send_otp_via_sms(mobile_number, otp):
    """Send an OTP to the specified mobile number using Twilio."""
  
    
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        body=f"Your Admin OTP for login is: {otp}",
        from_=twilio_phone_number,
        to=mobile_number
    )
    
    return message.sid


