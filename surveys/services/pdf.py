import base64
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
# Giả sử bạn dùng WeasyPrint hoặc xhtml2pdf để render PDF từ HTML
from xhtml2pdf import pisa 
import io

def send_pdf_email(email_to, submission, threshold=None, chart_base64=None):
    """
    Hàm tạo file PDF báo cáo kết quả và gửi Email đính kèm.
    
    :param email_to: Địa chỉ email người nhận
    :param submission: Instance của Submission
    :param threshold: Instance của SurveyResultThreshold (nếu có)
    :param chart_base64: Chuỗi Base64 của biểu đồ Chart.js gửi từ Frontend
    """
    
    # 1. Chuẩn bị context để render template HTML xuất PDF
    context = {
        'submission': submission,
        'survey': submission.survey,
        'total_score': submission.total_score,
        'threshold': threshold,
        'chart_base64': chart_base64,  # Dùng trực tiếp trong <img> của PDF HTML template
    }

    # 2. Render HTML template dành riêng cho Báo cáo PDF
    html_content = render_to_string('surveys/pdf_report_template.html', context)

    # 3. Chuyển đổi HTML sang dữ liệu PDF (ví dụ sử dụng xhtml2pdf)
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

    if pisa_status.err:
        raise Exception("Lỗi trong quá trình khởi tạo PDF!")

    pdf_data = pdf_buffer.getvalue()
    pdf_buffer.close()

    # 4. Cấu hình Email
    subject = f"Báo cáo kết quả khảo sát: {submission.survey.title}"
    body = (
        f"Xin chào,\n\n"
        f"Cảm ơn bạn đã tham gia bài khảo sát '{submission.survey.title}'.\n"
        f"Tổng điểm của bạn: {submission.total_score} điểm.\n\n"
        f"Vui lòng xem file PDF đính kèm để biết thêm chi tiết phân tích và lời khuyên.\n\n"
        f"Trân trọng,\nHệ thống HikikoCheck"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hikikocheck.com'),
        to=[email_to],
    )

    # 5. Đính kèm file PDF vào Email
    file_name = f"Bao_cao_{submission.survey.slug}_{submission.id}.pdf"
    email.attach(file_name, pdf_data, 'application/pdf')

    # 6. Gửi Email
    email.send(fail_silently=False)