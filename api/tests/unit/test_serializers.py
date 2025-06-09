from django.test import TestCase
from django.contrib.auth.password_validation import get_password_validators
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers # For ValidationError

from api.serializers import UserSerializer, ArticleSerializer
from api.models import User, Article, Category # Article, Category needed for ArticleSerializer tests

# Mock request for context if needed, especially for ArticleSerializer
class MockRequest:
    def __init__(self, user=None):
        self.user = user

class UserSerializerTests(TestCase):

    def setUp(self):
        # Ensure default password validators are used for tests
        settings.AUTH_PASSWORD_VALIDATORS = [
            {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
            {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
            {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
            {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
        ]
        self.validator = get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)

        self.user_data_valid = {
            'email': 'test@example.com',
            'password': 'ValidPassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user_data_with_username = {
            **self.user_data_valid,
            'username': 'testuser',
        }

    def test_user_serializer_valid_data_no_username(self):
        serializer = UserSerializer(data=self.user_data_valid)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, self.user_data_valid['email'])
        self.assertTrue(user.check_password(self.user_data_valid['password']))
        # Check username generation (simple case)
        expected_username_base = self.user_data_valid['email'].split('@')[0]
        self.assertTrue(user.username.startswith(expected_username_base))

    def test_user_serializer_valid_data_with_username(self):
        serializer = UserSerializer(data=self.user_data_with_username)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, self.user_data_with_username['username'])

    def test_user_serializer_username_generation_conflict(self):
        # Create a user that would conflict with the auto-generated username
        User.objects.create_user(
            email='conflict@example.com',
            username='test', # This is what 'test@example.com' would generate first
            password='password123'
        )
        serializer = UserSerializer(data=self.user_data_valid) # uses 'test@example.com'
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertNotEqual(user.username, 'test') # Should have been suffixed
        self.assertTrue(user.username.startswith('test'))
        self.assertTrue(any(char.isdigit() for char in user.username.replace('test','')))


    def test_user_serializer_missing_required_fields(self):
        invalid_data = self.user_data_valid.copy()
        del invalid_data['email']
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

        invalid_data_no_fn = self.user_data_valid.copy()
        del invalid_data_no_fn['first_name']
        serializer_no_fn = UserSerializer(data=invalid_data_no_fn)
        self.assertFalse(serializer_no_fn.is_valid())
        self.assertIn('first_name', serializer_no_fn.errors)

        invalid_data_no_ln = self.user_data_valid.copy()
        del invalid_data_no_ln['last_name']
        serializer_no_ln = UserSerializer(data=invalid_data_no_ln)
        self.assertFalse(serializer_no_ln.is_valid())
        self.assertIn('last_name', serializer_no_ln.errors)

    def test_user_serializer_invalid_password(self):
        # Password too short
        invalid_data = {**self.user_data_valid, 'password': 'short'}
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

        # Password purely numeric (if NumericPasswordValidator is on)
        invalid_data_numeric = {**self.user_data_valid, 'password': '123456789'}
        serializer_numeric = UserSerializer(data=invalid_data_numeric)
        self.assertFalse(serializer_numeric.is_valid())
        self.assertIn('password', serializer_numeric.errors)


    def test_user_serializer_representation(self):
        user = User.objects.create_user(**self.user_data_with_username)
        serializer = UserSerializer(instance=user)
        data = serializer.data
        self.assertEqual(data['email'], self.user_data_with_username['email'])
        self.assertEqual(data['username'], self.user_data_with_username['username'])
        self.assertEqual(data['first_name'], self.user_data_with_username['first_name'])
        self.assertNotIn('password', data) # Password should be write-only
        self.assertIn('id', data)
        self.assertIn('is_email_verified', data)
        self.assertFalse(data['is_email_verified']) # Default

    def test_user_serializer_update(self):
        user = User.objects.create_user(**self.user_data_with_username)
        update_data = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'password': 'NewValidPassword456'
        }
        serializer = UserSerializer(instance=user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()

        self.assertEqual(updated_user.first_name, update_data['first_name'])
        self.assertEqual(updated_user.last_name, update_data['last_name'])
        self.assertTrue(updated_user.check_password(update_data['password']))
        self.assertEqual(updated_user.email, user.email) # Email should not change unless provided

    def test_user_serializer_update_without_password(self):
        user = User.objects.create_user(**self.user_data_with_username)
        original_password_hash = user.password
        update_data = {'first_name': 'UpdatedAgain'}

        serializer = UserSerializer(instance=user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()

        self.assertEqual(updated_user.first_name, update_data['first_name'])
        self.assertEqual(updated_user.password, original_password_hash) # Password should not change


class ArticleSerializerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author_user = User.objects.create_user(
            email='author@example.com', username='author', password='password123'
        )
        cls.category_obj = Category.objects.create(name='Test Category')

        cls.article_data_valid = {
            'title': 'A Valid Article Title',
            'content': 'This is the content of the article.',
            'category_id': cls.category_obj.id # Pass ID for writable nested field if not read_only
        }
        # If category is represented by its ID on write:
        # For create, category might need to be passed as an ID or a pk related field
        # The current ArticleSerializer has category = CategorySerializer(read_only=True)
        # This means for create/update, we'd likely set category directly on the model or pass its ID
        # to a writable field if one existed.
        # The serializer's create method: validated_data['author'] = self.context['request'].user
        # So, we need to provide 'request' in context.

    def setUp(self):
        # For ArticleSerializer create, it expects request in context
        self.mock_request = MockRequest(user=self.author_user)
        self.article_data_for_create = {
            'title': 'New Article from Serializer',
            'content': 'Content here.',
            'category': self.category_obj.id # Assuming category is set via its ID on create
                                             # This depends on how category is handled in serializer.
                                             # If CategorySerializer is read_only, we might need a WritableField.
                                             # For now, let's assume 'category' field in validated_data will be the ID.
        }


    def test_article_serializer_valid_data_create(self):
        # The ArticleSerializer has author and category as read-only nested serializers.
        # For creation, 'author' is set from context. 'category' needs to be handled.
        # Let's adjust the test based on typical DRF patterns.
        # If 'category' is read_only via CategorySerializer, we'd typically pass 'category_id'.

        data_for_create = {
            'title': 'Test Article Creation',
            'content': 'Some content for creation.',
            'category': self.category_obj.id # Pass the ID
        }

        # serializer = ArticleSerializer(data=data_for_create, context={'request': self.mock_request})
        # The ArticleSerializer by default would try to use CategorySerializer for 'category' field.
        # If CategorySerializer is read_only, 'category' field itself is read_only.
        # We need to ensure 'category_id' is a writable field or that 'category' can accept a PK.
        # Let's assume for now the serializer is set up to accept category PK for creation.
        # A common way is to have `category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())`
        # OR to make the nested serializer writable (more complex).
        # Given the current serializer definition: `category = CategorySerializer(read_only=True)`
        # This means 'category' field itself is not for writing.
        # We should instead pass 'category_id' or set it directly before serializer.save() if it's not a serializer field.
        # For this test, we'll assume 'category' in validated_data will be an ID that the .create() or .save() handles.
        # The serializer's Meta class does not list 'category' as a writeable field if CategorySerializer is read_only.
        # Let's assume the model's 'category' field will be assigned directly.

        # Re-checking ArticleSerializer: fields = '__all__'. This means 'category' (the model field) is included.
        # If 'category' is a ForeignKey, DRF handles it by default as PrimaryKeyRelatedField on write if not specified otherwise.
        # So, data_for_create['category'] = self.category_obj.id should work.

        serializer = ArticleSerializer(data=data_for_create, context={'request': self.mock_request})

        if not serializer.is_valid():
            print("ArticleSerializer errors:", serializer.errors) # Debug output
        self.assertTrue(serializer.is_valid(), serializer.errors)

        article = serializer.save() # author is set in serializer.create()
        self.assertIsNotNone(article)
        self.assertEqual(article.title, data_for_create['title'])
        self.assertEqual(article.author, self.author_user)
        self.assertEqual(article.category, self.category_obj)


    def test_article_serializer_representation(self):
        article = Article.objects.create(
            title="Represent Me",
            content="Content for representation.",
            author=self.author_user,
            category=self.category_obj
        )
        # Manually create some likes and views for the method fields
        ArticleLike.objects.create(article=article, user=self.author_user)
        ArticleView.objects.create(article=article, user=self.author_user) # Assuming ArticleLike/View models exist for this

        serializer = ArticleSerializer(instance=article, context={'request': self.mock_request})
        data = serializer.data

        self.assertEqual(data['title'], article.title)
        self.assertIn('author', data)
        self.assertEqual(data['author']['id'], str(self.author_user.id)) # Nested UserSerializer
        self.assertIn('category_details', data) # Expect nested details here
        self.assertEqual(data['category_details']['id'], self.category_obj.id)
        self.assertIn('category', data) # Expect category ID here
        self.assertEqual(data['category'], self.category_obj.id)
        self.assertIn('media_files', data) # Should be empty list if none added
        self.assertEqual(len(data['media_files']), 0)
        self.assertIn('comments', data) # Should be empty list
        self.assertEqual(len(data['comments']), 0)
        self.assertIn('likes_count', data)
        # self.assertEqual(data['likes_count'], 1) # Requires ArticleLike model and instance
        self.assertIn('views_count', data)
        # self.assertEqual(data['views_count'], 1) # Requires ArticleView model and instance
        self.assertIn('slug', data) # read_only
        self.assertEqual(data['slug'], 'represent-me')


    def test_article_serializer_title_too_short(self):
        # Based on Article model MinLengthValidator(5) for title
        invalid_data = {**self.article_data_for_create, 'title': 'Bye'}
        serializer = ArticleSerializer(data=invalid_data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_article_serializer_missing_content(self):
        invalid_data = self.article_data_for_create.copy()
        del invalid_data['content']
        serializer = ArticleSerializer(data=invalid_data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid()) # content is a required model field
        self.assertIn('content', serializer.errors)

# Need to import ArticleLike and ArticleView if used in tests
from api.models import ArticleLike, ArticleView
