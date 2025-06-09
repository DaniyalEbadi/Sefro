from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from api.models import Article, Category, User # User needed for type hinting if any
from unittest.mock import patch

UserModel = get_user_model() # Use UserModel consistently

class UserArticleFlowE2ETests(APITestCase):

    def setUp(self):
        self.client = APIClient() # Fresh client for the E2E test

        # URLs needed for the flow
        self.register_url = reverse('auth-register')
        self.verify_email_url = reverse('auth-verify-email')
        self.login_url = reverse('auth-login')
        self.article_list_create_url = reverse('article-list')
        # Detail URL for article will be dynamic

        # Test data for the flow
        self.user_e2e_data = {
            'email': 'e2e_user@example.com',
            'password': 'StrongE2EPassword123',
            'first_name': 'E2E',
            'last_name': 'Tester'
        }
        self.category_data = {'name': 'E2E Category'}
        self.article_e2e_data = {
            'title': 'My E2E Test Article',
            'content': 'This article was created during an E2E test flow.',
            # category_id will be set after category creation
        }

    def get_article_detail_url(self, slug):
        return reverse('article-detail', kwargs={'slug': slug})

    @patch('api.views.send_verification_email', return_value=True) # Mock email sending
    def test_user_registers_verifies_logs_in_creates_and_retrieves_article(self, mock_send_email):
        # --- 1. Preparation: Create a Category ---
        category_obj = Category.objects.create(**self.category_data)
        self.article_e2e_data['category'] = category_obj.id


        # --- 2. User Registration ---
        reg_response = self.client.post(self.register_url, self.user_e2e_data, format='json')
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED, f"Registration failed: {reg_response.data}")
        self.assertIn('access', reg_response.data)
        self.assertIn('refresh', reg_response.data)
        registered_user_email = reg_response.data['user']['email']
        self.assertEqual(registered_user_email, self.user_e2e_data['email'])

        # Retrieve the created user from DB to get verification code
        user_in_db = UserModel.objects.get(email=registered_user_email)
        self.assertFalse(user_in_db.is_email_verified)
        self.assertIsNotNone(user_in_db.verification_code)
        verification_code = user_in_db.verification_code

        mock_send_email.assert_called_once()


        # --- 3. Email Verification ---
        verify_payload = {'email': registered_user_email, 'code': verification_code}
        verify_response = self.client.post(self.verify_email_url, verify_payload, format='json')
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK, f"Email verification failed: {verify_response.data}")
        self.assertTrue(verify_response.data['user']['is_email_verified'])
        self.assertIn('access', verify_response.data, "New access token should be issued after verification.")

        user_in_db.refresh_from_db()
        self.assertTrue(user_in_db.is_email_verified)

        # Store the new access token from verification for subsequent authenticated requests
        current_access_token = verify_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {current_access_token}')


        # --- 4. User Login (Optional step, as verification might return tokens. Let's test it anyway) ---
        # Clear credentials to ensure login works independently if needed
        self.client.credentials()
        login_payload = {'login': registered_user_email, 'password': self.user_e2e_data['password']}
        login_response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login failed: {login_response.data}")
        self.assertIn('access', login_response.data)

        # Use the token from login for subsequent requests
        current_access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {current_access_token}')


        # --- 5. Create Article ---
        create_article_response = self.client.post(
            self.article_list_create_url,
            self.article_e2e_data,
            format='json'
        )
        self.assertEqual(create_article_response.status_code, status.HTTP_201_CREATED, f"Article creation failed: {create_article_response.data}")
        self.assertEqual(create_article_response.data['title'], self.article_e2e_data['title'])
        self.assertEqual(create_article_response.data['author']['email'], registered_user_email)
        article_slug = create_article_response.data['slug']
        self.assertTrue(Article.objects.filter(slug=article_slug, author=user_in_db).exists())


        # --- 6. Retrieve Article ---
        # Client should still be authenticated from the last step
        retrieve_article_response = self.client.get(self.get_article_detail_url(article_slug), format='json')
        self.assertEqual(retrieve_article_response.status_code, status.HTTP_200_OK, f"Article retrieval failed: {retrieve_article_response.data}")
        self.assertEqual(retrieve_article_response.data['title'], self.article_e2e_data['title'])
        self.assertEqual(retrieve_article_response.data['content'], self.article_e2e_data['content'])
        self.assertEqual(retrieve_article_response.data['author']['id'], str(user_in_db.id))
        # Check category details (assuming your ArticleSerializer includes expanded category details)
        # Based on previous serializer work, it might be 'category' (ID) and 'category_details' (nested)
        if 'category_details' in retrieve_article_response.data:
             self.assertEqual(retrieve_article_response.data['category_details']['name'], self.category_data['name'])
        elif 'category' in retrieve_article_response.data and isinstance(retrieve_article_response.data['category'], dict):
             self.assertEqual(retrieve_article_response.data['category']['name'], self.category_data['name'])
        elif 'category' in retrieve_article_response.data: # Check if it's just the ID
            self.assertEqual(retrieve_article_response.data['category'], category_obj.id)


        # --- 7. (Optional) Update Article ---
        update_data = {'title': 'My E2E Article - Updated'}
        update_response = self.client.patch(self.get_article_detail_url(article_slug), update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK, f"Article update failed: {update_response.data}")
        self.assertEqual(update_response.data['title'], update_data['title'])


        # --- 8. (Optional) Delete Article ---
        delete_response = self.client.delete(self.get_article_detail_url(article_slug))
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT, f"Article deletion failed: {delete_response.data}")
        self.assertFalse(Article.objects.filter(slug=article_slug).exists())
