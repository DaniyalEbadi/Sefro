from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinLengthValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
import uuid
import random


# =============================================================================
# User Management Models
# =============================================================================

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    verification_code_created = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    def save(self, *args, **kwargs):
        if not self.username and self.email:
            self.username = self.email
        super().save(*args, **kwargs)

    def set_verification_code(self, code):
        self.verification_code = code
        self.verification_code_created = timezone.now()
        self.save()

    def clear_verification_code(self):
        self.verification_code = None
        self.verification_code_created = None
        self.save()

    def is_verification_code_valid(self, code):
        if not self.verification_code or not self.verification_code_created:
            return False
        
        from django.conf import settings
        timeout = getattr(settings, 'EMAIL_VERIFICATION_TIMEOUT', 3600)
        now = timezone.now()
        is_expired = (now - self.verification_code_created).total_seconds() > timeout
        
        return not is_expired and self.verification_code == code
        
    def generate_verification_code(self):
        """Generate a random 6-digit verification code and save it to the user model"""
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.verification_code = code
        self.verification_code_created = timezone.now()
        self.save()
        return code
        
    def verify_code(self, code):
        """Verify that the provided code matches the stored code and is not expired"""
        return self.is_verification_code_valid(code)
        
    @property
    def is_verified(self):
        """Property that returns the email verification status"""
        return self.is_email_verified

    @is_verified.setter
    def is_verified(self, value):
        """Setter for email verification status"""
        self.is_email_verified = value

    class Meta:
        ordering = ['-created_at']


# =============================================================================
# Role and Permission Models
# =============================================================================

class Role(models.Model):
    """Role model for role-based access control"""
    name = models.CharField(max_length=50, unique=True)
    users = models.ManyToManyField(User, related_name="roles", blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Permission model for granular access control"""
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """Many-to-many relationship between roles and permissions"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['role', 'permission']


class UserRole(models.Model):
    """Many-to-many relationship between users and roles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'role']


# =============================================================================
# Content Management Models
# =============================================================================

class Category(models.Model):
    """Category model for organizing articles"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    """Article model for blog posts"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, validators=[MinLengthValidator(5)])
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(max_length=500, blank=True)
    Main_image = models.CharField(max_length=200, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('article-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


# =============================================================================
# Media Management Models
# =============================================================================

class Media(models.Model):
    """Media model for storing image and video URLs related to an article."""
    
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    url = models.URLField()  # Stores the image/video URL
    alt_text = models.CharField(max_length=255, blank=True, null=True)  # For SEO and accessibility
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.media_type.capitalize()} for {self.article.title}"


# =============================================================================
# Engagement Models
# =============================================================================

class Comment(models.Model):
    """Comment model for article discussions"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(validators=[MinLengthValidator(10)])
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.author.username} on {self.article.title}'


class ArticleLike(models.Model):
    """Like model for article reactions"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='article_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['article', 'user']

    def __str__(self):
        return f'{self.user.username} likes {self.article.title}'


class ArticleView(models.Model):
    """View model for tracking article views"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="article_views", null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)  # Track browser/device info
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["article", "ip_address", "user"]  # Better uniqueness constraint

    def __str__(self):
        return f"View of {self.article.title}"












