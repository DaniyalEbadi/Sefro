import os
import logging
import smtplib
import socket
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_test_email(request):
    """
    Send a test email to verify the email configuration.
    Expects: {"recipient": "email@example.com"}
    """
    recipient = request.data.get('recipient')
    if not recipient:
        return JsonResponse({
            'status': 'error',
            'message': 'No recipient email provided'
        }, status=400)
    
    try:
        subject = "Test Email from Sefr API"
        message = "This is a test email from Sefr API. If you received this, your email configuration is working."
        from_email = settings.DEFAULT_FROM_EMAIL
        
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient],
            fail_silently=False,
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Test email sent to {recipient}',
            'details': {
                'subject': subject,
                'from_email': from_email,
                'email_backend': settings.EMAIL_BACKEND,
                'email_host': settings.EMAIL_HOST,
                'email_port': settings.EMAIL_PORT,
            }
        })
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to send email: {str(e)}',
            'details': {
                'email_backend': settings.EMAIL_BACKEND,
                'email_host': settings.EMAIL_HOST,
                'email_port': settings.EMAIL_PORT,
            }
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def test_smtp_email(request):
    """
    Test sending an email directly via SMTP with SSL.
    Expects: {"recipient": "email@example.com"}
    """
    recipient = request.data.get('recipient')
    if not recipient:
        return JsonResponse({
            'status': 'error',
            'message': 'No recipient email provided'
        }, status=400)
    
    try:
        # Create a message
        msg = MIMEMultipart()
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = recipient
        msg['Subject'] = "SMTP Test Email from Sefr API"
        
        body = "This is a test email sent directly via SMTP from Sefr API."
        msg.attach(MIMEText(body, 'plain'))
        
        # Send the email via SMTP with SSL
        with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.send_message(msg)
        
        return JsonResponse({
            'status': 'success',
            'message': f'SMTP test email sent to {recipient}',
            'details': {
                'host': settings.EMAIL_HOST,
                'port': settings.EMAIL_PORT,
                'user': settings.EMAIL_HOST_USER,
                'use_ssl': settings.EMAIL_USE_SSL,
            }
        })
    except Exception as e:
        logger.error(f"SMTP test error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to send SMTP email: {str(e)}',
            'details': {
                'host': settings.EMAIL_HOST,
                'port': settings.EMAIL_PORT,
                'user': settings.EMAIL_HOST_USER,
                'use_ssl': settings.EMAIL_USE_SSL,
            }
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def email_diagnostics(request):
    """
    Perform diagnostics on email delivery configuration.
    Expects: {"recipient": "email@example.com"}
    """
    recipient = request.data.get('recipient')
    if not recipient:
        return JsonResponse({
            'status': 'error',
            'message': 'No recipient email provided'
        }, status=400)
    
    diagnostics = {
        'environment': {
            'python_version': os.sys.version,
            'django_settings': {
                'email_backend': settings.EMAIL_BACKEND,
                'email_host': settings.EMAIL_HOST,
                'email_port': settings.EMAIL_PORT,
                'email_use_tls': settings.EMAIL_USE_TLS,
                'email_use_ssl': settings.EMAIL_USE_SSL,
                'default_from_email': settings.DEFAULT_FROM_EMAIL,
            },
            'os_info': os.name,
        },
        'connectivity': {
            'check_dns': None,
            'check_socket': None,
            'smtp_test': None,
        },
        'delivery': {
            'status': None,
            'message': None,
        }
    }
    
    # DNS Resolution
    try:
        socket.gethostbyname(settings.EMAIL_HOST)
        diagnostics['connectivity']['check_dns'] = 'success'
    except socket.gaierror as e:
        diagnostics['connectivity']['check_dns'] = f'failed: {str(e)}'
    
    # Socket Connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((settings.EMAIL_HOST, settings.EMAIL_PORT))
        sock.close()
        diagnostics['connectivity']['check_socket'] = 'success'
    except Exception as e:
        diagnostics['connectivity']['check_socket'] = f'failed: {str(e)}'
    
    # SMTP Login Test
    try:
        if settings.EMAIL_USE_SSL:
            server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
        else:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
            if settings.EMAIL_USE_TLS:
                server.starttls()
        
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.quit()
        diagnostics['connectivity']['smtp_test'] = 'success'
    except Exception as e:
        diagnostics['connectivity']['smtp_test'] = f'failed: {str(e)}'
    
    # Attempt email delivery
    try:
        subject = "Diagnostics Test from Sefr API"
        message = "This is a diagnostics test email from Sefr API."
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
            headers={'X-Test': 'Diagnostics'}
        )
        email.send()
        diagnostics['delivery']['status'] = 'sent'
        diagnostics['delivery']['message'] = f'Test email sent to {recipient}'
    except Exception as e:
        diagnostics['delivery']['status'] = 'failed'
        diagnostics['delivery']['message'] = str(e)
    
    return JsonResponse({
        'status': 'success',
        'message': 'Email diagnostics completed',
        'diagnostics': diagnostics
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def test_liara_api_email(request):
    """
    Test sending an email via Liara's Mail API instead of SMTP.
    Expects: {"recipient": "email@example.com"}
    """
    recipient = request.data.get('recipient')
    if not recipient:
        return JsonResponse({
            'status': 'error',
            'message': 'No recipient email provided'
        }, status=400)
    
    try:
        # Liara Mail API endpoint
        url = f"{settings.MAIL_SERVICE_URL}/api/v1/mails"
        
        # Prepare email payload
        payload = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [recipient],
            "subject": "Liara API Test Email from Sefr",
            "text": "This is a test email sent via Liara's Mail API from Sefr.",
            "html": "<h1>Liara API Test</h1><p>This is a test email sent via Liara's Mail API from Sefr.</p>"
        }
        
        # Set headers with authorization
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LIARA_API_TOKEN}"
        }
        
        # Make the API request
        response = requests.post(
            url, 
            data=json.dumps(payload), 
            headers=headers
        )
        
        if response.status_code == 202:
            return JsonResponse({
                'status': 'success',
                'message': f'Email sent via Liara API to {recipient}',
                'details': {
                    'api_response': response.json() if response.text else {},
                    'status_code': response.status_code
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Liara API error: {response.text}',
                'details': {
                    'status_code': response.status_code,
                    'api_url': url
                }
            }, status=response.status_code)
            
    except Exception as e:
        logger.error(f"Liara API test error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to send via Liara API: {str(e)}',
            'details': {
                'mail_service_url': settings.MAIL_SERVICE_URL,
                'server_id': settings.MAIL_SERVER_ID
            }
        }, status=500)
