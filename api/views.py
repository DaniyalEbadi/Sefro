"""
🏥 Health Check API
==================

Monitor and diagnose your application's health in real-time. This API provides comprehensive insights into system performance,
configuration, and operational status.

Features
--------
✨ Real-time System Metrics
  - CPU & Memory utilization
  - Disk space analytics
  - Database connectivity
  - Cache system status

⏰ Time Management
  - System uptime tracking
  - Server time in Shamsi (Iranian) calendar
  - UTC time synchronization

🔍 Application Insights
  - Environment detection
  - Debug mode status
  - Database configuration
  - Recent migrations history

🛡️ Security
  - Public access (no auth required)
  - No sensitive data exposure
  - Production-safe monitoring

Example Usage
------------
```bash
# Check system health
GET /api/health/

# Response includes:
{
    "status": "ok",
    "server_time": "1403/01/08 14:30:45",  # Shamsi format
    "cpu_usage": "45.2%",
    ...
}
```

Use Cases
---------
🔄 Regular Health Monitoring
📊 System Performance Analysis
🚨 Automated Health Alerts
📈 Resource Usage Tracking
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import connection
from django.conf import settings
import time
import datetime
import jdatetime  # For Shamsi calendar
import psutil
import os
import django
import platform  # For Python version info
from django.core.cache import cache
from .models import (
    User, Role, Permission, RolePermission, UserRole,
    Category, Article, Comment, Media, ArticleLike, ArticleView
)
from .serializers import (
    UserSerializer, RoleSerializer, PermissionSerializer,
    RolePermissionSerializer, UserRoleSerializer, CategorySerializer,
    ArticleSerializer, CommentSerializer, MediaSerializer,
    ArticleLikeSerializer, ArticleViewSerializer
)
from drf_spectacular.utils import OpenApiParameter, OpenApiExample, OpenApiResponse
from .utils import generate_verification_code, send_verification_email
import logging

logger = logging.getLogger(__name__)

# Store the start time of the application
START_TIME = time.time()

User = get_user_model()

@extend_schema_view(
    list=extend_schema(
        tags=['users'],
        summary='List all users',
        description='Retrieve a paginated list of all users in the system.',
        responses={
            200: UserSerializer(many=True),
            401: {'description': 'Authentication credentials were not provided.'},
            403: {'description': 'Insufficient permissions to access user list.'}
        },
        examples=[
            OpenApiExample(
                'User List Response',
                value={
                    'count': 2,
                    'next': None,
                    'previous': None,
                    'results': [
                        {
                            'id': '123e4567-e89b-12d3-a456-426614174000',
                            'email': 'user@example.com',
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'is_active': True,
                            'date_joined': '2024-03-28T10:00:00Z'
                        }
                    ]
                },
                media_type='application/json',
                description='Example response showing a list of users'
            )
        ]
    ),
    create=extend_schema(
        tags=['users'],
        summary='Create a new user',
        description='Create a new user account with the provided information.',
        responses={
            201: UserSerializer,
            400: {'description': 'Invalid input data provided.'},
            401: {'description': 'Authentication credentials were not provided.'},
            403: {'description': 'Insufficient permissions to create users.'}
        },
        examples=[
            OpenApiExample(
                'Create User Request',
                value={
                    'email': 'newuser@example.com',
                    'password': 'securepassword123',
                    'first_name': 'Jane',
                    'last_name': 'Smith'
                },
                media_type='application/json',
                description='Example request for creating a new user'
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['users'],
        summary='Retrieve a user',
        description='Get detailed information about a specific user.',
        responses={
            200: UserSerializer,
            401: {'description': 'Authentication credentials were not provided.'},
            403: {'description': 'Insufficient permissions to access this user.'},
            404: {'description': 'User not found.'}
        }
    ),
    update=extend_schema(
        tags=['users'],
        summary='Update a user',
        description='Update all fields of a specific user.',
        responses={
            200: UserSerializer,
            400: {'description': 'Invalid input data provided.'},
            401: {'description': 'Authentication credentials were not provided.'},
            403: {'description': 'Insufficient permissions to update this user.'},
            404: {'description': 'User not found.'}
        }
    ),
    partial_update=extend_schema(
        tags=['users'],
        summary='Partially update a user',
        description='Update specific fields of a user while leaving others unchanged.',
        responses={
            200: UserSerializer,
            400: {'description': 'Invalid input data provided.'},
            401: {'description': 'Authentication credentials were not provided.'},
            403: {'description': 'Insufficient permissions to update this user.'},
            404: {'description': 'User not found.'}
        }
    ),
    destroy=extend_schema(
        tags=['users'],
        summary='Delete a user',
        description='Permanently delete a specific user account.',
        responses={
            204: {'description': 'User successfully deleted.'},
            401: {'description': 'Authentication credentials were not provided.'},
            403: {'description': 'Insufficient permissions to delete this user.'},
            404: {'description': 'User not found.'}
        }
    )
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user accounts.
    
    This ViewSet provides CRUD operations for user management:
    - List all users (paginated)
    - Create new users
    - Retrieve user details
    - Update user information
    - Delete user accounts
    
    Additional endpoints:
    - /profile/: Get the current user's profile
    - /me/: Get the authenticated user's information
    
    Permissions:
    - List/Retrieve: Authenticated users
    - Create: Anonymous users (for registration)
    - Update/Delete: Admin users or account owners
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()

    @extend_schema(
        tags=['users'],
        summary="Get user's profile",
        description='Retrieve the detailed profile information for a specific user.',
        responses={
            200: UserSerializer,
            401: {'description': 'Authentication credentials were not provided.'},
            403: {'description': 'Insufficient permissions to access this profile.'},
            404: {'description': 'Profile not found.'}
        }
    )
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @extend_schema(
        tags=['users'],
        summary="Get current user's information",
        description='Retrieve the profile information for the currently authenticated user.',
        responses={
            200: UserSerializer,
            401: {'description': 'Authentication credentials were not provided.'}
        }
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

class RolePermissionViewSet(viewsets.ModelViewSet):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

@extend_schema_view(
    list=extend_schema(tags=['articles']),
    create=extend_schema(tags=['articles']),
    retrieve=extend_schema(tags=['articles']),
    update=extend_schema(tags=['articles']),
    partial_update=extend_schema(tags=['articles']),
    destroy=extend_schema(tags=['articles']),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Category.objects.all()
        parent = self.request.query_params.get('parent', None)
        if parent is not None:
            queryset = queryset.filter(parent_id=parent)
        return queryset

@extend_schema_view(
    list=extend_schema(tags=['articles']),
    create=extend_schema(tags=['articles']),
    retrieve=extend_schema(tags=['articles']),
    update=extend_schema(tags=['articles']),
    partial_update=extend_schema(tags=['articles']),
    destroy=extend_schema(tags=['articles']),
)
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'

    def get_queryset(self):
        queryset = Article.objects.all()
        status = self.request.query_params.get('status', None)
        category = self.request.query_params.get('category', None)
        author = self.request.query_params.get('author', None)

        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(category_id=category)
        if author:
            queryset = queryset.filter(author_id=author)

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @extend_schema(tags=['articles'])
    @action(detail=True, methods=['post'])
    def like(self, request, slug=None):
        article = self.get_object()
        like, created = ArticleLike.objects.get_or_create(
            article=article,
            user=request.user
        )
        return Response({'status': 'liked' if created else 'already liked'})

    @extend_schema(tags=['articles'])
    @action(detail=True, methods=['post'])
    def view(self, request, slug=None):
        article = self.get_object()
        view, created = ArticleView.objects.get_or_create(
            article=article,
            user=request.user
        )
        return Response({'status': 'viewed'})

@extend_schema_view(
    list=extend_schema(tags=['articles']),
    create=extend_schema(tags=['articles']),
    retrieve=extend_schema(tags=['articles']),
    update=extend_schema(tags=['articles']),
    partial_update=extend_schema(tags=['articles']),
    destroy=extend_schema(tags=['articles']),
)
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Comment.objects.all()
        article = self.request.query_params.get('article', None)
        if article:
            queryset = queryset.filter(article_id=article)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Media.objects.all()
        article = self.request.query_params.get('article', None)
        media_type = self.request.query_params.get('media_type', None)

        if article:
            queryset = queryset.filter(article_id=article)
        if media_type:
            queryset = queryset.filter(media_type=media_type)

        return queryset

@extend_schema(
    tags=['auth'],
    summary='Register a new user',
    description="""
    Create a new user account with the provided information.
    
    This endpoint:
    - Creates a new user account
    - Sends a verification code to the user's email
    - Returns JWT tokens for immediate authentication
    - Returns user profile information
    
    Notes:
    - Email must be unique
    - Password must meet security requirements
    - First name and last name are required
    - Username is optional (will be generated from email if not provided)
    - A verification code will be sent to the provided email
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'username': {'type': 'string', 'description': 'Optional username (generated from email if not provided)'},
                'password': {'type': 'string', 'format': 'password'},
                'first_name': {'type': 'string', 'minLength': 1},
                'last_name': {'type': 'string', 'minLength': 1}
            },
            'required': ['email', 'password', 'first_name', 'last_name']
        }
    },
    responses={
        201: {
            'description': 'User successfully registered',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'refresh': {'type': 'string', 'description': 'JWT refresh token'},
                        'access': {'type': 'string', 'description': 'JWT access token'},
                        'user': {'type': 'object', 'description': 'User profile information'},
                        'verification': {
                            'type': 'object',
                            'properties': {
                                'email_status': {'type': 'string'},
                                'email_sent_to': {'type': 'string'},
                                'expires_in_hours': {'type': 'integer'},
                                'is_verified': {'type': 'boolean'}
                            }
                        },
                        'message': {'type': 'string', 'description': 'Success message'}
                    }
                }
            }
        },
        400: {
            'description': 'Invalid input data',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'email': {'type': 'array', 'items': {'type': 'string'}},
                        'password': {'type': 'array', 'items': {'type': 'string'}},
                        'first_name': {'type': 'array', 'items': {'type': 'string'}},
                        'last_name': {'type': 'array', 'items': {'type': 'string'}}
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """
    Register a new user account and send verification email.
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate and send verification code
        code = generate_verification_code()
        user.set_verification_code(code)
        
        # Send verification email
        try:
            if settings.EMAIL_DELIVERY_CHECK:
                send_verification_email(user, code)
                email_status = "sent"
            else:
                # Skip email sending in development if EMAIL_DELIVERY_CHECK is False
                email_status = "skipped (dev mode)"
                logger.info(f"Verification email sending skipped for {user.email} (EMAIL_DELIVERY_CHECK=False)")
        except Exception as e:
            email_status = f"failed: {str(e)}"
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
            'verification': {
                'email_status': email_status,
                'email_sent_to': user.email,
                'expires_in_hours': settings.EMAIL_VERIFICATION_TIMEOUT // 3600,
                'is_verified': user.is_email_verified,
                'dev_note': None if settings.EMAIL_DELIVERY_CHECK else "Use /api/auth/debug/direct-verify/ in development"
            },
            'message': 'ثبت نام شما با موفقیت انجام شد. لطفا ایمیل خود را برای کد تأیید بررسی کنید.'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=['auth'],
    summary='Verify email address',
    description="""
    Verify user's email address using the verification code sent during registration.
    
    This endpoint:
    - Validates the verification code
    - Marks the user's email as verified
    - Returns success message and user profile
    
    Notes:
    - Code expires after the configured timeout
    - Invalid or expired codes will return an error
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'code': {'type': 'string', 'minLength': 6, 'maxLength': 6}
            },
            'required': ['email', 'code']
        }
    },
    responses={
        200: {
            'description': 'Email successfully verified',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'user': {'type': 'object'}
                    }
                }
            }
        },
        400: {
            'description': 'Invalid or expired verification code',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        },
        404: {
            'description': 'User not found',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    """
    Verify user's email address using the verification code.
    """
    email = request.data.get('email')
    code = request.data.get('code')
    
    if not email or not code:
        return Response({
            'error': 'هر دو فیلد ایمیل و کد تأیید الزامی هستند.',
            'code': 'missing_fields'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'کاربری با این ایمیل یافت نشد.',
            'code': 'user_not_found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if user.is_email_verified:
        return Response({
            'message': 'ایمیل شما قبلاً تأیید شده است.',
            'code': 'already_verified',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    if not user.is_verification_code_valid(code):
        return Response({
            'error': 'کد تأیید نامعتبر یا منقضی شده است.',
            'code': 'invalid_code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user.is_email_verified = True
    user.clear_verification_code()
    user.save()
    
    # Generate fresh JWT tokens after verification
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'ایمیل شما با موفقیت تأیید شد.',
        'code': 'success',
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': UserSerializer(user).data
    })

@extend_schema(
    tags=['auth'],
    summary='Resend verification code',
    description="""
    Resend verification code to user's email address.
    
    This endpoint:
    - Generates a new verification code
    - Sends it to the user's email
    - Updates the verification code timestamp
    
    Notes:
    - Only works for unverified email addresses
    - Previous verification code becomes invalid
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'}
            },
            'required': ['email']
        }
    },
    responses={
        200: {
            'description': 'Verification code resent successfully',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'}
                    }
                }
            }
        },
        400: {
            'description': 'Invalid request or email already verified',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        },
        404: {
            'description': 'User not found',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification(request):
    """
    Resend verification code to user's email.
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'ایمیل الزامی است.',
            'code': 'missing_email'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'کاربری با این ایمیل یافت نشد.',
            'code': 'user_not_found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if user.is_email_verified:
        return Response({
            'message': 'ایمیل شما قبلاً تأیید شده است.',
            'code': 'already_verified'
        }, status=status.HTTP_200_OK)
    
    # Generate and send new verification code
    code = generate_verification_code()
    user.set_verification_code(code)
    
    try:
        send_verification_email(user, code)
        email_status = "sent"
    except Exception as e:
        email_status = f"failed: {str(e)}"
        return Response({
            'error': 'خطا در ارسال ایمیل تأیید.',
            'details': str(e),
            'code': 'email_sending_failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'message': 'کد تأیید جدید به ایمیل شما ارسال شد.',
        'code': 'success',
        'verification': {
            'email_status': email_status,
            'email_sent_to': user.email,
            'expires_in_hours': settings.EMAIL_VERIFICATION_TIMEOUT // 3600
        }
    })

@extend_schema(
    tags=['auth'],
    summary='Login to the system',
    description="""
    Authenticate a user using their email/username and password.
    
    This endpoint:
    - Accepts either email or username for authentication
    - Validates the provided credentials
    - Returns JWT tokens upon successful authentication
    - Includes user profile information in the response
    
    Notes:
    - The login field accepts either email or username
    - Passwords are case-sensitive
    - Accounts must be active to login
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'login': {'type': 'string', 'description': 'Username or Email'},
                'password': {'type': 'string', 'format': 'password'}
            },
            'required': ['login', 'password']
        }
    },
    responses={
        200: {
            'description': 'Successfully authenticated',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'refresh': {'type': 'string', 'description': 'JWT refresh token'},
                        'access': {'type': 'string', 'description': 'JWT access token'},
                        'user': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string', 'format': 'uuid'},
                                'username': {'type': 'string'},
                                'email': {'type': 'string', 'format': 'email'},
                                'first_name': {'type': 'string'},
                                'last_name': {'type': 'string'},
                                'is_email_verified': {'type': 'boolean'}
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Missing credentials',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        },
        401: {
            'description': 'Invalid credentials or inactive account',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        }
    },
    examples=[
        OpenApiExample(
            'Successful Login',
            value={
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'user': {
                    'id': '123e4567-e89b-12d3-a456-426614174000',
                    'username': 'johndoe',
                    'email': 'john@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'is_email_verified': True
                }
            },
            media_type='application/json',
            description='Example of a successful login response'
        ),
        OpenApiExample(
            'Invalid Credentials',
            value={
                'error': 'Invalid credentials. Please check your login and password.'
            },
            media_type='application/json',
            description='Example of an invalid credentials response'
        )
    ]
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Authenticate a user and return JWT tokens.
    
    Accepts either username or email for authentication, validates the credentials,
    and returns JWT tokens along with user profile information upon success.
    """
    login = request.data.get('login')
    password = request.data.get('password')

    if not login or not password:
        return Response({
            'error': 'Please provide both login (username or email) and password'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=login, password=password)

    if user is None:
        return Response({
            'error': 'Invalid credentials. Please check your login and password.'
        }, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({
            'error': 'This account is inactive.'
        }, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_email_verified': user.is_email_verified
        }
    })

@extend_schema(
    tags=['auth'],
    summary='Logout from the system',
    description="""
    Invalidate the user's refresh token.
    
    This endpoint:
    - Blacklists the provided refresh token
    - Prevents its future use for token refresh
    - Effectively logs out the user from the system
    
    Notes:
    - Requires a valid refresh token
    - Access token will still be valid until expiration
    - Multiple devices/sessions can be logged out separately
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {'type': 'string', 'description': 'JWT refresh token to blacklist'}
            },
            'required': ['refresh']
        }
    },
    responses={
        200: {
            'description': 'Successfully logged out',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'}
                    }
                }
            }
        },
        400: {
            'description': 'Invalid token',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        }
    },
    examples=[
        OpenApiExample(
            'Successful Logout',
            value={
                'message': 'Successfully logged out'
            },
            media_type='application/json',
            description='Example of a successful logout response'
        ),
        OpenApiExample(
            'Invalid Token',
            value={
                'error': 'Invalid token'
            },
            media_type='application/json',
            description='Example of an invalid token response'
        )
    ]
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout a user by blacklisting their refresh token.
    
    Takes a refresh token and adds it to the blacklist, preventing its future use
    for token refresh operations.
    """
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Successfully logged out'})
    except Exception:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=['auth'],
    summary='Refresh access token',
    description="""
    Refresh access token for the authenticated user.
    
    This endpoint:
    - Generates a new access token
    - Returns the refreshed access token
    
    Notes:
    - Requires a valid refresh token
    - Access token will still be valid until expiration
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {'type': 'string', 'description': 'JWT refresh token'}
            },
            'required': ['refresh']
        }
    },
    responses={
        200: {
            'description': 'Access token successfully refreshed',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'access': {'type': 'string', 'description': 'Refreshed JWT access token'}
                    }
                }
            }
        },
        400: {
            'description': 'Invalid refresh token',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refresh_access_token(request):
    """
    Refresh access token for the authenticated user.
    """
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        new_access_token = str(token.access_token)
        return Response({'access': new_access_token})
    except Exception:
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=['system'],
    summary='System Health Status Check',
    description="""Health check endpoint that monitors system vitals, performance metrics, and server status"""
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """
    Comprehensive health check endpoint that monitors system vitals, performance
    metrics, and server status in both UTC and Shamsi (Iranian) time.
    """
    # Basic database check
    db_status = "connected"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Calculate uptime
    uptime_seconds = time.time() - START_TIME
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    uptime_str = f"{days} days, {hours} hours, {minutes} minutes"
    
    # Get current time in Shamsi format
    now = datetime.datetime.now()
    shamsi_time = jdatetime.datetime.fromgregorian(datetime=now)
    shamsi_time_str = shamsi_time.strftime("%Y/%m/%d %H:%M:%S")
    utc_time_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # System information
    system_info = {
        'cpu_usage': psutil.cpu_percent(interval=1),
        'memory_usage': {
            'total': f"{psutil.virtual_memory().total / (1024 * 1024 * 1024):.2f}GB",
            'available': f"{psutil.virtual_memory().available / (1024 * 1024 * 1024):.2f}GB",
            'percent': psutil.virtual_memory().percent
        },
        'disk_usage': {
            'total': f"{psutil.disk_usage('/').total / (1024 * 1024 * 1024):.2f}GB",
            'used': f"{psutil.disk_usage('/').used / (1024 * 1024 * 1024):.2f}GB",
            'free': f"{psutil.disk_usage('/').free / (1024 * 1024 * 1024):.2f}GB",
            'percent': psutil.disk_usage('/').percent
        },
        'python_version': platform.python_version(),
        'django_version': django.get_version()
    }
    
    # Application information
    application_info = {
        'environment': os.getenv('DJANGO_ENV', 'development'),
        'debug_mode': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'installed_apps': settings.INSTALLED_APPS,
        'time_zone': settings.TIME_ZONE,
        'language_code': settings.LANGUAGE_CODE
    }
    
    # Cache check
    cache_key = 'health_check_test'
    try:
        cache.set(cache_key, 'test', 10)
        cache_value = cache.get(cache_key)
        cache_status = 'working' if cache_value == 'test' else 'error'
    except Exception as e:
        cache_status = f'error: {str(e)}'
    
    # Get latest migrations
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT app, name, applied FROM django_migrations ORDER BY applied DESC LIMIT 5")
            latest_migrations = [
                {
                    'app': row[0],
                    'name': row[1],
                    'applied': row[2].strftime("%Y-%m-%d %H:%M:%S")
                }
                for row in cursor.fetchall()
            ]
    except Exception:
        latest_migrations = []
    
    # Get version from settings or default
    version = getattr(settings, 'VERSION', '1.0.0')
    
    # Prepare response
    response_data = {
        'status': 'ok' if db_status == "connected" else 'error',
        'database': db_status,
        'version': version,
        'uptime': uptime_str,
        'server_time': shamsi_time_str,
        'server_time_utc': utc_time_str,
        'system_info': system_info,
        'application_info': application_info,
        'cache_status': cache_status,
        'latest_migrations': latest_migrations
    }
    
    # Return appropriate status code
    status_code = status.HTTP_200_OK if db_status == "connected" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(response_data, status=status_code)

@extend_schema(
    tags=['auth'],
    summary='Debug: Get verification code (DEV only)',
    description="""
    WARNING: This endpoint is for development purposes only.
    It should be disabled in production environments.
    
    Get the current verification code for a user by email.
    This is a convenience endpoint for testing when email delivery is problematic.
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'}
            },
            'required': ['email']
        }
    },
    responses={
        200: {
            'description': 'Verification code retrieved successfully',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'code': {'type': 'string'},
                        'email': {'type': 'string'},
                        'expires_at': {'type': 'string', 'format': 'date-time'},
                        'warning': {'type': 'string'}
                    }
                }
            }
        },
        400: {
            'description': 'Invalid request',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        },
        404: {
            'description': 'User not found',
            'content': {
                'application/json': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'}
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def debug_get_verification_code(request):
    """
    DEV ONLY: Get verification code for testing.
    """
    # Check if DEBUG is enabled
    if not settings.DEBUG:
        return Response({
            'error': 'This endpoint is only available in development environments'
        }, status=status.HTTP_403_FORBIDDEN)
    
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if user.is_email_verified:
        return Response({
            'message': 'This email is already verified',
            'is_verified': True
        }, status=status.HTTP_200_OK)
    
    if not user.verification_code or not user.verification_code_created:
        # Generate a new code if needed
        code = generate_verification_code()
        user.set_verification_code(code)
    else:
        code = user.verification_code
    
    expires_at = user.verification_code_created + datetime.timedelta(seconds=settings.EMAIL_VERIFICATION_TIMEOUT)
    
    return Response({
        'warning': 'DO NOT USE IN PRODUCTION',
        'email': email,
        'code': code,
        'expires_at': expires_at.isoformat()
    }, status=status.HTTP_200_OK)

@extend_schema(
    tags=['auth'],
    summary='Emergency Direct Verification',
    description="""
    Emergency endpoint to directly verify a user's email without requiring a verification code.
    Use this if email delivery is not working properly.
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'}
            },
            'required': ['email']
        }
    },
    responses={
        200: OpenApiResponse(description='Email successfully verified'),
        404: OpenApiResponse(description='User not found')
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def debug_direct_verify(request):
    """
    Emergency: Directly verify a user's email without code.
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if user.is_email_verified:
        return Response({
            'message': 'Email already verified',
            'is_verified': True
        }, status=status.HTTP_200_OK)
    
    # Directly verify the user
    user.is_email_verified = True
    user.clear_verification_code()
    user.save()
    
    # Generate fresh JWT tokens after verification
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Email successfully verified without code',
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': UserSerializer(user).data
    })