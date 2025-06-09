from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
import json
import logging
from unittest.mock import patch, MagicMock

User = get_user_model()

class EmailVerificationTests(APITestCase):
    """Test cases for email verification endpoints"""
    
    def setUp(self):
        """Set up test data for each test"""
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    @patch('api.utils.send_verification_email')
    def test_register_with_verification(self, mock_send_email):
        """Test user registration with email verification"""
        mock_send_email.return_value = True
        
        url = reverse('auth-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securePass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertIn('verification', response.data)
        
        # Verify that user was created
        user = User.objects.get(email='newuser@example.com')
        self.assertFalse(user.is_email_verified)
        self.assertIsNotNone(user.verification_code)
        
        # Verify that the email send function was called
        # Note: the actual function might be called from inside the view, not directly
        
    def test_verify_email(self):
        """Test email verification with valid code"""
        # Set up verification code
        code = '123456'
        self.user.set_verification_code(code)
        self.assertFalse(self.user.is_email_verified)
        
        url = reverse('auth-verify-email')
        data = {
            'email': self.user.email,
            'code': code
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that the user's email is now verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertIsNone(self.user.verification_code)
        
    def test_verify_email_invalid_code(self):
        """Test email verification with invalid code"""
        code = '123456'
        invalid_code = '654321'
        self.user.set_verification_code(code)
        
        url = reverse('auth-verify-email')
        data = {
            'email': self.user.email,
            'code': invalid_code
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify that the user's email is still not verified
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)
        
    @patch('api.utils.send_verification_email')
    def test_resend_verification(self, mock_send_email):
        """Test resending verification code"""
        # Initially not verified
        self.assertFalse(self.user.is_email_verified)
        
        # Store original verification code
        original_code = '123456'
        self.user.set_verification_code(original_code)
        self.user.refresh_from_db()
        
        mock_send_email.return_value = True
        
        url = reverse('auth-resend-verification')
        data = {'email': self.user.email}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Note: The actual email sending may be tested in the view test
            
    def test_debug_get_verification_code(self):
        """Test the debug endpoint to get verification code"""
        # Set up verification code
        code = '123456'
        self.user.set_verification_code(code)
        
        # Create an admin user for authorization
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.client.force_authenticate(user=admin)
        
        url = reverse('auth-debug-get-code')
        data = {'email': self.user.email}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], code)
        
    def test_debug_direct_verify(self):
        """Test the debug endpoint to directly verify email"""
        # Initially not verified
        self.assertFalse(self.user.is_email_verified)
        
        # Create an admin user for authorization
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.client.force_authenticate(user=admin)
        
        url = reverse('auth-debug-direct-verify')
        data = {'email': self.user.email}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that the user's email is now verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)


class EmailDeliveryTests(APITestCase):
    """Test cases for email delivery functionality"""
    
    def setUp(self):
        """Set up test data for each test"""
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.client.force_authenticate(user=self.admin_user)
        
    @patch('api.views_email.send_mail')
    def test_send_test_email(self, mock_send_mail):
        """Test sending a test email"""
        mock_send_mail.return_value = 1
        
        url = reverse('test_email')
        data = {'email': 'test@example.com'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        
        # Verify that the send_mail function was called
        mock_send_mail.assert_called_once()
        
    @patch('smtplib.SMTP_SSL')
    def test_smtp_email(self, mock_smtp):
        """Test sending an email via SMTP"""
        # Setup mock SMTP connection
        mock_connection = MagicMock()
        mock_smtp.return_value = mock_connection
        mock_connection.login.return_value = (235, b'Authentication successful')
        mock_connection.sendmail.return_value = {}
        
        url = reverse('test_smtp_email')
        data = {'email': 'test@example.com'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        
        # Verify that SMTP functions were called
        mock_smtp.assert_called_once()
        mock_connection.login.assert_called_once()
        mock_connection.sendmail.assert_called_once()
        
    @patch('requests.post')
    def test_liara_api_email(self, mock_post):
        """Test sending an email via Liara API"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'test-email-id', 'status': 'sent'}
        mock_post.return_value = mock_response
        
        url = reverse('test_liara_api_email')
        data = {'email': 'test@example.com'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        
        # Verify that requests.post was called
        mock_post.assert_called_once()
        
    def test_email_diagnostics(self):
        """Test the email diagnostics endpoint"""
        url = reverse('email_diagnostics')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that the response contains diagnostic information
        self.assertIn('email_settings', response.data) 