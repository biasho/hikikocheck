from django.urls import path
from . import views

# Khai báo app_name để tạo namespace cho ứng dụng surveys
app_name = 'surveys'

urlpatterns = [
    # Danh sách tất cả khảo sát: /surveys/
    path('', views.survey_list, name='survey_list'),
    
    # 🎯 1. CÁC PATH CỐ ĐỊNH TỔNG HỢP / BÁO CÁO
    path('send-email-result/', views.send_email_result, name='send_email_result'),
    path('report/', views.reconnect360_report_view, name='reconnect_report'),

    # 🎯 2. BỘ KHẢO SÁT / COMBO (Dùng 'surveys/' - Cố định hoặc Dynamic)
    path(
        'khao-sat-xu-huong-thu-minh-va-muc-do-ket-noi-xa-hoi-o-hoc-sinh-thcs-thpt-1/', 
        views.reconnect360_detail, 
        name='reconnect360_detail'
    ),
    # 🎯 1. BỘ KHẢO SÁT DÙNG DẠNG ĐỘNG (Dành cho tất cả các bộ khảo sát sau này)
    # Kết quả URL: domain.com/surveys/combo/ten-bo-khao-sat/
    path('combo/<slug:slug>/', views.combo_detail, name='combo_detail'),
    # Nếu muốn dùng slug động cho các BỘ KHẢO SÁT khác trong tương lai:
    # path('combo/<slug:slug>/', views.reconnect360_detail, name='combo_detail'),
    path('<slug:slug>/submit/', views.submit_survey, name='submit_survey'),
    # THÊM DÒNG NÀY CHO TRANG KẾT QUẢ:
    path('<slug:slug>/result/', views.survey_result_view, name='survey_result'),
    path('<int:survey_id>/statistics/', views.survey_statistics_view, name='survey_statistics'),
   # 🎯 Khảo sát đơn dùng 'detail'
    path('thank-you/<slug:slug>', views.survey_thankyou, name='survey_thankyou'),
    path('detail/<slug:slug>/', views.survey_detail, name='survey_detail'),
    path('detail/<slug:slug>/submit/', views.submit_detail, name='submit_detail'),
]