from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Role  # Import thêm model Role

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # Lấy Role 'Member' (hoặc tự động tạo Role 'Member' nếu trong DB chưa có)
        default_role, _ = Role.objects.get_or_create(
            name="Member",
            defaults={"description": "Thành viên mặc định của hệ thống"}
        )
        
        # Tạo UserProfile và gán Role mặc định
        UserProfile.objects.create(user=instance, role=default_role)
    else:
        # Kiểm tra xem user đã có profile chưa trước khi save
        if hasattr(instance, 'profile'):
            instance.profile.save()