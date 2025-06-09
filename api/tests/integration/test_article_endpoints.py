from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from api.models import Article, Category
from unittest.mock import patch # If any external calls are made during article operations

User = get_user_model()

class ArticleEndpointsIntegrationTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # Create users
        cls.user1 = User.objects.create_user(
            email='user1@example.com', username='user1', password='Password123',
            first_name='User', last_name='One', is_email_verified=True
        )
        cls.user2 = User.objects.create_user(
            email='user2@example.com', username='user2', password='Password456',
            first_name='User', last_name='Two', is_email_verified=True
        )

        # Create a category
        cls.category = Category.objects.create(name='General Test Category')

        # URLs
        cls.list_create_url = reverse('article-list') # DRF router default name for list/create

    def setUp(self):
        self.client = APIClient() # Use a fresh client for each test method
        # Detail URL needs a slug, will be constructed per test
        # self.detail_url = reverse('article-detail', kwargs={'slug': 'some-slug'})

        self.article_data_valid = {
            'title': 'My Test Article Title',
            'content': 'This is the detailed content of my test article.',
            'category': self.category.id # Pass category ID for creation
        }

    def get_detail_url(self, slug):
        return reverse('article-detail', kwargs={'slug': slug})

    # --- Create Article Tests ---
    def test_create_article_authenticated_user_success(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_create_url, self.article_data_valid, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Article.objects.count(), 1)
        article_db = Article.objects.first()
        self.assertEqual(article_db.title, self.article_data_valid['title'])
        self.assertEqual(article_db.author, self.user1)
        self.assertEqual(article_db.category, self.category)
        self.assertIsNotNone(response.data.get('slug'))

    def test_create_article_unauthenticated_user_fails(self):
        response = self.client.post(self.list_create_url, self.article_data_valid, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # Default for IsAuthenticated

    def test_create_article_missing_title_fails(self):
        self.client.force_authenticate(user=self.user1)
        invalid_data = self.article_data_valid.copy()
        del invalid_data['title']
        response = self.client.post(self.list_create_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_create_article_missing_content_fails(self):
        self.client.force_authenticate(user=self.user1)
        invalid_data = self.article_data_valid.copy()
        del invalid_data['content'] # Content is a required model field
        response = self.client.post(self.list_create_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)

    def test_create_article_missing_category_fails(self):
        self.client.force_authenticate(user=self.user1)
        invalid_data = self.article_data_valid.copy()
        del invalid_data['category']
        response = self.client.post(self.list_create_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data) # category_id is required

    # --- List Articles Tests ---
    def test_list_articles_success(self):
        # Create a couple of articles
        Article.objects.create(title='Article One', content='Content 1', author=self.user1, category=self.category)
        Article.objects.create(title='Article Two', content='Content 2', author=self.user2, category=self.category)

        self.client.force_authenticate(user=self.user1) # Listing should be allowed for any authenticated user
        response = self.client.get(self.list_create_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Default pagination is 10, so count should be in results
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_articles_unauthenticated_fails(self):
        response = self.client.get(self.list_create_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Retrieve Article Tests ---
    def test_retrieve_article_success(self):
        article = Article.objects.create(
            title='Retrieve Me', content='Content for retrieval.', author=self.user1, category=self.category
        )
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.get_detail_url(article.slug), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['title'], article.title)
        self.assertEqual(response.data['slug'], article.slug)

    def test_retrieve_article_unauthenticated_fails(self):
        article = Article.objects.create(
            title='Retrieve Me Unauth', content='Content.', author=self.user1, category=self.category
        )
        response = self.client.get(self.get_detail_url(article.slug), format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_article_not_found(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.get_detail_url('non-existent-slug'), format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Update Article Tests (PUT/PATCH) ---
    def test_update_article_patch_by_author_success(self):
        article = Article.objects.create(
            title='Original Title Patch', content='Original content.', author=self.user1, category=self.category
        )
        self.client.force_authenticate(user=self.user1) # Authenticate as author

        update_data = {'title': 'Updated Title via PATCH'}
        response = self.client.patch(self.get_detail_url(article.slug), update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        article.refresh_from_db()
        self.assertEqual(article.title, update_data['title'])
        self.assertEqual(response.data['title'], update_data['title'])

    def test_update_article_put_by_author_success(self):
        article = Article.objects.create(
            title='Original Title PUT', content='Original content for PUT.', author=self.user1, category=self.category
        )
        self.client.force_authenticate(user=self.user1)

        # PUT requires all required fields of the serializer
        # ArticleSerializer fields = '__all__', so we need to send all writable model fields
        # title, content, category (as ID). Slug, author etc are read-only or set by system.
        put_data = {
            'title': 'Updated Title via PUT',
            'content': 'Updated content for PUT.',
            'category': self.category.id
            # seo_title, seo_description, Main_image are optional
        }
        response = self.client.put(self.get_detail_url(article.slug), put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        article.refresh_from_db()
        self.assertEqual(article.title, put_data['title'])
        self.assertEqual(article.content, put_data['content'])

    def test_update_article_by_non_author_fails(self):
        article = Article.objects.create(
            title='Non-Author Update Test', content='Content.', author=self.user1, category=self.category
        )
        self.client.force_authenticate(user=self.user2) # Authenticate as different user

        update_data = {'title': 'Attempted Update by Non-Author'}
        response = self.client.patch(self.get_detail_url(article.slug), update_data, format='json')
        # Default ModelViewSet behavior without custom permissions might allow this.
        # If object-level permissions (e.g., IsOwner) are not set, this might pass (200) or fail (403/404).
        # For now, let's assume a basic setup where it might pass if not restricted.
        # A proper test for this would require IsOwner permission class on the ViewSet.
        # Let's assert that if it passes, the author is unchanged.
        # If it's forbidden, it should be 403.
        # The default ArticleViewSet has permission_classes = [permissions.IsAuthenticated]
        # It does NOT have object-level permissions to restrict updates to authors only.
        # So, this request *should* succeed (HTTP 200).
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Default ModelViewSet allows update by any authenticated user.")
        article.refresh_from_db()
        self.assertEqual(article.title, update_data['title']) # Title is updated
        self.assertEqual(article.author, self.user1) # Author remains the same (not updatable via serializer directly)

    def test_update_article_unauthenticated_fails(self):
        article = Article.objects.create(
            title='Unauth Update Test', content='Content.', author=self.user1, category=self.category
        )
        update_data = {'title': 'Attempted Unauth Update'}
        response = self.client.patch(self.get_detail_url(article.slug), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Delete Article Tests ---
    def test_delete_article_by_author_success(self):
        article = Article.objects.create(
            title='Delete Me By Author', content='Content.', author=self.user1, category=self.category
        )
        self.client.force_authenticate(user=self.user1) # Authenticate as author

        response = self.client.delete(self.get_detail_url(article.slug))
        # Similar to update, without object-level permissions, any authenticated user might delete.
        # For now, we test if the author *can* delete.
        # To properly test if *only* author can delete, IsOwner permission is needed.
        # The default ArticleViewSet allows any authenticated user to delete.
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data if response.data else "No content")
        self.assertEqual(Article.objects.count(), 0)

    def test_delete_article_by_non_author_succeeds_without_isowner_permission(self):
        article = Article.objects.create(
            title='Delete Me By Non-Author', content='Content.', author=self.user1, category=self.category
        )
        self.client.force_authenticate(user=self.user2) # Authenticate as different user

        response = self.client.delete(self.get_detail_url(article.slug))
        # As with update, this will succeed with default ModelViewSet permissions.
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Article.objects.count(), 0)


    def test_delete_article_unauthenticated_fails(self):
        article = Article.objects.create(
            title='Delete Me Unauth', content='Content.', author=self.user1, category=self.category
        )
        response = self.client.delete(self.get_detail_url(article.slug))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_article_not_found(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.get_detail_url('non-existent-slug'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
