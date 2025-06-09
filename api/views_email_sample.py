import os
import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.template.loader import render_to_string
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from api.utils import send_verification_email, generate_verification_code
from django.utils import timezone

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_sample_email(request):
    """
    Send a plain text email to a recipient.
    
    Expects: {"email": "recipient@example.com"}
    
    Returns:
        JsonResponse: Result of the email sending attempt
    """
    recipient = request.data.get('email')
    if not recipient:
        return JsonResponse({
            'status': 'error',
            'message': 'Recipient email is required'
        }, status=400)
    
    try:
        subject = "Sample Email from Sefr API"
        message = "This is a sample email sent from Sefr API. This demonstrates our email sending capability."
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
            'message': f'Sample email sent to {recipient}'
        })
    except Exception as e:
        logger.error(f"Error sending sample email: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to send email: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_html_email(request):
    """
    Send an HTML email with alternative plain text content.
    
    Expects: {"email": "recipient@example.com"}
    
    Returns:
        JsonResponse: Result of the email sending attempt
    """
    recipient = request.data.get('email')
    if not recipient:
        return JsonResponse({
            'status': 'error',
            'message': 'Recipient email is required'
        }, status=400)
    
    try:
        subject = "HTML Email from Sefr API"
        text_content = "This is a sample HTML email from Sefr API. This demonstrates our email sending capability."
        html_content = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    h1 { color: #0066cc; }
                    .footer { margin-top: 30px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>HTML Email from Sefr API</h1>
                    <p>This is a sample HTML email from Sefr API.</p>
                    <p>This demonstrates our email sending capability with <strong>rich HTML formatting</strong>.</p>
                    <div class="footer">
                        <p>This is an automated message. Please do not reply.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        
        # Create email message with both text and HTML versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[recipient]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        return JsonResponse({
            'status': 'success',
            'message': f'HTML email sent to {recipient}'
        })
    except Exception as e:
        logger.error(f"Error sending HTML email: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to send HTML email: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_template_email(request):
    """
    Send an email using a Django template.
    
    Expects: {
        "email": "recipient@example.com",
        "name": "User Name"
    }
    
    Returns:
        JsonResponse: Result of the email sending attempt
    """
    recipient = request.data.get('email')
    name = request.data.get('name', 'User')
    
    if not recipient:
        return JsonResponse({
            'status': 'error',
            'message': 'Recipient email is required'
        }, status=400)
    
    try:
        subject = "Template Email from Sefr API"
        context = {
            'name': name,
            'app_name': 'Sefr API',
            'current_year': timezone.now().year
        }
        
        # Render text and HTML content from templates
        text_content = f"""
        Hello {name},
        
        This is a template-based email from Sefr API.
        
        This demonstrates our capability to send emails using Django templates.
        
        Best regards,
        The Sefr API Team
        """
        
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #0066cc; }}
                    .greeting {{ font-size: 18px; margin-bottom: 20px; }}
                    .content {{ margin: 20px 0; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Template Email from Sefr API</h1>
                    <div class="greeting">Hello {name},</div>
                    <div class="content">
                        <p>This is a template-based email from Sefr API.</p>
                        <p>This demonstrates our capability to send emails using Django templates.</p>
                    </div>
                    <div class="footer">
                        <p>Best regards,<br>The Sefr API Team</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        from_email = settings.DEFAULT_FROM_EMAIL
        
        # Create email message with both text and HTML versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[recipient]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Template email sent to {recipient}'
        })
    except Exception as e:
        logger.error(f"Error sending template email: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to send template email: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def test_verification_email(request):
    """
    Test sending a verification email with a code.
    
    Expects: {"email": "recipient@example.com"}
    
    Returns:
        JsonResponse: Result of the verification email sending attempt
    """
    recipient = request.data.get('email')
    if not recipient:
        return JsonResponse({
            'status': 'error',
            'message': 'Recipient email is required'
        }, status=400)
    
    try:
        # For testing, we'll use a fixed verification code
        verification_code = "123456"  # In a real app, use generate_verification_code()
        
        # Get the user (simplified for this sample)
        # In a real app, you'd get the user from the database
        from api.models import User
        try:
            user = User.objects.get(email=recipient)
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'User not found with this email'
            }, status=404)
        
        # Send verification email
        result = send_verification_email(user, verification_code)
        
        if result:
            return JsonResponse({
                'status': 'success',
                'message': f'Verification email sent to {recipient}',
                'verification_code': verification_code  # Only for testing! Don't include this in production
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send verification email'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to send verification email: {str(e)}'
        }, status=500)
