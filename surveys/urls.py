from django.urls import path
from . import views

# Khai báo app_name để tạo namespace cho ứng dụng surveys
app_name = 'surveys'

urlpatterns = [
    # Danh sách khảo sát: /surveys/
    path('', views.survey_list, name='survey_list'),
    
    # Trang chi tiết khảo sát: /surveys/danh-gia-suc-khoe-102/
    path('<slug:slug>/', views.survey_detail, name='survey_detail'),
    
    # Nộp bài khảo sát: /surveys/danh-gia-suc-khoe-102/submit/
    path('<slug:slug>/submit/', views.submit_survey, name='submit_survey'),
    # URL AJAX gửi Email
    path('send-email-result/', views.send_email_result, name='send_email_result'),
]