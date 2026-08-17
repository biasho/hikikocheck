# users/admin.py
from django.contrib import admin
from .models import UserProfile, Role

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone_number', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email', 'phone_number']