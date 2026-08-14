from django.contrib import admin
from .models import Source, Lead

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'source', 'object_id', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone') 