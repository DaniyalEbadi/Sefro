from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch

User = get_user_model()

class VerificationCommandsTest(TestCase):
    """Tests for email verification management commands"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
    @patch('api.utils.send_verification_email')
    def test_verify_user_command(self, mock_send_email):
        """Test verifying a user via command line"""
        # Initially not verified
        self.assertFalse(self.user.is_email_verified)
        
        # Call the command to verify user
        out = StringIO()
        call_command('verify_user', 'test@example.com', stdout=out)
        
        # Check that the user is now verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertIn('Successfully verified user', out.getvalue())
    
    @patch('api.utils.generate_verification_code')
    def test_get_verification_code_command(self, mock_generate_code):
        """Test getting verification code via command line"""
        # Set up a mock code
        mock_generate_code.return_value = '123456'
        
        # Set verification code
        self.user.set_verification_code('123456')
        self.user.save()
        
        # Call the command
        out = StringIO()
        call_command('get_verification_code', 'test@example.com', stdout=out)
        
        # Check the output contains the code
        self.assertIn('123456', out.getvalue())
    
    @patch('smtplib.SMTP_SSL')
    def test_test_smtp_command(self, mock_smtp):
        """Test the SMTP test command"""
        # Setup mock SMTP connection
        mock_connection = mock_smtp.return_value
        mock_connection.login.return_value = (235, b'Authentication successful')
        mock_connection.sendmail.return_value = {}
        
        # Call the command
        out = StringIO()
        call_command('test_smtp', 'test@example.com', stdout=out)
        
        # Check that SMTP methods were called
        mock_smtp.assert_called_once()
        mock_connection.login.assert_called_once()
        mock_connection.sendmail.assert_called_once()
        self.assertIn('SMTP test successful', out.getvalue())
    
    @patch('requests.post')
    def test_test_liara_command(self, mock_post):
        """Test the Liara API test command"""
        # Setup mock response
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'test-email-id', 'status': 'sent'}
        
        # Call the command
        out = StringIO()
        call_command('test_liara', 'test@example.com', stdout=out)
        
        # Check that requests.post was called
        mock_post.assert_called_once()
        self.assertIn('Liara API test successful', out.getvalue())
    
    @patch('api.utils.send_verification_email')
    def test_test_email_verification_command(self, mock_send_email):
        """Test the email verification test command"""
        mock_send_email.return_value = True
        
        # Call the command
        out = StringIO()
        call_command('test_email_verification', 'test@example.com', stdout=out)
        
        # Check that verification email was sent
        mock_send_email.assert_called_once()
        self.assertIn('Verification email sent', out.getvalue()) 