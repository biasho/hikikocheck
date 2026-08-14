from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction  # Import transaction để dùng atomic

from .models import Survey, Submission, Answer, SurveyResultThreshold
from questions.models import Question, Option  # Import Question, Option


def survey_list(request):
    """Hiển thị danh sách các bài khảo sát đang hoạt động"""
    surveys = Survey.objects.filter(is_active=True)
    return render(request, 'surveys/survey_list.html', {'surveys': surveys})


def survey_detail(request, survey_id):
    """Hiển thị trang chi tiết bài khảo sát (Giao diện làm bài)"""
    survey = get_object_or_404(Survey, id=survey_id, is_active=True)
    
    # Lấy toàn bộ câu hỏi và các option liên quan
    questions = survey.questions.prefetch_related('options').all()

    context = {
        'survey': survey,
        'questions': questions,
    }
    return render(request, 'surveys/survey_detail.html', context)


def submit_survey(request, survey_id):
    """Xử lý nộp bài khảo sát, tính điểm và trả về trang kết quả"""
    survey = get_object_or_404(Survey, pk=survey_id, is_active=True)

    if request.method == 'POST':
        user = request.user if request.user.is_authenticated else None
        
        # Đảm bảo khởi tạo session key cho khách vãng lai nếu chưa có
        if not user and not request.session.session_key:
            request.session.create()

        total_score = 0
        answers_to_create = []

        # Tối ưu hóa lưu Database bằng atomic transaction
        with transaction.atomic():
            # 1. Tạo Lượt nộp bài (Submission)
            submission = Submission.objects.create(
                survey=survey,
                user=user,
                total_score=0
            )

            # 2. Lặp qua toàn bộ dữ liệu gửi lên từ Form
            for key, value in request.POST.items():
                if key.startswith('question_'):
                    question_id = key.split('_')[1]
                    question = Question.objects.filter(id=question_id, surveys=survey).first()

                    if not question:
                        continue

                    # Trường hợp Trắc nghiệm / Rating
                    if question.question_type in ['single_choice', 'rating']:
                        selected_option = Option.objects.filter(id=value, question=question).first()
                        if selected_option:
                            # Cộng điểm của Option vào Tổng điểm (mặc định 0 nếu option không có điểm)
                            option_score = getattr(selected_option, 'score', getattr(selected_option, 'point', 0))
                            total_score += option_score

                            answers_to_create.append(
                                Answer(
                                    submission=submission,
                                    question=question,
                                    selected_option=selected_option
                                )
                            )

                    # Trường hợp Tự luận
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

            # Bulk create các Answer để tiết kiệm truy vấn SQL
            Answer.objects.bulk_create(answers_to_create)

            # Cập nhật lại tổng điểm
            submission.total_score = total_score
            submission.save()

        # 3. Tìm Ngưỡng điểm phù hợp trong SurveyResultThreshold
        matched_threshold = SurveyResultThreshold.objects.filter(
            survey=survey,
            min_score__lte=total_score,
            max_score__gte=total_score
        ).first()

        # 4. Trả về trang kết quả
        context = {
            'survey': survey,
            'submission': submission,
            'total_score': total_score,
            'threshold': matched_threshold,
            'total_questions': survey.questions.count(),
        }
        return render(request, 'surveys/survey_result.html', context)

    # Nếu không phải POST request thì đẩy về lại trang chi tiết khảo sát
    return redirect('surveys:survey_detail', survey_id=survey_id)