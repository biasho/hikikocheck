from django.urls import path, include  # ⚠️ Nhớ thêm 'include' vào đây
from . import views

# Khai báo app_name để tạo namespace cho ứng dụng surveys
app_name = 'surveys'

urlpatterns = [
    # 🎯 0. ĐƯỜNG DẪN TÍCH HỢP API (Cho Flutter / Mobile App)
    path('api/', include('surveys.api.urls')),

    # 🎯 1. CÁC PATH CỐ ĐỊNH TỔNG HỢP / BÁO CÁO (Đặt lên trên cùng)
    path('', views.survey_list, name='survey_list'),
    path('send-email-result/', views.send_email_result, name='send_email_result'),
    path('report/', views.reconnect360_report_view, name='reconnect_report'),

    # 🎯 2. BỘ KHẢO SÁT / COMBO CỐ ĐỊNH (Ví dụ Reconnect 360)
    path(
        'khao-sat-xu-huong-thu-minh-va-muc-do-ket-noi-xa-hoi-o-hoc-sinh-thcs-thpt-1/', 
        views.reconnect360_detail, 
        name='reconnect360_detail'
    ),
    
    # 🎯 3. BỘ KHẢO SÁT DẠNG ĐỘNG (COMBO)
    path('combo/<slug:slug>/', views.combo_detail, name='combo_detail'),

    # 🎯 4. CÁC ĐƯỜNG DẪN KHẢO SÁT ĐƠN / CHI TIẾT (ĐẶT PHÍA DƯỚI CÙNG)
    path('detail/<slug:slug>/', views.survey_detail, name='survey_detail'),
    path('detail/<slug:slug>/submit/', views.submit_detail, name='submit_detail'),
    path('thank-you/<slug:slug>/', views.survey_thankyou, name='survey_thankyou'),
    
    # Các URL dùng slug chung chung (đặt dưới thấp để tránh đè các URL cố định ở trên)
    path('<slug:slug>/submit/', views.submit_survey, name='submit_survey'),
    path('<slug:slug>/result/', views.survey_result_view, name='survey_result'),
    path('<int:survey_id>/statistics/', views.survey_statistics_view, name='survey_statistics'),
]