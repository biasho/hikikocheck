from django.urls import path
from . import views

# Khai báo app_name để tạo namespace cho ứng dụng surveys
app_name = 'surveys'

urlpatterns = [
    # Đường dẫn ví dụ: /surveys/1/
    path('', views.survey_list, name='survey_list'),  # URL: /surveys/
    path('<int:survey_id>/', views.survey_detail, name='survey_detail'),
    path('<int:survey_id>/submit/', views.submit_survey, name='submit_survey'),
]