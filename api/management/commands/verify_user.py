from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Verify a user email directly (for testing and development)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email to verify')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email {email} does not exist')
        
        if user.is_email_verified:
            self.stdout.write(self.style.WARNING(f'Email {email} is already verified'))
            return
        
        user.is_email_verified = True
        user.verification_code = None
        user.verification_code_created = None
        user.save()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully verified user email: {email}')) 