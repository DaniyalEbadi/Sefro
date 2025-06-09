from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from api.models import Role, Permission, RolePermission, UserRole
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UserTests(APITestCase):
    def setUp(self):
        # Create test user
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'name': 'Test User'
        }
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_user(self):
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password2': 'newpass123',
            'name': 'New User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.get(username='newuser').email, 'new@example.com')

    def test_user_password_hashing(self):
        url = reverse('user-list')
        data = {
            'username': 'passwordtest',
            'email': 'password@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'name': 'Password Test'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='passwordtest')
        self.assertNotEqual(user.password, 'testpass123')
        self.assertTrue(user.check_password('testpass123'))

    def test_user_login(self):
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class RoleTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.role = Role.objects.create(
            name='Test Role',
            description='Test Description'
        )

    def test_create_role(self):
        url = reverse('role-list')
        data = {
            'name': 'New Role',
            'description': 'New Description'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.count(), 2)

    def test_assign_role_to_user(self):
        url = reverse('userrole-list')
        data = {
            'user': self.user.id,
            'role': self.role.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserRole.objects.filter(user=self.user, role=self.role).exists())

class PermissionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.permission = Permission.objects.create(
            name='Test Permission',
            codename='test_permission',
            description='Test Description'
        )

    def test_create_permission(self):
        url = reverse('permission-list')
        data = {
            'name': 'New Permission',
            'codename': 'new_permission',
            'description': 'New Description'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Permission.objects.count(), 2)

    def test_assign_permission_to_role(self):
        role = Role.objects.create(name='Test Role')
        url = reverse('rolepermission-list')
        data = {
            'role': role.id,
            'permission': self.permission.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RolePermission.objects.filter(role=role, permission=self.permission).exists())

class AuthenticationTests(APITestCase):
    def setUp(self):
        # Create a test user
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_register_user(self):
        """Test user registration"""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')

    def test_login_with_username(self):
        """Test login with username"""
        url = reverse('login')
        data = {
            'login': self.user_data['username'],
            'password': self.user_data['password']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])

    def test_login_with_email(self):
        """Test login with email"""
        url = reverse('login')
        data = {
            'login': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('login')
        data = {
            'login': self.user_data['username'],
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_logout(self):
        """Test user logout"""
        # First login to get the refresh token
        login_url = reverse('login')
        login_data = {
            'login': self.user_data['username'],
            'password': self.user_data['password']
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Then logout using the refresh token
        logout_url = reverse('logout')
        logout_data = {
            'refresh': login_response.data['refresh']
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        logout_response = self.client.post(logout_url, logout_data, format='json')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertIn('message', logout_response.data)

    def test_token_refresh(self):
        """Test token refresh"""
        # First login to get the refresh token
        login_url = reverse('login')
        login_data = {
            'login': self.user_data['username'],
            'password': self.user_data['password']
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Then try to get a new access token
        refresh_url = reverse('token_refresh')
        refresh_data = {
            'refresh': login_response.data['refresh']
        }
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_login_missing_fields(self):
        """Test login with missing fields"""
        url = reverse('login')
        # Test without password
        data = {'login': self.user_data['username']}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test without login
        data = {'password': self.user_data['password']}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        """Test registration with duplicate username"""
        url = reverse('register')
        data = self.user_data.copy()
        data['email'] = 'another@example.com'  # Different email but same username
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        url = reverse('register')
        data = self.user_data.copy()
        data['username'] = 'anotheruser'  # Different username but same email
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) 