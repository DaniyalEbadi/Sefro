from django.core.management.base import BaseCommand, CommandError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import sys

class Command(BaseCommand):
    help = 'Test SMTP email functionality by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email address to send the test email to')

    def handle(self, *args, **options):
        recipient = options['recipient']
        
        # Get email settings from Django settings
        host = settings.EMAIL_HOST
        port = settings.EMAIL_PORT
        username = settings.EMAIL_HOST_USER
        password = settings.EMAIL_HOST_PASSWORD
        use_tls = settings.EMAIL_USE_TLS
        use_ssl = settings.EMAIL_USE_SSL
        default_from = settings.DEFAULT_FROM_EMAIL
        
        # Display configuration
        self.stdout.write(self.style.SUCCESS('Email Configuration:'))
        self.stdout.write(f'Host: {host}')
        self.stdout.write(f'Port: {port}')
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'From: {default_from}')
        self.stdout.write(f'TLS: {use_tls}')
        self.stdout.write(f'SSL: {use_ssl}')
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'SMTP Test Email from Sefr'
        msg['From'] = default_from
        msg['To'] = recipient
        
        text = "This is a test email sent from the Sefr API using SMTP."
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
                h2 { color: #0ea5e9; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>SMTP Test Email</h2>
                <p>This is a test email sent from the Sefr API using SMTP.</p>
                <p>If you're seeing this, the SMTP configuration is working correctly!</p>
            </div>
        </body>
        </html>
        """
        
        # Attach parts
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        try:
            self.stdout.write('Connecting to SMTP server...')
            
            # Connect to SMTP server
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port)
            else:
                server = smtplib.SMTP(host, port)
                if use_tls:
                    server.starttls()
            
            # Login if credentials provided
            if username and password:
                self.stdout.write('Logging in...')
                server.login(username, password)
            
            # Send email
            self.stdout.write(f'Sending email to {recipient}...')
            server.sendmail(default_from, recipient, msg.as_string())
            server.quit()
            
            self.stdout.write(self.style.SUCCESS('SMTP test successful! Email sent.'))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {str(e)}'))
            sys.exit(1) 