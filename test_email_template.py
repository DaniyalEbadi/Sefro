"""
Simple script to test the Gmail-compatible email template directly.
"""
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from django.conf import settings
import django

# Initialize Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sefr.settings')
django.setup()

# Email settings
SMTP_HOST = settings.EMAIL_HOST
SMTP_PORT = settings.EMAIL_PORT
SMTP_USER = settings.EMAIL_HOST_USER
SMTP_PASSWORD = settings.EMAIL_HOST_PASSWORD
FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
FROM_NAME = "Sefr API"
MAIL_FROM = f"{FROM_NAME} <{FROM_EMAIL}>"

def test_gmail_template(recipient_email):
    """Test the Gmail-compatible template"""
    print(f"Testing Gmail-compatible template email to {recipient_email}...")
    
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
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "تست قالب سازگار با Gmail"
    message["From"] = MAIL_FROM
    message["To"] = recipient_email
    
    # Add plain text content
    message.attach(MIMEText(text_content, "plain", "utf-8"))
    
    # Add HTML content
    message.attach(MIMEText(html_content, "html", "utf-8"))
    
    try:
        # Connect to SMTP server
        print(f"Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        print("Connected successfully")
        
        # Login
        print(f"Logging in as {SMTP_USER}...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("Logged in successfully")
        
        # Send email
        print("Sending email...")
        server.sendmail(FROM_EMAIL, recipient_email, message.as_string())
        print("Email sent successfully!")
        
        # Quit server
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_email_template.py <recipient_email>")
        return
    
    recipient = sys.argv[1]
    test_gmail_template(recipient)

if __name__ == "__main__":
    main() 