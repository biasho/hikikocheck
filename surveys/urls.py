from django.urls import path
from . import views

# Khai báo app_name để tạo namespace cho ứng dụng surveys
app_name = 'surveys'

urlpatterns = [
    # Danh sách khảo sát: /surveys/
    path('', views.survey_list, name='survey_list'),
    
    # 🎯 ĐƯA URL TĨNH LÊN TRÊN ĐỂ KHÔNG BỊ NHẦM LẪN VỚI SLUG
    path('send-email-result/', views.send_email_result, name='send_email_result'),
    path('report/', views.reconnect_report_view, name='reconnect_report'),
   # 1. ĐẶT PATH CỐ ĐỊNH NÀY LÊN ĐẦU
    # Django sẽ khớp URL này trước tiên khi người dùng bấm vào bài khảo sát THCS
    path(
        'khao-sat-xu-huong-thu-minh-va-muc-do-ket-noi-xa-hoi-o-hoc-sinh-thcs-1/', 
        views.reconnect360_detail, 
        name='reconnect360_detail'
    ),
    # Trang chi tiết khảo sát: /surveys/danh-gia-suc-khoe-102/
    path('<slug:slug>/', views.survey_detail, name='survey_detail'),
    
    # Nộp bài khảo sát: /surveys/danh-gia-suc-khoe-102/submit/
    path('<slug:slug>/submit/', views.submit_survey, name='submit_survey'),
]