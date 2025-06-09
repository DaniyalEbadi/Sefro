from django.test import TestCase
from django.utils import timezone
from django.conf import settings
from unittest.mock import patch, MagicMock
import datetime

from api.models import User, Article, Category # Assuming Category is needed for Article tests

class UserModelTests(TestCase):

    def setUp(self):
        # A user instance that can be used by multiple tests
        # Note: In Django tests, the database is typically reset for each test method.
        # However, creating a user here is fine for methods that don't rely on a pristine state
        # or that modify this user instance directly.
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'password123'
        }
        # self.user = User.objects.create_user(**self.user_data) # Not creating here to avoid db hit for non-db tests if any

    def test_create_user_sets_username_from_email_if_not_provided(self):
        user = User.objects.create_user(email='no_username@example.com', password='password123')
        self.assertEqual(user.username, 'no_username@example.com')

    def test_set_verification_code(self):
        user = User.objects.create_user(**self.user_data)
        code = "123456"
        user.set_verification_code(code)
        self.assertEqual(user.verification_code, code)
        self.assertIsNotNone(user.verification_code_created)
        self.assertTrue(timezone.now() - user.verification_code_created < datetime.timedelta(seconds=5))

    def test_clear_verification_code(self):
        user = User.objects.create_user(**self.user_data)
        user.set_verification_code("123456")
        user.clear_verification_code()
        self.assertIsNone(user.verification_code)
        self.assertIsNone(user.verification_code_created)

    def test_generate_verification_code(self):
        user = User.objects.create_user(**self.user_data)
        code = user.generate_verification_code()
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        self.assertEqual(user.verification_code, code)
        self.assertIsNotNone(user.verification_code_created)

    def test_is_verification_code_valid_correct_code(self):
        user = User.objects.create_user(**self.user_data)
        code = "654321"
        user.set_verification_code(code)
        self.assertTrue(user.is_verification_code_valid(code))

    def test_is_verification_code_valid_incorrect_code(self):
        user = User.objects.create_user(**self.user_data)
        user.set_verification_code("111111")
        self.assertFalse(user.is_verification_code_valid("222222"))

    def test_is_verification_code_valid_no_code_set(self):
        user = User.objects.create_user(**self.user_data)
        # user.verification_code and user.verification_code_created are None
        self.assertFalse(user.is_verification_code_valid("123456"))

    def test_is_verification_code_valid_code_expired(self):
        user = User.objects.create_user(**self.user_data)
        code = "789012"
        user.set_verification_code(code)

        # Mock timezone.now() to simulate time passing
        # EMAIL_VERIFICATION_TIMEOUT is in seconds, default is 3600 (1 hour)
        timeout_seconds = getattr(settings, 'EMAIL_VERIFICATION_TIMEOUT', 3600)
        future_time = user.verification_code_created + datetime.timedelta(seconds=timeout_seconds + 60) # 1 minute past expiry

        with patch('django.utils.timezone.now', MagicMock(return_value=future_time)):
            self.assertFalse(user.is_verification_code_valid(code))

    def test_is_verification_code_valid_code_just_before_expiry(self):
        user = User.objects.create_user(**self.user_data)
        code = "000000"
        user.set_verification_code(code)

        timeout_seconds = getattr(settings, 'EMAIL_VERIFICATION_TIMEOUT', 3600)
        # Simulate time just before expiry
        almost_expired_time = user.verification_code_created + datetime.timedelta(seconds=timeout_seconds - 10)

        with patch('django.utils.timezone.now', MagicMock(return_value=almost_expired_time)):
            self.assertTrue(user.is_verification_code_valid(code))

    def test_verify_code_method_calls_is_verification_code_valid(self):
        user = User.objects.create_user(**self.user_data)
        code = "121212"
        # Mock is_verification_code_valid to check if it's called
        with patch.object(user, 'is_verification_code_valid', return_value=True) as mock_is_valid:
            user.verify_code(code)
            mock_is_valid.assert_called_once_with(code)


class ArticleModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create user and category once for all test methods in this class
        cls.user = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='password'
        )
        cls.category = Category.objects.create(name='Test Category For Articles')

    def test_article_slug_auto_generation(self):
        article = Article.objects.create(
            title='A Test Article Title',
            content='Some content.',
            author=self.user,
            category=self.category
        )
        self.assertEqual(article.slug, 'a-test-article-title')

    def test_article_uses_provided_slug(self):
        article = Article.objects.create(
            title='Another Test Article',
            slug='custom-slug-test',
            content='More content.',
            author=self.user,
            category=self.category
        )
        self.assertEqual(article.slug, 'custom-slug-test')

    def test_published_at_set_on_status_change_to_published(self):
        article = Article.objects.create(
            title='Publish Me',
            content='Content to be published.',
            author=self.user,
            category=self.category,
            status='draft' # Initial status
        )
        self.assertIsNone(article.published_at)

        article.status = 'published'
        article.save()
        article.refresh_from_db() # Ensure we get the latest state from DB
        self.assertIsNotNone(article.published_at)
        self.assertTrue(timezone.now() - article.published_at < datetime.timedelta(seconds=5))

    def test_published_at_not_overwritten_if_already_set(self):
        initial_publish_time = timezone.now() - datetime.timedelta(days=1)
        article = Article.objects.create(
            title='Already Published Article',
            content='Old content.',
            author=self.user,
            category=self.category,
            status='published',
            published_at=initial_publish_time
        )

        article.content = 'Updated old content.' # Make a change
        article.save()
        article.refresh_from_db()

        # Comparing with a tolerance due to potential microsecond differences on save
        self.assertAlmostEqual(article.published_at, initial_publish_time, delta=datetime.timedelta(seconds=1))


    def test_published_at_not_set_if_status_not_published(self):
        article = Article.objects.create(
            title='Draft Article',
            content='Draft content.',
            author=self.user,
            category=self.category,
            status='draft'
        )
        article.save() # Save with draft status
        self.assertIsNone(article.published_at)

        article.status = 'review'
        article.save() # Save with review status
        self.assertIsNone(article.published_at)

# Ensure Django can find and run these tests
# You might need to run python manage.py test api.tests.unit.test_models
