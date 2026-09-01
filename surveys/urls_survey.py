from django.urls import path
from . import views

app_name = 'survey_single'

urlpatterns = [
    # Kết quả: https://reconnect360.vn/survey/<slug>/
    path('<slug:slug>/', views.survey_detail, name='survey_detail'),
    
    # Kết quả: https://reconnect360.vn/survey/<slug>/submit/
    path('<slug:slug>/submit/', views.submit_survey, name='submit_survey'),
]