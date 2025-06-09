from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from api.utils import generate_verification_code, send_verification_email
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test verification email sending functionality'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send the verification email to')
        parser.add_argument('--create-user', action='store_true', help='Create a test user if not exists')

    def handle(self, *args, **options):
        email = options['email']
        create_user = options.get('create_user', False)
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f'Using existing user: {user.username} <{email}>')
        except User.DoesNotExist:
            if not create_user:
                self.stderr.write(
                    self.style.ERROR(f'User with email {email} does not exist. Use --create-user to create a test user.')
                )
                return
                
            # Create test user if requested
            username = email.split('@')[0]
            user = User.objects.create_user(
                username=username,
                email=email,
                password='TestUser123!',
                first_name='Test',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS(f'Created test user: {username} <{email}>'))
        
        # Generate verification code
        code = generate_verification_code()
        user.set_verification_code(code)
        user.save()
        
        self.stdout.write(f'Generated verification code: {code}')
        
        # Send verification email
        try:
            self.stdout.write('Sending verification email...')
            result = send_verification_email(user, code)
            
            if result:
                self.stdout.write(self.style.SUCCESS('Verification email sent successfully!'))
                
                # Show verification instructions
                self.stdout.write('\nVerification endpoints:')
                self.stdout.write(f'1. Use API: POST /api/auth/verify-email/ with payload:')
                self.stdout.write(f'   {{"email": "{email}", "code": "{code}"}}')
                self.stdout.write(f'2. Use command: python manage.py verify_user {email}')
                
            else:
                self.stderr.write(self.style.ERROR('Failed to send verification email. Check the logs for details.'))
                
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            self.stderr.write(self.style.ERROR(f'Error: {str(e)}')) 