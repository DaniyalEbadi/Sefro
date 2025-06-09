from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from django.views.static import serve

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/', include('api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(template_name='drf-spectacular/swagger-ui.html', url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Test page for email verification
    path('test-verification/', TemplateView.as_view(template_name='test_verification.html'), name='test_verification'),
    
    # Serve static files directly
    path('', serve, {'document_root': settings.STATIC_ROOT, 'path': 'index.html'}, name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)