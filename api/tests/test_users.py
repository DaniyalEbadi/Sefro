from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from api.models import Role, Permission, RolePermission, UserRole

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