# repair_api/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    EquipmentCategory, 
    Equipment, 
    RepairRequest, 
    RepairHistory,
    UserProfile
)

class UserSerializer(serializers.ModelSerializer):
    """Serializer สำหรับข้อมูลผู้ใช้"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer สำหรับโปรไฟล์ผู้ใช้"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'department', 'phone', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer สำหรับการลงทะเบียน"""
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        default='user',
        write_only=True
    )
    department = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 
                  'first_name', 'last_name', 'role', 'department', 'phone']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "รหัสผ่านไม่ตรงกัน"})
        return attrs

    def create(self, validated_data):
        # ลบข้อมูลที่ไม่ใช่ของ User model
        validated_data.pop('password2')
        role = validated_data.pop('role', 'user')
        department = validated_data.pop('department', '')
        phone = validated_data.pop('phone', '')
        
        # สร้าง User
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # สร้าง UserProfile
        UserProfile.objects.create(
            user=user,
            role=role,
            department=department,
            phone=phone
        )
        
        return user


class EquipmentCategorySerializer(serializers.ModelSerializer):
    """Serializer สำหรับหมวดหมู่อุปกรณ์"""
    equipment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EquipmentCategory
        fields = ['id', 'name', 'description', 'equipment_count', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_equipment_count(self, obj):
        return obj.equipments.filter(is_active=True).count()


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer สำหรับอุปกรณ์"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    
    class Meta:
        model = Equipment
        fields = [
            'id', 'equipment_code', 'name', 'category', 'category_name',
            'description', 'location', 'purchase_date', 'warranty_expiry',
            'condition', 'condition_display', 'image', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RepairHistorySerializer(serializers.ModelSerializer):
    """Serializer สำหรับประวัติการซ่อม"""
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = RepairHistory
        fields = [
            'id', 'repair_request', 'updated_by', 'updated_by_name',
            'updated_by_username', 'status', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RepairRequestSerializer(serializers.ModelSerializer):
    """Serializer สำหรับคำร้องขอซ่อม"""
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_code = serializers.CharField(source='equipment.equipment_code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    histories = RepairHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = RepairRequest
        fields = [
            'id', 'request_number', 'equipment', 'equipment_name', 'equipment_code',
            'requester', 'requester_name', 'requester_username',
            'title', 'description', 'priority', 'priority_display',
            'status', 'status_display', 'assigned_to', 'assigned_to_name',
            'request_date', 'assigned_date', 'completed_date',
            'estimated_cost', 'actual_cost', 'remarks',
            'histories', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'request_number', 'requester', 'request_date', 
            'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        # กำหนด requester จาก request.user
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)


class RepairRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer สำหรับสร้างคำร้องขอซ่อม (ง่ายกว่า)"""
    
    class Meta:
        model = RepairRequest
        fields = [
            'equipment', 'title', 'description', 'priority'
        ]

    def create(self, validated_data):
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)


class RepairRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer สำหรับอัพเดทสถานะคำร้อง"""
    comment = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    class Meta:
        model = RepairRequest
        fields = [
            'status', 'assigned_to', 'estimated_cost', 
            'actual_cost', 'remarks', 'comment'
        ]

    def update(self, instance, validated_data):
        comment = validated_data.pop('comment', None)
        
        # อัพเดทวันที่ตามสถานะ
        if 'status' in validated_data:
            from django.utils import timezone
            if validated_data['status'] == 'assigned' and not instance.assigned_date:
                instance.assigned_date = timezone.now()
            elif validated_data['status'] == 'completed' and not instance.completed_date:
                instance.completed_date = timezone.now()
        
        # อัพเดทข้อมูล
        instance = super().update(instance, validated_data)
        
        # บันทึกประวัติ
        if comment or 'status' in validated_data:
            RepairHistory.objects.create(
                repair_request=instance,
                updated_by=self.context['request'].user,
                status=instance.status,
                comment=comment or ''
            )
        
        return instance


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer สำหรับสถิติในแดชบอร์ด"""
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    in_progress_requests = serializers.IntegerField()
    completed_requests = serializers.IntegerField()
    total_equipment = serializers.IntegerField()
    active_equipment = serializers.IntegerField()
    recent_requests = RepairRequestSerializer(many=True)