# surveys/api/urls.py
from django.urls import path, include
from surveys.api.views import (
    composite_survey_list_api_view,
    composite_survey_api_view,
    submit_survey_api_view
)

# Gom nhóm tất cả API của phiên bản v1 vào một danh sách
v1_patterns = [
    # 1. API lấy danh sách các Bộ khảo sát (Hiển thị màn hình chính Flutter)
    path('composite-surveys/', composite_survey_list_api_view, name='api-v1-composite-survey-list'),
    
    # 2. API lấy chi tiết cấu trúc câu hỏi của một Bộ khảo sát
    path('composite-surveys/<int:pk>/', composite_survey_api_view, name='api-v1-composite-survey-detail'),
    
    # 3. API nhận kết quả làm bài & chấm điểm từ Flutter gửi lên
    path('surveys/submit/', submit_survey_api_view, name='api-v1-survey-submit'),
]

urlpatterns = [
    # Gắn tiền tố 'v1/' cho toàn bộ nhóm API trên
    path('v1/', include(v1_patterns)),
]