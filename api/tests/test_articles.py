from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from api.models import Category, Article, Comment, Media, ArticleLike, ArticleView

User = get_user_model()

class ArticleTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.article = Article.objects.create(
            title='Test Article',
            content='Test Content',
            author=self.user,
            category=self.category
        )

    def test_create_article(self):
        url = reverse('article-list')
        data = {
            'title': 'New Article',
            'content': 'New Content',
            'category': self.category.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 2)

    def test_article_detail(self):
        url = reverse('article-detail', kwargs={'slug': self.article.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Article')

    def test_article_update(self):
        url = reverse('article-detail', kwargs={'slug': self.article.slug})
        data = {
            'title': 'Updated Article',
            'content': 'Updated Content'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Article.objects.get(slug=self.article.slug).title, 'Updated Article')

    def test_article_delete(self):
        url = reverse('article-detail', kwargs={'slug': self.article.slug})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Article.objects.count(), 0)

class CategoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

    def test_create_category(self):
        url = reverse('category-list')
        data = {
            'name': 'New Category',
            'slug': 'new-category'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)

    def test_category_hierarchy(self):
        url = reverse('category-list')
        data = {
            'name': 'Child Category',
            'slug': 'child-category',
            'parent': self.category.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.get(slug='child-category').parent, self.category)

class CommentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Test Category')
        self.article = Article.objects.create(
            title='Test Article',
            content='Test Content',
            author=self.user,
            category=self.category
        )

    def test_create_comment(self):
        url = reverse('comment-list')
        data = {
            'article': self.article.id,
            'content': 'Test Comment'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_nested_comments(self):
        parent_comment = Comment.objects.create(
            article=self.article,
            author=self.user,
            content='Parent Comment'
        )
        url = reverse('comment-list')
        data = {
            'article': self.article.id,
            'content': 'Child Comment',
            'parent': parent_comment.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.get(content='Child Comment').parent, parent_comment)

class ArticleInteractionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Test Category')
        self.article = Article.objects.create(
            title='Test Article',
            content='Test Content',
            author=self.user,
            category=self.category
        )

    def test_article_like(self):
        url = reverse('article-like', kwargs={'slug': self.article.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(ArticleLike.objects.filter(article=self.article, user=self.user).exists())

    def test_article_view(self):
        url = reverse('article-view', kwargs={'slug': self.article.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(ArticleView.objects.filter(article=self.article, user=self.user).exists()) 