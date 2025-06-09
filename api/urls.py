from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet, ArticleViewSet, CategoryViewSet, 
    CommentViewSet, login_view, register_view, logout_view,
    health_check, RoleViewSet, PermissionViewSet, RolePermissionViewSet, UserRoleViewSet, MediaViewSet,
    verify_email, resend_verification, debug_get_verification_code, debug_direct_verify
)
from .views_email import email_diagnostics
from .verification_email import send_verification_email, verify_code

# Create router for API endpoints
router = DefaultRouter()

# User Management
router.register('users', UserViewSet, basename='user')

# Role & Permission Management
router.register('roles', RoleViewSet, basename='role')
router.register('permissions', PermissionViewSet, basename='permission')
router.register('role-permissions', RolePermissionViewSet, basename='role-permission')
router.register('user-roles', UserRoleViewSet, basename='user-role')

# Content Management
router.register('articles', ArticleViewSet, basename='article')
router.register('categories', CategoryViewSet, basename='category')
router.register('comments', CommentViewSet, basename='comment')
router.register('media', MediaViewSet, basename='media')

urlpatterns = [
    # Authentication Endpoints
    path('auth/', include([
        path('register/', register_view, name='auth-register'),
        path('login/', login_view, name='auth-login'),
        path('logout/', logout_view, name='auth-logout'),
        path('verify-email/', verify_email, name='auth-verify-email'),
        path('resend-verification/', resend_verification, name='auth-resend-verification'),
        path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
        path('debug/get-code/', debug_get_verification_code, name='auth-debug-get-code'),
        path('debug/direct-verify/', debug_direct_verify, name='auth-debug-direct-verify'),
        # Email Verification Endpoints
        path('send-verification/', send_verification_email, name='send_verification_email'),
        path('verify-code/', verify_code, name='verify_code'),
    ])),

    # API Endpoints
    path('', include(router.urls)),

    # System Endpoints
    path('system/health/', health_check, name='health-check'),
    path('system/email/diagnostics/', email_diagnostics, name='email_diagnostics'),
]