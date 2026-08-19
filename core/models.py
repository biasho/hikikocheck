from django.db import models
from django.contrib.auth.models import User

class Source(models.Model):
    """Model quản lý các nguồn thu thập lead (dùng cho dropdown)"""
    name = models.CharField(max_length=100, unique=True, help_text="Tên định danh nguồn (VD: survey_pdf_report, newsletter)")
    description = models.TextField(blank=True, null=True, help_text="Mô tả chi tiết về nguồn này")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Lead(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    
    # 🔓 Bỏ ràng buộc bắt buộc và unique tuyệt đối cứng để hỗ trợ người dùng không nhập email
    email = models.EmailField(db_index=True, blank=True, null=True)
    
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Họ và tên")
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # 🏫 Bổ sung thêm trường lưu Lớp / Đơn vị cho học sinh
    school_class = models.CharField(max_length=100, blank=True, null=True, verbose_name="Lớp / Đơn vị")
    
    # 🎯 Chuyển source thành ForeignKey liên kết sang bảng Source (Hiển thị dạng Dropdown ở Admin)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    
    object_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = f"{self.first_name or ''} {self.last_name or ''}".strip() or self.full_name or "Ẩn danh"
        class_info = f" - Lớp: {self.school_class}" if self.school_class else ""
        contact = f" ({self.email or self.phone})" if (self.email or self.phone) else ""
        source_name = self.source.name if self.source else "Unknown"
        return f"{name}{class_info}{contact} [{source_name}]"


class Group(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="Mã nhóm (VD: A, B, C, D)")
    name = models.CharField(max_length=255, verbose_name="Tên nhóm")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả nhóm")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")

    class Meta:
        ordering = ['order']
        verbose_name = "Nhóm khảo sát"
        verbose_name_plural = "Các nhóm khảo sát"

    def __str__(self):
        return f"[{self.code}] {self.name}"