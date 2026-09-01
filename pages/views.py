from django.shortcuts import render

def home(request):
    """View cho Trang chủ chính toàn trang"""
    return render(request, 'pages/index.html')

def about(request):
    """View cho trang Giới thiệu"""
    return render(request, 'pages/about.html')
def about_us(request):
    return render(request, 'pages/about_us.html')

def guide(request):
    return render(request, 'pages/guide.html')  # Tên file template hướng dẫn vừa tạo
def privacy(request):
    return render(request, 'pages/privacy.html')  # Tên file template hướng dẫn vừa tạo
def terms(request):
    return render(request, 'pages/terms.html')  # Tên file template hướng dẫn vừa tạo
def sitemap(request):
    return render(request, 'pages/sitemap.html')  # Tên file template hướng dẫn vừa tạo

def methodology(request):
    return render(request, 'pages/methodology.html')  # Tên file template hướng dẫn vừa tạo