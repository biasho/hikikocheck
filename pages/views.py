from django.shortcuts import render

def home(request):
    """View cho Trang chủ chính toàn trang"""
    return render(request, 'pages/index.html')

def about(request):
    """View cho trang Giới thiệu"""
    return render(request, 'pages/about.html')