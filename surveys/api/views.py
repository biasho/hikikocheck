# surveys/api/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from surveys.models import CompositeSurvey, Submission, Answer, Option, Question
from surveys.serializers import (
    CompositeSurveyDetailSerializer, 
    CompositeSurveyListSerializer
)

@api_view(['GET'])
def composite_survey_list_api_view(request):
    """API trả về danh sách các Bộ khảo sát cho ứng dụng Flutter hiển thị ở màn hình chính"""
    surveys = CompositeSurvey.objects.filter(is_active=True).order_by('-created_at')
    serializer = CompositeSurveyListSerializer(surveys, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def composite_survey_api_view(request, pk):
    """API trả về cấu trúc chi tiết Bộ khảo sát tổng hợp kèm câu hỏi và đáp án"""
    try:
        composite_survey = CompositeSurvey.objects.prefetch_related(
            'items__survey__questions__options',
            'items__survey__questions__group'
        ).get(pk=pk, is_active=True)
        
        serializer = CompositeSurveyDetailSerializer(composite_survey)
        return Response(serializer.data)
    except CompositeSurvey.DoesNotExist:
        return Response({'error': 'Bộ khảo sát không tồn tại hoặc đã bị khóa'}, status=404)


@api_view(['POST'])
def submit_survey_api_view(request):
    """API nhận kết quả làm bài khảo sát từ Flutter gửi lên và tiến hành chấm điểm"""
    data = request.data
    
    composite_survey_id = data.get('composite_survey_id')
    email = data.get('email')
    answers_data = data.get('answers', []) # Danh sách câu trả lời [{question_id: 1, option_id: 2}, ...]
    
    # 1. Kiểm tra bộ khảo sát tồn tại
    try:
        composite_survey = CompositeSurvey.objects.get(pk=composite_survey_id, is_active=True)
    except CompositeSurvey.DoesNotExist:
        return Response({'error': 'Bộ khảo sát không tồn tại'}, status=404)
        
    # 2. Khởi tạo điểm số ban đầu
    score_a = 0
    score_b = 0
    score_c = 0
    score_d = 0
    total_score = 0
    
    # 3. Tạo một Submission mới
    submission = Submission.objects.create(
        composite_survey=composite_survey,
        email=email,
        # Nếu user đã đăng nhập qua token/session, có thể gán thêm user=request.user ở đây
    )
    
    # 4. Duyệt qua từng câu trả lời để tính điểm và lưu vết
    for item in answers_data:
        q_id = item.get('question_id')
        opt_id = item.get('option_id')
        
        try:
            question = Question.objects.get(pk=q_id)
            option = Option.objects.get(pk=opt_id, question=question)
            
            # Lưu chi tiết câu trả lời
            Answer.objects.create(
                submission=submission,
                question=question,
                selected_option=option
            )
            
            # Cộng điểm dựa vào group của câu hỏi hoặc điểm của option
            points = option.score
            total_score += points
            
            if question.group:
                group_code = question.group.code.upper()
                if group_code == 'A': score_a += points
                elif group_code == 'B': score_b += points
                elif group_code == 'C': score_c += points
                elif group_code == 'D': score_d += points
                
        except (Question.DoesNotExist, Option.DoesNotExist):
            continue
            
    # 5. Cập nhật lại tổng điểm vào Submission
    submission.score_a = score_a
    submission.score_b = score_b
    submission.score_c = score_c
    submission.score_d = score_d
    submission.total_score = total_score
    submission.save()
    
    return Response({
        'message': 'Nộp bài thành công!',
        'submission_id': submission.id,
        'total_score': total_score,
        'scores': {
            'A': score_a,
            'B': score_b,
            'C': score_c,
            'D': score_d,
        }
    }, status=201)