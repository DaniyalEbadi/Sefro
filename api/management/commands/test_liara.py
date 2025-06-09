from django.core.management.base import BaseCommand, CommandError
import requests
import json
from django.conf import settings
import sys

class Command(BaseCommand):
    help = 'Test sending an email via Liara Mail API'

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email address to send the test email to')

    def handle(self, *args, **options):
        recipient = options['recipient']
        
        # Get Liara API settings
        try:
            liara_api_key = settings.LIARA_API_KEY
            liara_mail_server = settings.LIARA_MAIL_SERVER
            from_email = settings.DEFAULT_FROM_EMAIL
        except AttributeError as e:
            self.stderr.write(self.style.ERROR(f"Missing required settings: {str(e)}"))
            self.stderr.write(self.style.WARNING("Make sure LIARA_API_KEY, LIARA_MAIL_SERVER, and DEFAULT_FROM_EMAIL are configured in settings.py"))
            sys.exit(1)
        
        # Show configuration
        self.stdout.write(self.style.SUCCESS('Liara API Configuration:'))
        self.stdout.write(f'Mail Server: {liara_mail_server}')
        self.stdout.write(f'From: {from_email}')
        self.stdout.write(f'API Key: {"*" * 8}{liara_api_key[-4:] if liara_api_key else "Not set"}')
        
        # Prepare API request
        api_url = f'https://api.iran.liara.ir/v1/mail/servers/{liara_mail_server}/messages'
        headers = {
            'Authorization': f'Bearer {liara_api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Prepare email data
        payload = {
            'from': from_email,
            'to': [recipient],
            'subject': 'Liara API Test Email from Sefr',
            'html': """
            <html>
            <head>
                <style>
                    body { font-family: 'Vazirmatn', Arial, sans-serif; margin: 20px; direction: rtl; }
                    .container { border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
                    h2 { color: #0ea5e9; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>ایمیل آزمایشی لیارا</h2>
                    <p>این یک ایمیل آزمایشی ارسال شده از API سفر با استفاده از سرویس لیارا است.</p>
                    <p>اگر این ایمیل را می‌بینید، تنظیمات API لیارا به درستی کار می‌کند!</p>
                </div>
            </body>
            </html>
            """,
            'text': 'این یک ایمیل آزمایشی ارسال شده از API سفر با استفاده از سرویس لیارا است.',
            'tags': ['test', 'liara-api']
        }
        
        try:
            self.stdout.write('Sending request to Liara API...')
            
            # Make API request
            response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            
            # Check response
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('Liara API test successful! Email sent.'))
                self.stdout.write(f'Response: {response.json()}')
            else:
                self.stderr.write(self.style.ERROR(f'API Error: {response.status_code}'))
                self.stderr.write(response.text)
                sys.exit(1)
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {str(e)}'))
            sys.exit(1) 