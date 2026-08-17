import json
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST

from .models import Survey, Submission, Answer, SurveyResultThreshold
from questions.models import Question, Option
from .services.pdf import send_pdf_email
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import Survey, Submission, SurveyResultThreshold

def _get_survey_by_slug(slug):
    """Hàm phụ trợ lấy Survey bằng ID tách từ đuôi Slug"""
    try:
        survey_id = slug.split('-')[-1]
        return get_object_or_404(Survey, pk=survey_id, is_active=True)
    except (ValueError, IndexError):
        return get_object_or_404(Survey, slug=slug, is_active=True)


def survey_list(request):
    """Hiển thị danh sách các bài khảo sát đang hoạt động"""
    surveys = Survey.objects.filter(is_active=True)
    return render(request, 'surveys/survey_list.html', {'surveys': surveys})


def survey_detail(request, slug):
    """Hiển thị trang chi tiết bài khảo sát (Giao diện làm bài)"""
    survey = _get_survey_by_slug(slug)
    questions = survey.questions.prefetch_related('options').all()

    context = {
        'survey': survey,
        'questions': questions,
    }
    return render(request, 'surveys/survey_detail.html', context)


def submit_survey(request, slug):
    """Xử lý nộp bài khảo sát, tính điểm, cấu hình Chart.js JSON và trả về trang survey_result.html"""
    survey = _get_survey_by_slug(slug)

    if request.method == 'POST':
        user = request.user if request.user.is_authenticated else None

        if not user and not request.session.session_key:
            request.session.create()

        total_score = 0
        answers_to_create = []

        with transaction.atomic():
            submission = Submission.objects.create(
                survey=survey,
                user=user,
                total_score=0
            )

            for key, value in request.POST.items():
                if key.startswith('question_'):
                    question_id = key.split('_')[1]
                    question = Question.objects.filter(id=question_id, surveys=survey).first()

                    if not question:
                        continue

                    if question.question_type in ['single_choice', 'rating']:
                        selected_option = Option.objects.filter(id=value, question=question).first()
                        if selected_option:
                            option_score = getattr(selected_option, 'score', getattr(selected_option, 'point', 0))
                            total_score += option_score

                            answers_to_create.append(
                                Answer(
                                    submission=submission,
                                    question=question,
                                    selected_option=selected_option
                                )
                            )

                    elif question.question_type == 'text':
                        text_val = value.strip()
                        if text_val:
                            answers_to_create.append(
                                Answer(
                                    submission=submission,
                                    question=question,
                                    text_answer=text_val
                                )
                            )

            Answer.objects.bulk_create(answers_to_create)

            submission.total_score = total_score
            submission.save()

            request.session['last_submission_id'] = submission.id

        matched_threshold = SurveyResultThreshold.objects.filter(
            survey=survey,
            min_score__lte=total_score,
            max_score__gte=total_score
        ).first()

        # 📊 🎯 CẤU HÌNH DỮ LIỆU CHART.JS TRẢ VỀ FRONTEND (JSON)
        all_thresholds = list(survey.thresholds.all().order_by('min_score'))
        chart_data_json = None

        if all_thresholds:
            labels = []
            scores = []
            matched_index = -1

            for idx, t in enumerate(all_thresholds):
                title = t.title
                labels.append(title[:12] + '...' if len(title) > 15 else title)
                scores.append(t.max_score)
                if matched_threshold and t.id == matched_threshold.id:
                    matched_index = idx

            chart_data = {
                'labels': labels,
                'scores': scores,
                'total_score': total_score,
                'matched_index': matched_index
            }
            chart_data_json = json.dumps(chart_data)

        context = {
            'survey': survey,
            'submission': submission,
            'total_score': total_score,
            'threshold': matched_threshold,
            'total_questions': survey.questions.count(),
            'chart_data_json': chart_data_json,
        }
        return render(request, 'surveys/survey_result.html', context)

    return redirect('surveys:survey_detail', slug=survey.slug)


@require_POST
def send_email_result(request):
    """View xử lý AJAX từ Email Modal (Nhận thêm chart_base64 từ client gửi lên)"""
    email = request.POST.get('email', '').strip()
    submission_id = request.POST.get('submission_id')
    chart_base64 = request.POST.get('chart_base64', '').strip()

    if not email or not submission_id:
        return JsonResponse({'success': False, 'message': 'Vui lòng cung cấp đầy đủ thông tin!'}, status=400)

    try:
        submission = Submission.objects.get(pk=submission_id)

        threshold = SurveyResultThreshold.objects.filter(
            survey=submission.survey,
            min_score__lte=submission.total_score,
            max_score__gte=submission.total_score
        ).first()

        # Truyền chart_base64 nhận từ Client sang hàm gửi email tạo PDF
        send_pdf_email(email, submission, threshold, chart_base64=chart_base64)

        return JsonResponse({'success': True, 'message': 'Gửi báo cáo PDF thành công! Vui lòng kiểm tra hòm thư.'})

    except Submission.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy lượt nộp bài này!'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}, status=500)


def reconnect_report_view(request, slug="khao-sat-xu-huong-thu-minh-va-muc-do-ket-noi-xa-hoi-o-hoc-sinh-thcs-2"):
    """View hiển thị báo cáo thống kê khảo sát Reconnect 360° hỗ trợ AJAX Fetch lọc theo thời gian"""
    survey = _get_survey_by_slug(slug)
    
    # Lấy tham số lọc từ Request (Mặc định: current_year)
    time_filter = request.GET.get('time_filter', 'current_year')
    year_from = request.GET.get('year_from')
    year_to = request.GET.get('year_to')
    
    # Khởi tạo Queryset bài nộp của Survey
    submissions = Submission.objects.filter(survey=survey)
    
    # 🕒 BỘ LỌC THỜI GIAN THEO DATABASE (Sử dụng trường submitted_at)
    now = timezone.now()
    
    if time_filter == 'current_year':
        submissions = submissions.filter(submitted_at__year=now.year)
    elif time_filter == '3_months':
        three_months_ago = now - timedelta(days=90)
        submissions = submissions.filter(submitted_at__gte=three_months_ago)
    elif time_filter == '6_months':
        six_months_ago = now - timedelta(days=180)
        submissions = submissions.filter(submitted_at__gte=six_months_ago)
    elif time_filter == '1_year':
        one_year_ago = now - timedelta(days=365)
        submissions = submissions.filter(submitted_at__gte=one_year_ago)
    elif time_filter == 'last_year':
        submissions = submissions.filter(submitted_at__year=now.year - 1)
    elif time_filter == 'custom' and year_from and year_to:
        try:
            start_year = int(year_from)
            end_year = int(year_to)
            submissions = submissions.filter(
                submitted_at__year__gte=start_year,
                submitted_at__year__lte=end_year
            )
        except ValueError:
            pass

    # Tính toán tổng số lượng
    total_participants = submissions.count()
    total_completed = total_participants  # Mỗi bản ghi Submission tạo ra mặc định là bài đã nộp thành công
    
    completion_rate = round((total_completed / total_participants * 100), 1) if total_participants > 0 else 0
    
    # Lấy danh sách các ngưỡng kết quả (thresholds)
    thresholds = SurveyResultThreshold.objects.filter(survey=survey).order_by('min_score')
    
    threshold_stats = [
        {
            'title': t.title,
            'min_score': t.min_score,
            'max_score': t.max_score,
            'count': 0
        }
        for t in thresholds
    ]
    
    # Phân loại điểm bài nộp vào từng ngưỡng
    for sub in submissions:
        score = sub.total_score
        for stat in threshold_stats:
            if stat['min_score'] <= score <= stat['max_score']:
                stat['count'] += 1
                break

    # Đóng gói dữ liệu trả về
    data = {
        'total_participants': total_participants,
        'total_completed': total_completed,
        'completion_rate': completion_rate,
        'threshold_stats': threshold_stats,
    }

    # 🚀 Nếu Yêu cầu đến từ Fetch AJAX thì trả về JsonResponse
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(data)

    # Nếu truy cập trang trực tiếp từ trình duyệt thì render template HTML
    context = {
        'survey': survey,
        **data
    }
    return render(request, 'surveys/reconnect_report.html', context)