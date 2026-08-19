from django.contrib import admin
from .models import (
    Survey, 
    CompositeSurvey, 
    CompositeSurveyItem, 
    SurveyResultThreshold, 
    Submission, 
    Answer
)


# ==================== 1. INLINES ====================

class CompositeSurveyItemInline(admin.TabularInline):
    model = CompositeSurveyItem
    extra = 1
    fields = ('order', 'survey')
    ordering = ('order',)
    verbose_name = "Cấu trúc phần khảo sát"
    verbose_name_plural = "Cấu trúc các phần khảo sát"


class ThresholdInline(admin.TabularInline):
    model = SurveyResultThreshold
    extra = 1


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    fields = ('user', 'lead', 'total_score', 'submitted_at')
    readonly_fields = ('user', 'lead', 'total_score', 'submitted_at')
    can_delete = False
    show_change_link = True


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ('question', 'selected_option', 'text_answer')
    readonly_fields = ('question', 'selected_option', 'text_answer')
    can_delete = False


# ==================== 2. ADMIN CLASSES ====================

@admin.register(CompositeSurvey)
class CompositeSurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    inlines = [CompositeSurveyItemInline]


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('title', 'description')
    filter_horizontal = ('questions',) 
    inlines = [ThresholdInline, SubmissionInline] 


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'composite_survey', 
        'survey', 
        'user', 
        'lead', 
        'email', 
        'total_score', 
        'score_a', 
        'score_b', 
        'score_c', 
        'score_d', 
        'submitted_at'
    )
    list_filter = ('composite_survey', 'survey', 'submitted_at')
    search_fields = ('email', 'session_key', 'user__username', 'lead__full_name', 'lead__school_class')
    readonly_fields = ('submitted_at',)
    inlines = [AnswerInline]


@admin.register(CompositeSurveyItem)
class CompositeSurveyItemAdmin(admin.ModelAdmin):
    list_display = ('composite_survey', 'survey', 'order')
    list_filter = ('composite_survey',)
    ordering = ('composite_survey', 'order')


@admin.register(SurveyResultThreshold)
class SurveyResultThresholdAdmin(admin.ModelAdmin):
    list_display = ('title', 'survey', 'group', 'min_score', 'max_score')
    list_filter = ('survey', 'group')
    search_fields = ('title', 'description')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'submission', 'question', 'selected_option', 'text_answer')
    # Sửa list_filter tại đây (bỏ question__survey)
    list_filter = ('question__group', 'submission__composite_survey')
    search_fields = ('text_answer', 'submission__id', 'question__text')
    readonly_fields = ('submission', 'question', 'selected_option', 'text_answer')