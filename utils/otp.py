import random
from twilio.rest import Client

def generate_otp(length=6):
    """Generate a random OTP of the specified length."""
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

def send_otp_via_sms(mobile_number, otp):
    """Send an OTP to the specified mobile number using Twilio."""
    account_sid = 'ACf2e79a2369886dd66c1bf8a4c01657ec'
    auth_token = '9e9e917a452407df36eddcf41e8149cf'
    twilio_phone_number = '+12568261642'
    
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        body=f"Your Admin OTP for login is: {otp}",
        from_=twilio_phone_number,
        to=mobile_number
    )
    
    return message.sid


