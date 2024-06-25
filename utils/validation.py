import re

def validate_email(email):
    # Regular expression pattern for email validation
    pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
    
    # Check if the email matches the pattern
    if re.match(pattern, email):
        return True
    else:
        return False


def is_valid_mobile_number(mobile_number):
    # Regular expression to check if the mobile number is exactly 10 digits
    pattern = re.compile(r'^\d{10}$')
    
    if pattern.match(mobile_number):
        return True
    else:
        return False