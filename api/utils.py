import random
import string
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import logging
import requests
import os
import datetime
import json
from django.utils import timezone
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)

def generate_verification_code(length=None):
    """Generate a random verification code."""
    if length is None:
        length = getattr(settings, 'VERIFICATION_CODE_LENGTH', 6)
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(user, code):
    """
    Send a verification email to a user with the provided code.
    
    Args:
        user: The user to send the verification email to
        code: The verification code to include in the email
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    logger.info(f"Attempting to send verification email to {user.email}")
    
    # Get email settings from config
    if settings.EMAIL_HOST and settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        try:
            logger.info("Using standard SMTP email")
            
            # Format expiry time (4 hours from now)
            expiry_time = (timezone.now() + timezone.timedelta(hours=4)).strftime("%H:%M")
            
            # Prepare context for the template
            context = {
                'username': user.username,
                'verification_code': code,
                'expiry_time': expiry_time,
            }
            
            # Render the email templates
            html_content = render_to_string('email_verification_gmail.html', context)
            text_content = f"""
سلام {user.username} عزیز،

خوشحالیم که به خانواده بزرگ سفر پیوستید! برای تکمیل ثبت‌نام و استفاده از تمامی امکانات، لطفاً ایمیل خود را تأیید کنید.

کد تأیید شما: {code}

این کد تا ساعت {expiry_time} معتبر است.
پس از تأیید ایمیل، تمامی امکانات سفر در اختیار شما قرار می‌گیرد.

اگر شما درخواست این کار را نداده‌اید، لطفاً این ایمیل را نادیده بگیرید.

با تشکر،
تیم سفر
            """
            
            # Create email
            email = EmailMultiAlternatives(
                subject="تأیید ایمیل - سفر",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                headers={"x-liara-tag": "email-verification"}
            )
            
            # Attach HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            logger.info(f"Verification email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email via SMTP: {str(e)}")
            
            # Fallback to Liara API
            if hasattr(settings, 'LIARA_API_TOKEN') and settings.LIARA_API_TOKEN:
                logger.info("Falling back to Liara API for email sending")
                return send_email_via_liara_api(
                    recipient=user.email,
                    subject="تأیید ایمیل - سفر",
                    html_content=html_content,
                    text_content=text_content
                )
            else:
                logger.error("No fallback available for email sending")
                return False
    
    elif hasattr(settings, 'LIARA_API_TOKEN') and settings.LIARA_API_TOKEN:
        logger.info("Using Liara API for email sending")
        
        # Format expiry time (4 hours from now)
        expiry_time = (timezone.now() + timezone.timedelta(hours=4)).strftime("%H:%M")
        
        # Prepare context for the template
        context = {
            'username': user.username,
            'verification_code': code,
            'expiry_time': expiry_time,
        }
        
        # Render the email templates
        html_content = render_to_string('email_verification_gmail.html', context)
        text_content = f"""
سلام {user.username} عزیز،

خوشحالیم که به خانواده بزرگ سفر پیوستید! برای تکمیل ثبت‌نام و استفاده از تمامی امکانات، لطفاً ایمیل خود را تأیید کنید.

کد تأیید شما: {code}

این کد تا ساعت {expiry_time} معتبر است.
پس از تأیید ایمیل، تمامی امکانات سفر در اختیار شما قرار می‌گیرد.

اگر شما درخواست این کار را نداده‌اید، لطفاً این ایمیل را نادیده بگیرید.

با تشکر،
تیم سفر
        """
        
        return send_email_via_liara_api(
            recipient=user.email,
            subject="تأیید ایمیل - سفر",
            html_content=html_content,
            text_content=text_content
        )
    
    else:
        logger.error("No email configuration found")
        return False

def send_email_via_liara_api(to_email, subject, text_content, html_content=None, attachments=None):
    """
    Send email using Liara's Mail Service API instead of SMTP.
    
    Args:
        to_email (str): Recipient's email address
        subject (str): Email subject
        text_content (str): Plain text email content
        html_content (str, optional): HTML formatted email content
        attachments (list, optional): List of attachment dictionaries
        
    Returns:
        dict: Response from Liara API with status information
    """
    try:
        url = f"{settings.MAIL_SERVICE_URL}/servers/{settings.MAIL_SERVER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {settings.LIARA_API_TOKEN}",
            "Content-Type": "application/json",
            "x-liara-tag": "email"  # Tag for tracking in Liara dashboard
        }
        
        # Format to_email as list if it's a string
        if isinstance(to_email, str):
            to_email = [to_email]
        
        data = {
            "from": settings.MAIL_FROM,
            "to": to_email,
            "subject": subject,
            "text": text_content,
        }
        
        if html_content:
            data["html"] = html_content
            
        if attachments:
            data["attachments"] = attachments
        
        logger.info(f"Sending email via Liara API to {to_email}, subject: {subject}, url: {url}")
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code in (200, 201, 202):
            logger.info(f"Email sent successfully via Liara API to {to_email}")
            return {
                "success": True,
                "status_code": response.status_code,
                "api_response": response.json() if response.text else {},
                "api_url": url
            }
        else:
            logger.error(f"Failed to send email via Liara API: {response.status_code} - {response.text}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text,
                "api_url": url
            }
            
    except Exception as e:
        logger.error(f"Exception sending email via Liara API: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "api_url": url if 'url' in locals() else "URL not formed"
        } 