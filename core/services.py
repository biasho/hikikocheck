from core.models import Lead, Source

def save_lead_from_survey(email_to, submission):
    """
    Hàm kiểm tra và lưu Lead từ báo cáo khảo sát.
    - Nếu email đã tồn tại: Không làm gì cả (bỏ qua).
    - Nếu email chưa tồn tại: Tạo mới Lead gắn với nguồn 'survey_pdf_report'.
    """
    if not email_to:
        return

    # Chuẩn hóa email (viết thường, xóa khoảng trắng thừa)
    clean_email = email_to.strip().lower()

    # 1. Kiểm tra xem email đã tồn tại trong hệ thống chưa
    if Lead.objects.filter(email=clean_email).exists():
        # Đã tồn tại -> Không tạo mới, thoát hàm luôn
        return

    try:
        # 2. Lấy hoặc tạo sẵn nguồn 'survey_pdf_report'
        source_obj, _ = Source.objects.get_or_create(
            name='survey_pdf_report',
            defaults={'description': 'Nguồn thu thập từ việc tải báo cáo PDF khảo sát'}
        )

        # 3. Tiến hành tạo mới vì email chưa tồn tại
        Lead.objects.create(
            email=clean_email,
            user=submission.user if hasattr(submission, 'user') and submission.user else None,
            source=source_obj,
            object_id=submission.survey.id  # ID cụ thể của bài khảo sát
        )
    except Exception as e:
        print(f"Lỗi khi lưu Lead: {str(e)}")