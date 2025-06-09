import logging
import json
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import User
from django.utils import timezone

# Configure logger
logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def send_verification_email(request):
    """
    API endpoint to send a verification email to the user.
    
    Request JSON format:
    {
        "email": "user@example.com"
    }
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'}, status=400)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        
        # If already verified, return success
        if user.is_verified:
            return JsonResponse({'success': True, 'message': 'Email already verified'})
        
        # Generate and save verification code
        code = user.generate_verification_code()
        
        # Prepare email content
        subject = 'تایید ایمیل - سفر'
        to_email = [email]
        
        # HTML content with RTL support for Persian language
        html_content = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="fa">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>تایید ایمیل - سفر</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
                
                :root {{
                    color-scheme: light dark;
                }}
                
                body {{
                    font-family: 'Vazirmatn', Tahoma, Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f9fafb;
                    color: #111827;
                    direction: rtl;
                    text-align: right;
                }}
                
                @media (prefers-color-scheme: dark) {{
                    body {{
                        background-color: #111827;
                        color: #f9fafb;
                    }}
                    .container {{
                        background-color: #1f2937 !important;
                        border-color: #374151 !important;
                    }}
                    .info-box {{
                        background-color: #233044 !important;
                    }}
                    .warning-box {{
                        background-color: #42321a !important;
                    }}
                }}
                
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    padding: 0;
                    background-color: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                
                .header {{
                    padding: 20px;
                    text-align: center;
                    border-bottom: 1px solid #e5e7eb;
                }}
                
                .logo {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #2563eb;
                }}
                
                .content {{
                    padding: 25px;
                }}
                
                h1 {{
                    font-size: 18px;
                    font-weight: 600;
                    margin-top: 0;
                    margin-bottom: 16px;
                }}
                
                p {{
                    font-size: 15px;
                    line-height: 1.6;
                    margin: 16px 0;
                    color: #4b5563;
                }}
                
                .info-box {{
                    margin: 20px 0;
                    padding: 16px;
                    background-color: #f1f5f9;
                    border-radius: 8px;
                }}
                
                .warning-box {{
                    margin: 20px 0;
                    padding: 16px;
                    background-color: #fff8ed;
                    border-radius: 8px;
                    border-right: 4px solid #f97316;
                }}
                
                .code {{
                    font-family: 'Vazirmatn', monospace;
                    font-size: 24px;
                    font-weight: 700;
                    letter-spacing: 0.1em;
                    color: #2563eb;
                    margin: 10px 0;
                }}
                
                .footer {{
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #6b7280;
                    border-top: 1px solid #e5e7eb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">SEFRO</div>
                </div>
                <div class="content">
                    <h1>سلام {user.first_name} عزیز،</h1>
                    <p>خوشحالیم که به خانواده بزرگ SEFRO پیوستید! برای تکمیل ثبت‌نام و استفاده از تمامی امکانات، لطفا ایمیل خود را تأیید کنید.</p>
                    
                    <div class="info-box">
                        <p>کد تأیید شما: <span class="code">{code}</span></p>
                        <p>این کد تا ساعت {(timezone.now() + timezone.timedelta(hours=24)).strftime('%H:%M')} معتبر است.</p>
                        <p>لطفا این کد را در صفحه تایید وارد کنید.</p>
                    </div>
                    
                    <div class="warning-box">
                        <p>
                         این کار برای حفظ امنیت حساب شماست
                        </p>
                    </div>
                </div>
                <div class="footer">
                    <p>© سفر API - تمامی حقوق محفوظ است.</p>
                    <p>این ایمیل از طریق Liara Email Service ارسال شده است.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text content
        text_content = f"""
        شرکت سفر لیارا
        
        سلام {user.first_name if user.first_name else user.username} عزیز،
        
        خوشحالیم که به خانواده بزرگ سفر پیوستید! برای تکمیل ثبت‌نام و استفاده از تمامی امکانات، لطفا ایمیل خود را تأیید کنید.
        
        کد تأیید شما: {code}
        
        این کد تا ساعت {(timezone.now() + timezone.timedelta(hours=24)).strftime('%H:%M')} معتبر است.
        
        لطفا این کد را در صفحه تایید وارد کنید.
        
        اگر شما درخواست این کار را نداده‌اید، لطفا این ایمیل را نادیده بگیرید.
        
        © سفر API - تمامی حقوق محفوظ است.
        این ایمیل از طریق Liara Email Service ارسال شده است.
        """
        
        # Create custom headers for Liara email
        headers = {
            "x-liara-tag": "verification-email",  # For tracking in Liara dashboard
            "X-Priority": "1",  # High priority
            "X-MSMail-Priority": "High",
            "Importance": "High"
        }
        
        try:
            # Create and send email - using the MAIL_FROM from settings
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=None,  # Uses MAIL_FROM from settings.py
                to=to_email,
                headers=headers,
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()
            
            logger.info(f"Verification email sent to {email}")
            return JsonResponse({'success': True, 'message': 'Verification email sent successfully'})
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Failed to send email: {str(e)}'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        logger.error(f"Error in send_verification_email: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def verify_code(request):
    """
    API endpoint to verify a verification code.
    
    Request JSON format:
    {
        "email": "user@example.com",
        "code": "123456"
    }
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        code = data.get('code')
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'}, status=400)
            
        if not code:
            return JsonResponse({'success': False, 'message': 'Verification code is required'}, status=400)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        
        # If already verified, return success
        if user.is_verified:
            return JsonResponse({'success': True, 'message': 'Email already verified'})
        
        # Verify the code
        is_valid = user.verify_code(code)
        
        if is_valid:
            # Mark user as verified
            user.is_verified = True
            user.verification_code = None
            user.verification_code_created = None
            user.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Email verified successfully'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid or expired verification code'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        logger.error(f"Error in verify_code: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'}, status=500) 