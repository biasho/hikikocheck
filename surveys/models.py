# surveys/models.py
from django.db import models
from django.contrib.auth.models import User
from questions.models import Question, Option, Category  # Import từ app questions

# 1. Bộ khảo sát
class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    questions = models.ManyToManyField(Question, related_name='surveys')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# 2. Ngưỡng điểm & Kết luận
class SurveyResultThreshold(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='thresholds')
    min_score = models.IntegerField()
    max_score = models.IntegerField()
    title = models.CharField(max_length=255) # Mức độ
    description = models.TextField()         # Nhận xét chi tiết
    recommendation = models.TextField(blank=True, null=True) # Lời khuyên

    class Meta:
        ordering = ['min_score']

    def __str__(self):
        return f"{self.survey.title}: {self.min_score} - {self.max_score}đ ({self.title})"

# 3. Lượt nộp bài
class Submission(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    total_score = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lượt nộp #{self.id} - {self.survey.title} ({self.total_score}đ)"

# 4. Chi tiết từng câu trả lời
class Answer(models.Model):
    submission = models.ForeignKey(Submission, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)