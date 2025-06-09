"""
API Documentation Configuration
=============================

This module configures the OpenAPI (Swagger) documentation for the entire API.
It includes settings for:
- API metadata
- Security schemes
- Tags ordering and descriptions
- Server configurations
- Response schemas
"""

SPECTACULAR_SETTINGS = {
    'TITLE': 'Sefr API',
    'DESCRIPTION': """
    🚀 Modern RESTful API for Content Management
    ===========================================

    This API provides a comprehensive set of endpoints for managing content, users, and system health.
    
    Key Features
    -----------
    👤 **User Management**
    - Authentication with JWT
    - Role-based permissions
    - User profiles
    
    📝 **Content Management**
    - Article creation and management
    - Category organization
    - Media handling
    - Comments and interactions
    
    🔍 **System Features**
    - Health monitoring
    - Performance metrics
    - System configuration
    
    Authentication
    -------------
    This API uses JWT (JSON Web Tokens) for authentication. Most endpoints require a valid JWT token
    in the Authorization header using the Bearer scheme.
    
    Example: `Authorization: Bearer your.jwt.token`
    
    Rate Limiting
    ------------
    API requests are limited to:
    - 100 requests per minute for authenticated users
    - 20 requests per minute for anonymous users
    
    Error Handling
    -------------
    The API uses standard HTTP response codes:
    - 2xx for successful operations
    - 4xx for client errors
    - 5xx for server errors
    
    All error responses include a JSON body with error details.
    """,
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'defaultModelsExpandDepth': 3,
        'defaultModelExpandDepth': 3,
        'defaultModelRendering': 'model',
        'displayRequestDuration': True,
        'docExpansion': 'none',
        'filter': True,
        'operationsSorter': 'method',
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True,
        'operationIdFormatter': "function(str) { return str.replace(/\\s+/g, ''); }"
    },
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'SWAGGER_UI_STYLES': [
        'SIDECAR',
    ],
    'SWAGGER_UI_JS_URL': 'SIDECAR',
    'TAGS': [
        {
            'name': 'auth',
            'description': """
            Authentication endpoints for user management.
            Handles user registration, login, logout, and token refresh operations.
            """,
            'x-display-name': '🔐 Authentication'
        },
        {
            'name': 'users',
            'description': """
            User management endpoints.
            Handles user profiles, roles, and permissions.
            """,
            'x-display-name': '👤 Users'
        },
        {
            'name': 'articles',
            'description': """
            Article management endpoints.
            Handles creation, updating, and deletion of articles, categories, and related content.
            """,
            'x-display-name': '📝 Articles'
        },
        {
            'name': 'system_checking',
            'description': """
            System monitoring and health check endpoints.
            Provides real-time insights into system performance and health metrics.
            
            Features:
            - Real-time system metrics
            - Database connectivity checks
            - Cache system verification
            - Application configuration details
            - Server time in both UTC and Shamsi formats
            """,
            'x-display-name': '🏥 System Health'
        }
    ],
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Enter your JWT token in the format: `Bearer your.jwt.token`'
        },
        'Basic': {
            'type': 'basic',
            'description': 'Basic authentication for initial token acquisition'
        }
    },
    'SERVERS': [
        {
            'url': '/api',
            'description': 'Local Development Server'
        },
        {
            'url': 'https://api.example.com/v1',
            'description': 'Production Server'
        },
        {
            'url': 'https://staging-api.example.com/v1',
            'description': 'Staging Server'
        }
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'ENABLE_DJANGO_DEPLOY_CHECK': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'POSTPROCESSING_HOOKS': [],
    'ENUM_NAME_OVERRIDES': {},
    'DEFAULT_INFO': None,
    'AUTHENTICATION_WHITELIST': [],
    'APPEND_COMPONENTS': {},
    'COMPONENT_NO_READ_ONLY_REQUIRED': False
} 