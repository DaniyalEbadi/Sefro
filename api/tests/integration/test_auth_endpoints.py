from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from unittest.mock import patch # For mocking send_verification_email if needed

User = get_user_model()

class AuthEndpointsIntegrationTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
        self.verify_email_url = reverse('auth-verify-email')
        self.refresh_token_url = reverse('auth-token-refresh')
        # self.resend_verification_url = reverse('auth-resend-verification') # If testing this too

        self.user_data = {
            'email': 'testregister@example.com',
            'password': 'StrongPassword123',
            'first_name': 'Test',
            'last_name': 'Register'
        }
        self.user_data_login = { # For login, can use email or username
            'login': 'testregister@example.com',
            'password': 'StrongPassword123'
        }

    @patch('api.views.send_verification_email', return_value=True) # Mock to prevent actual email sending
    def test_user_registration_success(self, mock_send_email):
        response = self.client.post(self.register_url, self.user_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])
        self.assertFalse(response.data['user']['is_email_verified']) # Default

        self.assertIn('verification', response.data)
        # EMAIL_DELIVERY_CHECK is True in settings by default for tests from previous steps
        if getattr(settings, 'EMAIL_DELIVERY_CHECK', False):
             self.assertEqual(response.data['verification']['email_status'], 'sent')
        else:
            self.assertEqual(response.data['verification']['email_status'], 'skipped (dev mode)')

        mock_send_email.assert_called_once() # Check if email sending was attempted

        # Verify user exists in DB
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
        user_db = User.objects.get(email=self.user_data['email'])
        self.assertFalse(user_db.is_email_verified)
        self.assertIsNotNone(user_db.verification_code) # Code should be set

    def test_user_registration_missing_fields(self):
        invalid_data = self.user_data.copy()
        del invalid_data['email']
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_registration_email_already_exists(self):
        # Create a user first
        User.objects.create_user(
            email=self.user_data['email'],
            password='anotherpassword',
            first_name='Existing',
            last_name='User'
        )
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data) # Check for email error specifically

    @patch('api.views.send_verification_email', return_value=True)
    def test_user_login_success(self, mock_send_email):
        # Register user first
        self.client.post(self.register_url, self.user_data, format='json')

        # Now login
        response = self.client.post(self.login_url, self.user_data_login, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data_login['login'])

    def test_user_login_invalid_credentials_wrong_password(self):
        # Register user first
        self.client.post(self.register_url, self.user_data, format='json') # Use default user_data

        invalid_login_data = {'login': self.user_data['email'], 'password': 'WrongPassword'}
        response = self.client.post(self.login_url, invalid_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_user_login_user_not_found(self):
        non_existent_user_data = {'login': 'nouser@example.com', 'password': 'password'}
        response = self.client.post(self.login_url, non_existent_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # Or 404 depending on auth backend
        self.assertIn('error', response.data)

    @patch('api.views.send_verification_email', return_value=True)
    def test_email_verification_success(self, mock_send_email):
        # 1. Register user
        self.client.post(self.register_url, self.user_data, format='json')
        user = User.objects.get(email=self.user_data['email'])
        self.assertFalse(user.is_email_verified)
        self.assertIsNotNone(user.verification_code)

        verification_payload = {
            'email': user.email,
            'code': user.verification_code
        }

        # 2. Verify email
        response = self.client.post(self.verify_email_url, verification_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'ایمیل شما با موفقیت تأیید شد.')
        self.assertIn('user', response.data)
        self.assertTrue(response.data['user']['is_email_verified'])
        self.assertIn('access', response.data) # Should get new tokens
        self.assertIn('refresh', response.data)

        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertIsNone(user.verification_code) # Code should be cleared

    @patch('api.views.send_verification_email', return_value=True)
    def test_email_verification_invalid_code(self, mock_send_email):
        self.client.post(self.register_url, self.user_data, format='json')
        user = User.objects.get(email=self.user_data['email'])

        verification_payload = {'email': user.email, 'code': 'INVALID0'} # Invalid code

        response = self.client.post(self.verify_email_url, verification_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['code'], 'invalid_code')

        user.refresh_from_db()
        self.assertFalse(user.is_email_verified) # Should remain unverified

    @patch('api.views.send_verification_email', return_value=True)
    def test_email_verification_already_verified(self, mock_send_email):
        self.client.post(self.register_url, self.user_data, format='json')
        user = User.objects.get(email=self.user_data['email'])
        valid_code = user.verification_code

        # First verification
        self.client.post(self.verify_email_url, {'email': user.email, 'code': valid_code}, format='json')
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

        # Attempt to verify again
        response = self.client.post(self.verify_email_url, {'email': user.email, 'code': valid_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Returns 200 with a message
        self.assertEqual(response.data['code'], 'already_verified')


    @patch('api.views.send_verification_email', return_value=True)
    def test_token_refresh_success(self, mock_send_email):
        # 1. Register and get initial tokens
        reg_response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        initial_refresh_token = reg_response.data['refresh']
        initial_access_token = reg_response.data['access']

        # 2. Use refresh token to get a new access token
        refresh_payload = {'refresh': initial_refresh_token}
        # For token refresh, user needs to be authenticated with the current access token typically.
        # However, simplejwt's TokenRefreshView itself doesn't require authentication on the view,
        # just a valid refresh token in the payload. Let's check DRF simplejwt docs/behavior.
        # By default, TokenRefreshView does not require authentication.

        refresh_response = self.client.post(self.refresh_token_url, refresh_payload, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK, refresh_response.data)
        self.assertIn('access', refresh_response.data)
        self.assertNotIn('refresh', refresh_response.data) # Default refresh view only returns new access token
        new_access_token = refresh_response.data['access']
        self.assertNotEqual(new_access_token, initial_access_token)

    def test_token_refresh_invalid_token(self):
        refresh_payload = {'refresh': 'thisisnotavalidtoken'}
        response = self.client.post(self.refresh_token_url, refresh_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # Or 400 if token is badly formed
        self.assertIn('detail', response.data) # SimpleJWT usually returns 'detail' and 'code'
