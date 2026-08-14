from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR
from django.shortcuts import redirect
from django.urls import reverse
from .models import Category, Question, Option


class OptionInline(admin.TabularInline):
    model = Option
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'category', 'question_type')
    list_filter = ('category', 'question_type')
    search_fields = ('text',)
    inlines = [OptionInline]

    # 1. Ép Django Admin hiển thị nút "Save and add another" trên cả trang Add lẫn trang Change
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['show_save_and_add_another'] = True
        context['show_save_and_continue'] = True
        return super().render_change_form(request, context, add, change, form_url, obj)

    # 2. Xử lý khi người dùng bấm nút ở trang THÊM MỚI (Add)
    def response_add(self, request, obj, post_url_continue=None):
        if IS_POPUP_VAR in request.POST and "_addanother" in request.POST:
            # Quay lại trang Add trống để gõ tiếp câu tiếp theo
            add_url = reverse('admin:questions_question_add')
            popup_params = request.GET.urlencode()
            return redirect(f"{add_url}?{popup_params}")
        return super().response_add(request, obj, post_url_continue)

    # 3. Xử lý khi người dùng bấm nút ở trang CHỈNH SỬA (Change - như hình bạn đang mở)
    def response_change(self, request, obj):
        if IS_POPUP_VAR in request.POST and "_addanother" in request.POST:
            # Chuyển hướng ngay sang trang Add mới để tiếp tục gõ câu hỏi tiếp theo!
            add_url = reverse('admin:questions_question_add')
            popup_params = request.GET.urlencode()
            return redirect(f"{add_url}?{popup_params}")
        return super().response_change(request, obj)


admin.site.register(Category)