from django.db import models
from django.contrib.auth.models import User
from slugify import slugify  # Sử dụng python-slugify hỗ trợ Tiếng Việt
from questions.models import Question, Option, Category  # Import từ app questions
from core.models import Group  # Import model Group từ app core

# 1. Bộ khảo sát
class Survey(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, null=True) 
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    questions = models.ManyToManyField(Question, related_name='surveys')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        base_slug = slugify(self.title) if self.title else 'survey'
        expected_slug = f"{base_slug}-{self.pk}"

        if is_new or self.slug != expected_slug:
            self.slug = expected_slug
            super().save(update_fields=['slug'])

    def __str__(self):
        return self.title

# 2. Ngưỡng điểm & Kết luận (🎯 Dùng trực tiếp trường group để phân loại nhóm lẻ hoặc nhóm tổng hợp)
class SurveyResultThreshold(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='thresholds')
    group = models.ForeignKey(
        Group, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Áp dụng cho nhóm (Chọn nhóm A, B, C, D hoặc nhóm tổng hợp ALL_ABC, ALL_D)"
    )
    min_score = models.IntegerField()
    max_score = models.IntegerField()
    title = models.CharField(max_length=255, verbose_name="Mức độ") # Mức độ
    description = models.TextField(verbose_name="Nhận xét chi tiết")         # Nhận xét chi tiết
    recommendation = models.TextField(blank=True, null=True, verbose_name="Lời khuyên") # Lời khuyên

    class Meta:
        ordering = ['min_score']

    def __str__(self):
        group_name = self.group.name if self.group else "Tổng hợp chung"
        return f"{self.survey.title} [{group_name}]: {self.min_score} - {self.max_score}đ ({self.title})"

# 3. Lượt nộp bài (Lưu điểm chi tiết từng nhóm và điểm tổng hợp)
class Submission(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    email = models.EmailField(blank=True, null=True, help_text="Email của người làm khảo sát")
    
    # Lưu điểm chi tiết theo từng nhóm (A, B, C, D...)
    score_a = models.IntegerField(default=0)
    score_b = models.IntegerField(default=0)
    score_c = models.IntegerField(default=0)
    score_d = models.IntegerField(default=0)
    
    # Lưu điểm tổng hợp (Ví dụ: Chỉ số khó khăn = A + B + C)
    score_difficulties = models.IntegerField(default=0)
    
    total_score = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lượt nộp #{self.id} - {self.survey.title} (Tổng: {self.total_score}đ)"

# 4. Chi tiết từng câu trả lời
class Answer(models.Model):
    submission = models.ForeignKey(Submission, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)