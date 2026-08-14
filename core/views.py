from django.shortcuts import render

# Create your views here.
from core.models import Lead, Source

# 1. Lấy hoặc tạo sẵn nguồn 'survey_pdf_report' trong bảng Source
source_obj, _ = Source.objects.get_or_create(
    name='survey_pdf_report',
    defaults={'description': 'Nguồn thu thập từ báo cáo PDF bài khảo sát'}
)

# 2. Lưu lead liên kết với đối tượng Source đó
Lead.objects.get_or_create(
    email=email,
    defaults={
        'user': request.user if request.user.is_authenticated else None,
        'source': source_obj,               # Truyền object Source vào đây
        'object_id': submission.survey.id   # ID bài khảo sát tương ứng
    }
)