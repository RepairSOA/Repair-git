# repair_api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'categories', views.EquipmentCategoryViewSet, basename='category')
router.register(r'equipment', views.EquipmentViewSet, basename='equipment')
router.register(r'repair-requests', views.RepairRequestViewSet, basename='repair-request')
router.register(r'profiles', views.UserProfileViewSet, basename='profile')
router.register(r'auth', views.RegisterView, basename='auth')

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Custom endpoints
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('technicians/', views.technician_list, name='technician_list'),
    
    # Router URLs
    path('', include(router.urls)),
    
    path('categories/', views.equipment_category_list),
    path('get-equipment/', 
     views.EquipmentViewSet.as_view({'get': 'available'}), 
     name='get-equipment-list-js'
),
]