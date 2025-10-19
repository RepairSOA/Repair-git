# repair_api/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class EquipmentCategory(models.Model):
    """หมวดหมู่อุปกรณ์ เช่น คอมพิวเตอร์, เครื่องพิมพ์, เฟอร์นิเจอร์"""
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อหมวดหมู่")
    description = models.TextField(blank=True, null=True, verbose_name="คำอธิบาย")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "หมวดหมู่อุปกรณ์"
        verbose_name_plural = "หมวดหมู่อุปกรณ์"
        ordering = ['name']

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """ข้อมูลอุปกรณ์ในองค์กร"""
    CONDITION_CHOICES = [
        ('excellent', 'ดีมาก'),
        ('good', 'ดี'),
        ('fair', 'พอใช้'),
        ('poor', 'แย่'),
    ]

    equipment_code = models.CharField(max_length=50, unique=True, verbose_name="รหัสอุปกรณ์")
    name = models.CharField(max_length=200, verbose_name="ชื่อุปกรณ์")
    category = models.ForeignKey(
        EquipmentCategory, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='equipments',
        verbose_name="หมวดหมู่"
    )
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียด")
    location = models.CharField(max_length=200, verbose_name="สถานที่ติดตั้ง")
    purchase_date = models.DateField(null=True, blank=True, verbose_name="วันที่จัดซื้อ")
    warranty_expiry = models.DateField(null=True, blank=True, verbose_name="วันหมดประกัน")
    condition = models.CharField(
        max_length=20, 
        choices=CONDITION_CHOICES, 
        default='good',
        verbose_name="สภาพ"
    )
    image = models.ImageField(
        upload_to='equipment_images/', 
        blank=True, 
        null=True,
        verbose_name="รูปภาพ"
    )
    is_active = models.BooleanField(default=True, verbose_name="ใช้งานอยู่")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "อุปกรณ์"
        verbose_name_plural = "อุปกรณ์"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.equipment_code} - {self.name}"


class RepairRequest(models.Model):
    """คำร้องขอซ่อม"""
    STATUS_CHOICES = [
        ('pending', 'รอดำเนินการ'),
        ('assigned', 'มอบหมายงาน'),
        ('in_progress', 'กำลังดำเนินการ'),
        ('completed', 'เสร็จสิ้น'),
        ('cancelled', 'ยกเลิก'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'ต่ำ'),
        ('medium', 'ปานกลาง'),
        ('high', 'สูง'),
        ('urgent', 'เร่งด่วน'),
    ]

    request_number = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        verbose_name="เลขที่คำร้อง"
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='repair_requests',
        verbose_name="อุปกรณ์"
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='repair_requests',
        verbose_name="ผู้แจ้ง"
    )
    title = models.CharField(max_length=200, verbose_name="หัวข้อ")
    description = models.TextField(verbose_name="รายละเอียดปัญหา")
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="ความสำคัญ"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="สถานะ"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_repairs',
        verbose_name="ช่างที่รับผิดชอบ"
    )
    request_date = models.DateTimeField(default=timezone.now, verbose_name="วันที่แจ้ง")
    assigned_date = models.DateTimeField(null=True, blank=True, verbose_name="วันที่มอบหมาย")
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name="วันที่เสร็จสิ้น")
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="ค่าใช้จ่ายประมาณ"
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="ค่าใช้จ่ายจริง"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "คำร้องขอซ่อม"
        verbose_name_plural = "คำร้องขอซ่อม"
        ordering = ['-request_date']

    def save(self, *args, **kwargs):
        if not self.request_number:
            # สร้างเลขที่คำร้องอัตโนมัติ เช่น REQ2024001
            from django.utils import timezone
            year = timezone.now().year
            last_request = RepairRequest.objects.filter(
                request_number__startswith=f'REQ{year}'
            ).order_by('-request_number').first()
            
            if last_request:
                last_number = int(last_request.request_number[-3:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.request_number = f'REQ{year}{new_number:03d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_number} - {self.title}"


class RepairHistory(models.Model):
    """ประวัติการอัพเดทสถานะ"""
    repair_request = models.ForeignKey(
        RepairRequest,
        on_delete=models.CASCADE,
        related_name='histories',
        verbose_name="คำร้องซ่อม"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="ผู้อัพเดท"
    )
    status = models.CharField(max_length=20, verbose_name="สถานะ")
    comment = models.TextField(blank=True, null=True, verbose_name="ความคิดเห็น")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ประวัติการซ่อม"
        verbose_name_plural = "ประวัติการซ่อม"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.repair_request.request_number} - {self.status}"


class UserProfile(models.Model):
    """ข้อมูลเพิ่มเติมของผู้ใช้"""
    ROLE_CHOICES = [
        ('user', 'ผู้ใช้ทั่วไป'),
        ('technician', 'ช่างซ่อม'),
        ('admin', 'ผู้ดูแลระบบ'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="ผู้ใช้"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name="บทบาท"
    )
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name="แผนก")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "โปรไฟล์ผู้ใช้"
        verbose_name_plural = "โปรไฟล์ผู้ใช้"

    def __str__(self):
        return f"{self.user.username} - {self.role}"