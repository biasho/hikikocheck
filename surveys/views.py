import json
from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from questions.models import Option, Question
from core.models import Lead, Source  # Import Lead và Source từ app core
from .models import Answer, CompositeSurvey, CompositeSurveyItem, Submission, Survey, SurveyResultThreshold
from .services.pdf import send_pdf_email


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
    """Hiển thị trang chi tiết bài khảo sát đơn lẻ"""
    survey = _get_survey_by_slug(slug)
    questions = survey.questions.prefetch_related('options').all()

    context = {
        'survey': survey,
        'questions': questions,
    }
    return render(request, 'surveys/survey_detail.html', context)


def reconnect360_detail(request, slug="khao-sat-xu-huong-thu-minh-va-muc-do-ket-noi-xa-hoi-o-hoc-sinh-thcs-1"):
    """
    Hiển thị giao diện Bộ khảo sát tổng hợp (CompositeSurvey) gồm nhiều phần.
    Sắp xếp câu hỏi theo group__code của Model Group.
    """
    composite = get_object_or_404(
        CompositeSurvey,
        slug=slug,
        is_active=True
    )
    
    questions_prefetch = Prefetch(
        'survey__questions',
        queryset=Question.objects.select_related('group').order_by('group__code', 'id').prefetch_related('options')
    )

    survey_items = composite.items.select_related('survey').prefetch_related(
        questions_prefetch
    ).order_by('order')

    context = {
        'composite': composite,
        'survey_items': survey_items,
    }
    return render(request, 'surveys/reconnect360/detail.html', context)


def submit_survey(request, slug):
    """
    Xử lý nộp bài cho Bộ khảo sát tổng hợp (CompositeSurvey),
    tính điểm theo từng Group câu hỏi (A, B, C, D) và áp dụng các ngưỡng tương ứng.
    Hỗ trợ xử lý single_choice, rating, multiple_choice (có kèm text nhập thêm cho Khác/Other), và text.
    """
    composite = get_object_or_404(CompositeSurvey, slug=slug, is_active=True)

    if request.method == 'POST':
        user = None
        lead = None
        source_obj = Source.objects.filter(name='survey_reconnect360').first()

        # --- 1. XỬ LÝ ĐỊNH DANH USER KHẢO SÁT ---
        if request.user.is_authenticated:
            user = request.user
            lead, _ = Lead.objects.get_or_create(
                user=user,
                defaults={
                    'email': user.email,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'source': source_obj,
                }
            )
        else:
            if not request.session.session_key:
                request.session.create()

            # Lấy Lead cũ từ session nếu đã từng tạo
            lead_id_from_session = request.session.get('survey_lead_id')
            if lead_id_from_session:
                lead = Lead.objects.filter(id=lead_id_from_session).first()

            # Nếu chưa có Lead, tự động tạo Lead ẩn danh cho phiên làm bài này
            if not lead:
                lead = Lead.objects.create(
                    full_name="Học sinh vãng lai",
                    source=source_obj
                )
                request.session['survey_lead_id'] = lead.id

        total_score = 0
        answers_to_create = []

        survey_scores = {}
        group_scores = {}  # { 'A': score, 'B': score, ... }
        group_names = {}   # { 'A': 'Tên nhóm A', ... }

        # Tra cứu nhanh question_id -> survey_id
        question_to_survey_map = {}
        items = composite.items.select_related('survey').prefetch_related('survey__questions')
        for item in items:
            for q in item.survey.questions.all():
                question_to_survey_map[q.id] = item.survey.id

        with transaction.atomic():
            submission = Submission.objects.create(
                composite_survey=composite,
                user=user,
                lead=lead,
                email=lead.email if lead else None,
                session_key=request.session.session_key,
                total_score=0
            )

            # Thu thập các keys đã xử lý cho multiple_choice để tránh lặp lại
            processed_mc_questions = set()

            for key in request.POST.keys():
                if key.startswith('question_') and not '_text_' in key:
                    try:
                        question_id = int(key.split('_')[1])
                    except (IndexError, ValueError):
                        continue

                    question = Question.objects.select_related('group').filter(id=question_id).first()
                    if not question:
                        continue

                    parent_survey_id = question_to_survey_map.get(question.id)

                    # A. SINGLE CHOICE & RATING
                    if question.question_type in ['single_choice', 'rating']:
                        val = request.POST.get(key)
                        selected_option = Option.objects.filter(id=val, question=question).first()
                        if selected_option:
                            option_score = getattr(selected_option, 'score', getattr(selected_option, 'point', 0))
                            
                            total_score += option_score

                            if parent_survey_id:
                                survey_scores[parent_survey_id] = survey_scores.get(parent_survey_id, 0) + option_score

                            if question.group:
                                g_code = question.group.code.upper().strip()
                                group_scores[g_code] = group_scores.get(g_code, 0) + option_score
                                if g_code not in group_names:
                                    group_names[g_code] = question.group.name or f"Nhóm {g_code}"

                            answers_to_create.append(
                                Answer(
                                    submission=submission,
                                    question=question,
                                    selected_option=selected_option
                                )
                            )

                    # B. MULTIPLE CHOICE (Chọn nhiều + Nhập text phụ nếu chọn 'Khác'/'Other')
                    elif question.question_type == 'multiple_choice':
                        if question_id in processed_mc_questions:
                            continue
                        processed_mc_questions.add(question_id)

                        selected_ids = request.POST.getlist(key)
                        for opt_id in selected_ids:
                            selected_option = Option.objects.filter(id=opt_id, question=question).first()
                            if selected_option:
                                # Kiểm tra xem lựa chọn có đi kèm ô nhập văn bản (Khác/Other hoặc thuộc tính custom)
                                custom_text = request.POST.get(f'question_{question.id}_text_{opt_id}', '').strip()
                                
                                option_score = getattr(selected_option, 'score', getattr(selected_option, 'point', 0))
                                total_score += option_score

                                if parent_survey_id:
                                    survey_scores[parent_survey_id] = survey_scores.get(parent_survey_id, 0) + option_score

                                if question.group:
                                    g_code = question.group.code.upper().strip()
                                    group_scores[g_code] = group_scores.get(g_code, 0) + option_score
                                    if g_code not in group_names:
                                        group_names[g_code] = question.group.name or f"Nhóm {g_code}"

                                answers_to_create.append(
                                    Answer(
                                        submission=submission,
                                        question=question,
                                        selected_option=selected_option,
                                        text_answer=custom_text if custom_text else ""
                                    )
                                )

                    # C. TEXT
                    elif question.question_type == 'text':
                        text_val = request.POST.get(key, '').strip()
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
            submission.score_a = group_scores.get('A', 0)
            submission.score_b = group_scores.get('B', 0)
            submission.score_c = group_scores.get('C', 0)
            submission.score_d = group_scores.get('D', 0)
            submission.save()
            request.session['last_submission_id'] = submission.id

      # --- 2. TÍNH ĐIỂM CÁC NGƯỠNG RIÊNG THEO GROUP CODE ('ALL_ABC', 'D') ---
        score_abc = group_scores.get('A', 0) + group_scores.get('B', 0) + group_scores.get('C', 0)
        score_d = group_scores.get('D', 0)

        threshold_abc = None
        threshold_d = None
        all_thresholds_abc = []
        all_thresholds_d = []

        # Tự động tìm ngưỡng dựa trên group code thay vì cố định vị trí part_items
        for item in composite.items.select_related('survey').all():
            s_obj = item.survey

            # Kiểm tra ngưỡng cho 'all_abc'
            if not threshold_abc:
                t_abc = SurveyResultThreshold.objects.filter(
                    survey=s_obj,
                    min_score__lte=score_abc,
                    max_score__gte=score_abc,
                    group__code__iexact='all_abc'
                ).first()
                if t_abc:
                    threshold_abc = t_abc
                    all_thresholds_abc = list(
                        SurveyResultThreshold.objects.filter(survey=s_obj, group__code__iexact='all_abc')
                        .order_by('min_score')
                    )

            # Kiểm tra ngưỡng cho 'D'
            if not threshold_d:
                t_d = SurveyResultThreshold.objects.filter(
                    survey=s_obj,
                    min_score__lte=score_d,
                    max_score__gte=score_d,
                    group__code__iexact='D'
                ).first()
                if t_d:
                    threshold_d = t_d
                    all_thresholds_d = list(
                        SurveyResultThreshold.objects.filter(survey=s_obj, group__code__iexact='D')
                        .order_by('min_score')
                    )
        # --- 3. DỰNG DỮ LIỆU JSON ĐỘC LẬP CHO BIỂU ĐỒ ---
        chart_abc_json = json.dumps({
            'labels': [f"{t.title} ({t.min_score}-{t.max_score}đ)" for t in all_thresholds_abc],
            'max_scores': [t.max_score for t in all_thresholds_abc],
            'user_score': score_abc
        }) if all_thresholds_abc else json.dumps({'labels': [], 'max_scores': [], 'user_score': score_abc})

        chart_d_json = json.dumps({
            'labels': [f"{t.title} ({t.min_score}-{t.max_score}đ)" for t in all_thresholds_d],
            'max_scores': [t.max_score for t in all_thresholds_d],
            'user_score': score_d
        }) if all_thresholds_d else json.dumps({'labels': [], 'max_scores': [], 'user_score': score_d})

        context = {
            'composite': composite,
            'submission': submission,
            'total_score': total_score,
            'score_abc': score_abc,
            'score_d': score_d,
            'threshold_abc': threshold_abc,
            'threshold_d': threshold_d,
            'chart_abc_json': chart_abc_json,
            'chart_d_json': chart_d_json,
        }
        return render(request, 'surveys/survey_result.html', context)

    return redirect('surveys:reconnect360_detail', slug=composite.slug)


@require_POST
def send_email_result(request):
    """View xử lý AJAX từ Email Modal"""
    email = request.POST.get('email', '').strip()
    submission_id = request.POST.get('submission_id')
    chart_base64 = request.POST.get('chart_base64', '').strip()

    if not email or not submission_id:
        return JsonResponse({'success': False, 'message': 'Vui lòng cung cấp đầy đủ thông tin!'}, status=400)

    try:
        submission = Submission.objects.get(pk=submission_id)

        # Cập nhật thêm email vào Lead nếu học sinh nhập email ở modal kết quả
        if submission.lead and not submission.lead.email:
            submission.lead.email = email
            submission.lead.save(update_fields=['email'])

        threshold = None
        survey_obj = getattr(submission, 'survey', None)
        if survey_obj:
            threshold = SurveyResultThreshold.objects.filter(
                survey=survey_obj,
                min_score__lte=submission.total_score,
                max_score__gte=submission.total_score
            ).first()

        send_pdf_email(email, submission, threshold, chart_base64=chart_base64)

        return JsonResponse({'success': True, 'message': 'Gửi báo cáo PDF thành công! Vui lòng kiểm tra hòm thư.'})

    except Submission.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy lượt nộp bài này!'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}, status=500)


def reconnect_report_view(request, slug="khao-sat-xu-huong-thu-minh-va-muc-do-ket-noi-xa-hoi-o-hoc-sinh-thcs-2"):
    """View hiển thị báo cáo thống kê khảo sát Reconnect 360°"""
    survey = _get_survey_by_slug(slug)
    
    time_filter = request.GET.get('time_filter', 'current_year')
    year_from = request.GET.get('year_from')
    year_to = request.GET.get('year_to')
    
    if hasattr(Submission, 'survey'):
        submissions = Submission.objects.filter(Q(survey=survey) | Q(composite_survey__items__survey=survey)).distinct()
    else:
        submissions = Submission.objects.filter(composite_survey__items__survey=survey).distinct()

    now = timezone.now()
    date_field = 'submitted_at'
    
    if time_filter == 'current_year':
        submissions = submissions.filter(**{f'{date_field}__year': now.year})
    elif time_filter == '3_months':
        three_months_ago = now - timedelta(days=90)
        submissions = submissions.filter(**{f'{date_field}__gte': three_months_ago})
    elif time_filter == '6_months':
        six_months_ago = now - timedelta(days=180)
        submissions = submissions.filter(**{f'{date_field}__gte': six_months_ago})
    elif time_filter == '1_year':
        one_year_ago = now - timedelta(days=365)
        submissions = submissions.filter(**{f'{date_field}__gte': one_year_ago})
    elif time_filter == 'last_year':
        submissions = submissions.filter(**{f'{date_field}__year': now.year - 1})
    elif time_filter == 'custom' and year_from and year_to:
        try:
            start_year = int(year_from)
            end_year = int(year_to)
            submissions = submissions.filter(**{
                f'{date_field}__year__gte': start_year,
                f'{date_field}__year__lte': end_year
            })
        except ValueError:
            pass

    total_participants = submissions.count()
    total_completed = total_participants
    completion_rate = round((total_completed / total_participants * 100), 1) if total_participants > 0 else 0
    
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
    
    for sub in submissions:
        score = sub.total_score
        for stat in threshold_stats:
            if stat['min_score'] <= score <= stat['max_score']:
                stat['count'] += 1
                break

    data = {
        'total_participants': total_participants,
        'total_completed': total_completed,
        'completion_rate': completion_rate,
        'threshold_stats': threshold_stats,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(data)

    context = {
        'survey': survey,
        **data
    }
    return render(request, 'surveys/reconnect_report.html', context)