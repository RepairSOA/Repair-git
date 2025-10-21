"""
URL configuration for repair_api app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# สร้าง router สำหรับ ViewSets (ถ้ามี)
router = DefaultRouter()

# ถ้ามี ViewSets ให้ register ที่นี่
# ตัวอย่าง:
# from .views import RepairViewSet
# router.register(r'repairs', RepairViewSet, basename='repair')

# API Info view
@csrf_exempt
def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Repair System API v1',
        'endpoints': {
            'auth': {
                'login': '/api/auth/login/',
                'refresh': '/api/auth/refresh/',
                'verify': '/api/auth/verify/',
            },
            'docs': '/swagger/',
        }
    })

urlpatterns = [
    # API Root
    path('', api_root, name='api-root'),
    
    # Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Router URLs (ViewSets)
    path('', include(router.urls)),
    
    # เพิ่ม URL patterns อื่นๆ ของคุณที่นี่
]