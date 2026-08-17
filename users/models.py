# users/models.py
from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Tên vai trò")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Liên kết động tới Model Role
    role = models.ForeignKey(
        Role, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='users',
        verbose_name="Vai trò"
    )
    
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Số điện thoại")
    bio = models.TextField(max_length=500, blank=True, null=True, verbose_name="Tiểu sử")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        role_name = self.role.name if self.role else "Chưa phân vai trò"
        return f"Hồ sơ của {self.user.username} ({role_name})"