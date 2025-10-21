"""
URL configuration for repair_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Schema view สำหรับ API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Repair System API",
        default_version='v1',
        description="API Documentation for Repair System",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@repairsystem.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Health check view
@csrf_exempt
def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'ok',
        'message': 'Repair System API is running',
        'version': '1.0.0'
    })

# Home/Root view
@csrf_exempt
def home_view(request):
    """Root endpoint with API information"""
    return JsonResponse({
        'message': 'Welcome to Repair System API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'docs': '/swagger/',
            'redoc': '/redoc/',
            'health': '/health/'
        },
        'status': 'active'
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Root endpoint
    path('', home_view, name='home'),
    
    # Health check
    path('health/', health_check, name='health'),
    
    # API endpoints
    path('api/', include('repair_api.urls')),
    
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]