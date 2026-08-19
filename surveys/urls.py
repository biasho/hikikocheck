from django.urls import path
from . import views

# Khai báo app_name để tạo namespace cho ứng dụng surveys
app_name = 'surveys'

urlpatterns = [
    # Danh sách khảo sát: /surveys/
    path('', views.survey_list, name='survey_list'),
    
    # 🎯 1. CÁC PATH CỐ ĐỊNH PHẢI ĐẶT LÊN ĐẦU
    path('send-email-result/', views.send_email_result, name='send_email_result'),
   # path('report/', views.reconnect_report_view, name='reconnect_report'),
    path('report/', views.reconnect360_report_view, name='reconnect_report'),

    # 🎯 2. BÀI KHẢO SÁT TỔNG HỢP CỐ ĐỊNH (RECONNECT 360)
    path(
        'khao-sat-xu-huong-thu-minh-va-muc-do-ket-noi-xa-hoi-o-hoc-sinh-thcs-1/', 
        views.reconnect360_detail, 
        name='reconnect360_detail'
    ),

    # 🎯 3. XỬ LÝ NỘP BÀI KHẢO SÁT (Được gọi từ Form detail.html)
    path('<slug:slug>/submit/', views.submit_survey, name='submit_survey'),

    # 🎯 4. CÁC BÀI KHẢO SÁT ĐƠN (ĐẶT Ở CUỐI CÙNG ĐỂ KHÔNG BỊ NUỐT SLUG)
    path('<slug:slug>/', views.survey_detail, name='survey_detail'),
]