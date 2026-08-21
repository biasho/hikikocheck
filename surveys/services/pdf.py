import io
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from xhtml2pdf import pisa

from core.models import Lead, Source


def save_lead_from_survey(email_to, submission):
    """Lưu Lead từ thông tin gửi email báo cáo khảo sát"""
    if not email_to:
        return

    clean_email = email_to.strip().lower()

    if Lead.objects.filter(email=clean_email).exists():
        return

    try:
        source_obj, _ = Source.objects.get_or_create(
            name='survey_pdf_report',
            defaults={'description': 'Nguồn thu thập từ việc tải báo cáo PDF khảo sát'}
        )

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


def send_pdf_email(
    email_to,
    submission,
    threshold=None,
    threshold_abc=None,
    threshold_d=None,
    chart_base64=None,
    request=None
):
    """Khởi tạo PDF từ template HTML và gửi qua Email"""
    if email_to:
        clean_email = email_to.strip().lower()
        
        if not submission.email:
            submission.email = clean_email
            
        if request and not submission.user:
            if not request.session.session_key:
                request.session.create()
            submission.session_key = request.session.session_key
            
        submission.save()
        save_lead_from_survey(clean_email, submission)

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

    context = {
        'submission': submission,
        'survey': survey_obj,
        'survey_title': survey_title,
        'total_score': submission.total_score,
        'threshold': threshold,
        'threshold_abc': threshold_abc,
        'threshold_d': threshold_d,
        'chart_base64': chart_base64,
    }

    html_content = render_to_string('surveys/pdf_report_template.html', context)

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_content,
        dest=pdf_buffer,
        encoding='utf-8'
    )

    if pisa_status.err:
        raise Exception("Lỗi trong quá trình khởi tạo PDF từ HTML!")

    pdf_data = pdf_buffer.getvalue()
    pdf_buffer.close()

    subject = f"Báo cáo kết quả khảo sát: {survey_title}"
    body = (
        f"Xin chào,\n\n"
        f"Cảm ơn bạn đã tham gia bài khảo sát '{survey_title}'.\n"
        f"Tổng điểm của bạn: {submission.total_score} điểm.\n\n"
        f"Vui lòng xem file PDF đính kèm để biết thêm chi tiết.\n\n"
        f"Trân trọng,\nHệ thống Reconnect 360"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@reconnect360.vn'),
        to=[email_to],
    )

    file_name = f"Bao_cao_{survey_slug}_{submission.id}.pdf"
    email.attach(file_name, pdf_data, 'application/pdf')
    email.send(fail_silently=False)