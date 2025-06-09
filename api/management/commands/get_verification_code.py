from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Get the verification code for a specified user (for development/testing)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email to get verification code for')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email {email} does not exist')
        
        if user.is_email_verified:
            self.stdout.write(self.style.WARNING(f'User {email} is already verified'))
        
        if not user.verification_code:
            self.stdout.write(self.style.WARNING('User has no verification code set'))
            return
        
        # Calculate code expiry
        from django.conf import settings
        timeout = getattr(settings, 'EMAIL_VERIFICATION_TIMEOUT', 3600)  # Default 1 hour
        
        now = timezone.now()
        created = user.verification_code_created
        
        if created:
            time_passed = (now - created).total_seconds()
            time_left = max(0, timeout - time_passed)
            
            if time_left > 0:
                self.stdout.write(self.style.SUCCESS(f'Verification code for {email}:'))
                self.stdout.write(self.style.SUCCESS(f'Code: {user.verification_code}'))
                self.stdout.write(f'Created: {created}')
                self.stdout.write(f'Expires in: {int(time_left)} seconds ({int(time_left/60)} minutes)')
            else:
                self.stdout.write(self.style.WARNING(f'Verification code for {email} has expired:'))
                self.stdout.write(self.style.WARNING(f'Code: {user.verification_code}'))
                self.stdout.write(f'Created: {created}')
                self.stdout.write(f'Expired: {int(time_passed - timeout)} seconds ago')
        else:
            self.stdout.write(self.style.WARNING('Code creation time not recorded'))
            self.stdout.write(self.style.SUCCESS(f'Code: {user.verification_code}')) 