# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm
from .models import UserProfile  # Import đúng tên UserProfile


# 1. Xử lý Đăng ký Tài khoản
def register_view(request):
    if request.user.is_authenticated:
        return redirect('pages:home')
        
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Đăng ký tài khoản thành công!")
            return redirect('pages:home')
    else:
        form = RegisterForm()
        
    return render(request, 'users/register.html', {'form': form})


# 2. Xử lý Đăng nhập
def login_view(request):
    if request.user.is_authenticated:
        return redirect('pages:home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('pages:home')
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không chính xác.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'users/login.html', {'form': form})


# 3. Xử lý Đăng xuất
def logout_view(request):
    logout(request)
    messages.info(request, "Bạn đã đăng xuất khỏi hệ thống.")
    return redirect('users:login')


# 4. Trang Hồ sơ cá nhân
@login_required(login_url='users:login')
def profile_view(request):
    # Dùng UserProfile thay vì Profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Cập nhật thông tin First Name / Last Name trong User model
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()

        # Cập nhật thông tin trong UserProfile
        profile.phone_number = request.POST.get('phone_number', '').strip()  # Đúng tên phone_number
        profile.bio = request.POST.get('bio', '').strip()

        # Cập nhật Avatar nếu tải lên file mới
        if 'avatar' in request.FILES:
            if profile.avatar and profile.avatar.name != 'avatars/default.png':
                profile.avatar.delete(save=False)
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, "Cập nhật thông tin cá nhân thành công!")
        return redirect('users:profile')

    return render(request, 'users/profile.html', {
        'user': request.user,
        'profile': profile
    })