# repair_api/admin.py

from django.contrib import admin
from .models import (
    EquipmentCategory,
    Equipment,
    RepairRequest,
    RepairHistory,
    UserProfile
)

@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['equipment_code', 'name', 'category', 'location', 'condition', 'is_active']
    search_fields = ['equipment_code', 'name', 'location']
    list_filter = ['category', 'condition', 'is_active', 'created_at']
    list_editable = ['is_active']

@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'equipment', 'requester', 'status', 'priority', 'request_date']
    search_fields = ['request_number', 'title', 'description']
    list_filter = ['status', 'priority', 'request_date']
    readonly_fields = ['request_number', 'request_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('ข้อมูลทั่วไป', {
            'fields': ('request_number', 'equipment', 'requester', 'title', 'description')
        }),
        ('สถานะและความสำคัญ', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('วันที่', {
            'fields': ('request_date', 'assigned_date', 'completed_date')
        }),
        ('ค่าใช้จ่าย', {
            'fields': ('estimated_cost', 'actual_cost')
        }),
        ('หมายเหตุ', {
            'fields': ('remarks',)
        }),
        ('ข้อมูลระบบ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RepairHistory)
class RepairHistoryAdmin(admin.ModelAdmin):
    list_display = ['repair_request', 'status', 'updated_by', 'created_at']
    search_fields = ['repair_request__request_number', 'comment']
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'phone']
    search_fields = ['user__username', 'user__email', 'department']
    list_filter = ['role', 'department']