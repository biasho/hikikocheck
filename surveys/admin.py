from django.contrib import admin
from .models import Survey, SurveyResultThreshold, Submission, Answer

# 1. Inline hiển thị Thang điểm trong trang Survey
class ThresholdInline(admin.TabularInline):
    model = SurveyResultThreshold
    extra = 1

# 2. Inline hiển thị Danh sách Submission trong trang Survey
class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0 # Không hiện dòng trống
    fields = ('user', 'total_score', 'submitted_at')
    readonly_fields = ('user', 'total_score', 'submitted_at') # Đặt chế độ chỉ xem
    can_delete = False
    show_change_link = True # Bật nút bấm để nhảy nhanh sang xem chi tiết Submission đó

# 3. Inline hiển thị Danh sách Answer trong trang Submission
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ('question', 'selected_option', 'text_answer')
    readonly_fields = ('question', 'selected_option', 'text_answer')
    can_delete = False

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('title', 'description')
    filter_horizontal = ('questions',) 
    # Nhúng cả Thang điểm và Danh sách các lượt nộp bài vào trang Survey
    inlines = [ThresholdInline, SubmissionInline] 

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'survey', 'user', 'email', 'session_key', 'total_score', 'submitted_at')
    list_filter = ('survey', 'submitted_at')
    search_fields = ('email', 'session_key', 'user__username') # Thêm tìm kiếm theo email và session_key
    readonly_fields = ('submitted_at',)
    inlines = [AnswerInline]

# Đăng ký riêng các model độc lập
admin.site.register(SurveyResultThreshold)
admin.site.register(Answer)