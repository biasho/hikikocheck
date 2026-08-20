import io
import base64
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from xhtml2pdf import pisa 

# Import model Lead và Source từ app core
from core.models import Lead, Source

def save_lead_from_survey(email_to, submission):
    """Hàm kiểm tra và lưu Lead từ báo cáo khảo sát (Chỉ tạo mới nếu email chưa tồn tại)"""
    if not email_to:
        return

    clean_email = email_to.strip().lower()

    if Lead.objects.filter(email=clean_email).exists():
        return  # Đã có rồi thì bỏ qua

    try:
        source_obj, _ = Source.objects.get_or_create(
            name='survey_pdf_report',
            defaults={'description': 'Nguồn thu thập từ việc tải báo cáo PDF khảo sát'}
        )

        # Lấy ID đối tượng an toàn (Survey hoặc CompositeSurvey)
        obj_id = None
        if getattr(submission, 'survey', None):
            obj_id = submission.survey.id
        elif getattr(submission, 'composite_survey', None):
            obj_id = submission.composite_survey.id

        Lead.objects.create(
            email=clean_email,
            user=submission.user if hasattr(submission, 'user') and submission.user else None,
            source=source_obj,
            object_id=obj_id
        )
    except Exception as e:
        print(f"Lỗi khi lưu Lead: {str(e)}")


def send_pdf_email(email_to, submission, threshold=None, chart_base64=None, request=None):
    """Hàm tạo PDF, gửi email đính kèm, cập nhật Submission và lưu Lead"""
    
    if email_to:
        clean_email = email_to.strip().lower()
        
        # 🎯 1. Cập nhật email vào Submission nếu trước đó chưa có
        if not submission.email:
            submission.email = clean_email
            
        # 🎯 2. Lưu session_key nếu người dùng chưa đăng nhập (lấy từ request)
        if request and not submission.user:
            if not request.session.session_key:
                request.session.create()
            submission.session_key = request.session.session_key
            
        # Lưu lại thay đổi vào cơ sở dữ liệu
        submission.save()

        # 🎯 3. Tự động kiểm tra và lưu Lead
        save_lead_from_survey(clean_email, submission)

    # 🎯 Trích xuất Survey Object, Title và Slug an toàn cho cả Single & Composite Survey
    survey_obj = getattr(submission, 'survey', None)
    
    if survey_obj:
        survey_title = survey_obj.title
        survey_slug = survey_obj.slug
    elif getattr(submission, 'composite_survey', None):
        survey_obj = submission.composite_survey
        survey_title = submission.composite_survey.title
        survey_slug = submission.composite_survey.slug
    else:
        survey_title = "Báo cáo Khảo sát Reconnect 360"
        survey_slug = "khao-sat"

    # 4. Chuẩn bị context render PDF
    context = {
        'submission': submission,
        'survey': survey_obj,
        'survey_title': survey_title,
        'total_score': submission.total_score,
        'threshold': threshold,
        'chart_base64': chart_base64,
    }

    html_content = render_to_string('surveys/pdf_report_template.html', context)

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

    if pisa_status.err:
        raise Exception("Lỗi trong quá trình khởi tạo PDF!")

    pdf_data = pdf_buffer.getvalue()
    pdf_buffer.close()

    subject = f"Báo cáo kết quả khảo sát: {survey_title}"
    body = (
        f"Xin chào,\n\n"
        f"Cảm ơn bạn đã tham gia bài khảo sát '{survey_title}'.\n"
        f"Tổng điểm của bạn: {submission.total_score} điểm.\n\n"
        f"Vui lòng xem file PDF đính kèm để biết thêm chi tiết.\n\n"
        f"Trân trọng,\nHệ thống HikikoCheck"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hikikocheck.com'),
        to=[email_to],
    )

    file_name = f"Bao_cao_{survey_slug}_{submission.id}.pdf"
    email.attach(file_name, pdf_data, 'application/pdf')
    email.send(fail_silently=False)