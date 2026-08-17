from django.contrib import admin
from .models import Source, Lead, Group

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'source', 'object_id', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone') 
# 🎯 Đăng ký model Group vào Django Admin
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'order')  # Các cột hiển thị danh sách
    search_fields = ('code', 'name')          # Ô tìm kiếm
    ordering = ('order',)