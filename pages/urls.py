from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.home, name='home'),         # URL: /
    path('guide/', views.guide, name='guide'), # URL: /about/
    path('about/', views.about, name='about'), # URL: /about/
    path('about-us/', views.about_us, name='about_us'),   # Trang Về chúng tôi
]