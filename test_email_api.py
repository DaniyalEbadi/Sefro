"""
Script to test sending the Gmail-compatible template via Liara's Mail API.
"""
import os
import sys
import requests
import json
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from django.conf import settings
import django

# Initialize Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sefr.settings')
django.setup()

# Liara API settings
API_URL = settings.MAIL_SERVICE_URL
API_SERVER_ID = settings.MAIL_SERVER_ID
API_TOKEN = settings.LIARA_API_TOKEN
FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

def test_api_gmail_template(recipient_email):
    """Test sending the Gmail-compatible template via Liara API"""
    print(f"Testing Gmail-compatible template via API to {recipient_email}...")
    
    # Test data
    username = "Danial"
    verification_url = "https://example.com/verify?email=test@example.com&code=123456"
    expiry_time = (datetime.now() + timedelta(hours=4)).strftime("%H:%M")
    
    # Context for the template
    context = {
        'username': username,
        'verification_url': verification_url,
        'expiry_time': expiry_time,
    }
    
    # Render the email template
    html_content = render_to_string('email_verification_gmail.html', context)
    
    # Plain text version
    text_content = f"""
سلام {username} عزیز،

خوشحالیم که به خانواده بزرگ سفر پیوستید! برای تکمیل ثبت‌نام و استفاده از تمامی امکانات، لطفاً ایمیل خود را تأیید کنید.

این لینک تا ساعت {expiry_time} معتبر است.
پس از تأیید ایمیل، تمامی امکانات سفر در اختیار شما قرار می‌گیرد.

برای تأیید ایمیل خود، به این آدرس بروید:
{verification_url}

اگر شما درخواست این کار را نداده‌اید، لطفاً این ایمیل را نادیده بگیرید.

با تشکر،
تیم سفر
    """
    
    # Updated URL formats based on Liara's documentation
    url = f"{API_URL}/api/v1/mails/{API_SERVER_ID}/messages"
    
    # Updated authorization format
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",  # Liara expects Bearer token format
        "Content-Type": "application/json",
        "x-liara-tag": "test-verification"
    }
    
    data = {
        "from": FROM_EMAIL,
        "to": recipient_email,
        "subject": "تست قالب سازگار با Gmail - ارسال از طریق API",
        "text": text_content,
        "html": html_content
    }
    
    try:
        print(f"Sending API request to {url}...")
        print(f"Using token format: {API_TOKEN[:10]}...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code in (200, 201, 202):
            print("Email sent successfully via API!")
            print(f"Response: {response.json() if response.text else 'No response body'}")
            return True
        else:
            print(f"API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error with URL {url}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_email_api.py <recipient_email>")
        return
    
    recipient = sys.argv[1]
    test_api_gmail_template(recipient)

if __name__ == "__main__":
    main() 