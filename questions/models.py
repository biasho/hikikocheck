# questions/models.py
from django.db import models

# 1. Danh mục / Chủ đề
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# 2. Ngân hàng câu hỏi
class Question(models.Model):
    QUESTION_TYPES = [
        ('single_choice', 'Trắc nghiệm chọn 1'),
        ('multiple_choice', 'Trắc nghiệm chọn nhiều'),
        ('text', 'Tự luận'),
        ('rating', 'Thang đo Likert'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single_choice')
    explanation = models.TextField(blank=True, null=True) # Lời giải (cho đề thi sau này)
    def __str__(self):
        cat_name = self.category.name if self.category else "Chưa phân loại"
        return f"[{cat_name}] {self.text[:40]}"

# 3. Các lựa chọn / Đáp án
class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    score = models.IntegerField(default=0)         # Thang điểm (cho khảo sát đánh giá)
    is_correct = models.BooleanField(default=False) # Đáp án đúng (cho đề thi sau này)

    def __str__(self):
        return f"{self.text} ({self.score}đ)"