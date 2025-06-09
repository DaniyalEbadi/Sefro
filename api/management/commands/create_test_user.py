from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a test user'

    def handle(self, *args, **kwargs):
        try:
            # Check if user exists
            user = User.objects.get(username='Danimeni')
            self.stdout.write(self.style.SUCCESS(f'User {user.username} already exists'))
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username='Danimeni',
                email='danimeni@example.com',
                password='Danial2017!',
                first_name='Danial',
                last_name='Meni'
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created user {user.username}')) 