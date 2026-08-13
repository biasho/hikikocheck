from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.home, name='home'),         # URL: /
    path('about/', views.about, name='about'), # URL: /about/
]