# repair_api/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.db.models import Q, Count
from datetime import datetime, timedelta

from .models import (
    EquipmentCategory,
    Equipment,
    RepairRequest,
    RepairHistory,
    UserProfile
)
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    RegisterSerializer,
    EquipmentCategorySerializer,
    EquipmentSerializer,
    RepairRequestSerializer,
    RepairRequestCreateSerializer,
    RepairRequestUpdateSerializer,
    RepairHistorySerializer,
    DashboardStatsSerializer
)


class RegisterView(viewsets.GenericViewSet):
    """API สำหรับการลงทะเบียน"""
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'ลงทะเบียนสำเร็จ',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    """API สำหรับจัดการโปรไฟล์ผู้ใช้"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """ดูโปรไฟล์ของตัวเอง"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'โปรไฟล์ไม่พบ'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """แก้ไขโปรไฟล์ของตัวเอง"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'โปรไฟล์ไม่พบ'},
                status=status.HTTP_404_NOT_FOUND
            )

# ----------------------------------------------------
# ▼▼▼ [START] นี่คือส่วนที่แก้ไขโครงสร้างให้ถูกต้อง ▼▼▼
# ----------------------------------------------------

class EquipmentCategoryViewSet(viewsets.ModelViewSet):
    """API สำหรับจัดการหมวดหมู่อุปกรณ์"""
    queryset = EquipmentCategory.objects.all()
    serializer_class = EquipmentCategorySerializer
    permission_classes = [IsAuthenticated]

    # --- นี่คือ get_queryset สำหรับ "หมวดหมู่" ---
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


# --- นี่คือคลาส "EquipmentViewSet" ที่เคยหายไป/อยู่ผิดที่ ---
class EquipmentViewSet(viewsets.ModelViewSet):
    """API สำหรับจัดการอุปกรณ์"""
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer  # <-- เพิ่มบรรทัดนี้ที่ขาดไป
    permission_classes = [IsAuthenticated]

    # --- นี่คือ get_queryset สำหรับ "อุปกรณ์" (ที่เคยอยู่ผิดที่) ---
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(equipment_code__icontains=search) |
                Q(name__icontains=search) |
                Q(location__icontains=search)
            )
        
        return queryset

    # --- นี่คือ action "available" (ที่เคยอยู่ผิดที่) ---
    @action(detail=False, methods=['get'])
    def available(self, request):
        """ดูอุปกรณ์ที่พร้อมใช้งาน"""
        equipments = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(equipments, many=True)
        
        # --- ส่งกลับแบบมี key 'results' (สำหรับ Dropdown) ---
        return Response({'results': serializer.data})


# ----------------------------------------------------
# ▲▲▲ [END] สิ้นสุดส่วนที่แก้ไขโครงสร้าง ▼▼▼
# ----------------------------------------------------


class RepairRequestViewSet(viewsets.ModelViewSet):
    """API สำหรับจัดการคำร้องขอซ่อม"""
    queryset = RepairRequest.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return RepairRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RepairRequestUpdateSerializer
        return RepairRequestSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # ถ้าเป็นผู้ใช้ทั่วไป ให้เห็นเฉพาะคำร้องของตัวเอง
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role == 'user':
                queryset = queryset.filter(requester=user)
            elif profile.role == 'technician':
                # ช่างเห็นงานที่ได้รับมอบหมายและงานที่รอรับ
                queryset = queryset.filter(
                    Q(assigned_to=user) | Q(status='pending')
                )
        except UserProfile.DoesNotExist:
            queryset = queryset.filter(requester=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by equipment
        equipment = self.request.query_params.get('equipment', None)
        if equipment:
            queryset = queryset.filter(equipment_id=equipment)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(request_number__icontains=search) |
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.select_related('equipment', 'requester', 'assigned_to')

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """ดูคำร้องของตัวเอง"""
        requests = self.queryset.filter(requester=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        """ดูงานที่ได้รับมอบหมาย"""
        requests = self.queryset.filter(assigned_to=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """มอบหมายงานให้ช่าง"""
        repair_request = self.get_object()
        technician_id = request.data.get('technician_id')
        
        try:
            technician = User.objects.get(id=technician_id)
            technician_profile = UserProfile.objects.get(user=technician)
            
            if technician_profile.role not in ['technician', 'admin']:
                return Response(
                    {'error': 'ผู้ใช้นี้ไม่ใช่ช่างซ่อม'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            repair_request.assigned_to = technician
            repair_request.status = 'assigned'
            from django.utils import timezone
            repair_request.assigned_date = timezone.now()
            repair_request.save()
            
            # บันทึกประวัติ
            RepairHistory.objects.create(
                repair_request=repair_request,
                updated_by=request.user,
                status='assigned',
                comment=f'มอบหมายงานให้ {technician.get_full_name()}'
            )
            
            serializer = self.get_serializer(repair_request)
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'ไม่พบผู้ใช้'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'ไม่พบโปรไฟล์ผู้ใช้'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """อัพเดทสถานะ"""
        repair_request = self.get_object()
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')
        
        if new_status not in dict(RepairRequest.STATUS_CHOICES):
            return Response(
                {'error': 'สถานะไม่ถูกต้อง'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        repair_request.status = new_status
        
        from django.utils import timezone
        if new_status == 'completed':
            repair_request.completed_date = timezone.now()
        
        repair_request.save()
        
        # บันทึกประวัติ
        RepairHistory.objects.create(
            repair_request=repair_request,
            updated_by=request.user,
            status=new_status,
            comment=comment
        )
        
        serializer = self.get_serializer(repair_request)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """ดูประวัติการอัพเดท"""
        repair_request = self.get_object()
        histories = RepairHistory.objects.filter(repair_request=repair_request)
        serializer = RepairHistorySerializer(histories, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """API สำหรับแสดงสถิติในแดชบอร์ด"""
    user = request.user
    
    try:
        profile = UserProfile.objects.get(user=user)
        
        if profile.role == 'user':
            # สถิติของผู้ใช้ทั่วไป
            total_requests = RepairRequest.objects.filter(requester=user).count()
            pending = RepairRequest.objects.filter(requester=user, status='pending').count()
            in_progress = RepairRequest.objects.filter(
                requester=user, 
                status__in=['assigned', 'in_progress']
            ).count()
            completed = RepairRequest.objects.filter(requester=user, status='completed').count()
            recent = RepairRequest.objects.filter(requester=user).order_by('-created_at')[:5]
            
        elif profile.role == 'technician':
            # สถิติของช่างซ่อม
            total_requests = RepairRequest.objects.filter(assigned_to=user).count()
            pending = RepairRequest.objects.filter(status='pending').count()
            in_progress = RepairRequest.objects.filter(
                assigned_to=user, 
                status='in_progress'
            ).count()
            completed = RepairRequest.objects.filter(
                assigned_to=user, 
                status='completed'
            ).count()
            recent = RepairRequest.objects.filter(
                Q(assigned_to=user) | Q(status='pending')
            ).order_by('-created_at')[:5]
            
        else:  # admin
            # สถิติทั้งหมด
            total_requests = RepairRequest.objects.count()
            pending = RepairRequest.objects.filter(status='pending').count()
            in_progress = RepairRequest.objects.filter(
                status__in=['assigned', 'in_progress']
            ).count()
            completed = RepairRequest.objects.filter(status='completed').count()
            recent = RepairRequest.objects.order_by('-created_at')[:5]
        
        # สถิติอุปกรณ์
        total_equipment = Equipment.objects.count()
        active_equipment = Equipment.objects.filter(is_active=True).count()
        
        data = {
            'total_requests': total_requests,
            'pending_requests': pending,
            'in_progress_requests': in_progress,
            'completed_requests': completed,
            'total_equipment': total_equipment,
            'active_equipment': active_equipment,
            'recent_requests': RepairRequestSerializer(recent, many=True).data
        }
        
        return Response(data)
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'ไม่พบโปรไฟล์ผู้ใช้'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def technician_list(request):
    """API สำหรับดูรายชื่อช่างซ่อม"""
    technicians = UserProfile.objects.filter(
        role__in=['technician', 'admin']
    ).select_related('user')
    
    data = [
        {
            'id': profile.user.id,
            'username': profile.user.username,
            'full_name': profile.user.get_full_name() or profile.user.username,
            'department': profile.department,
            'role': profile.role
        }
        for profile in technicians
    ]
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def equipment_category_list(request):
    """API สำหรับดึงรายการหมวดหมู่อุปกรณ์ทั้งหมด"""
    categories = EquipmentCategory.objects.all()
    
    data = [
        {
            'id': category.id,
            'name': category.name,
            'description': category.description if hasattr(category, 'description') else ''
        }
        for category in categories
    ]
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def equipment_by_category(request, category_id):
    """API สำหรับดึงรายการอุปกรณ์ตามหมวดหมู่"""
    try:
        equipments = Equipment.objects.filter(
            category_id=category_id,
            is_active=True
        )
        
        serializer = EquipmentSerializer(equipments, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )