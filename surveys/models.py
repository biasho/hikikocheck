from django.db import models
from django.contrib.auth.models import User
from slugify import slugify  # Sử dụng python-slugify hỗ trợ Tiếng Việt
from questions.models import Question, Option, Category  # Import từ app questions
from core.models import Group  # Import model Group từ app core


# 1. Khảo sát đơn / Phần khảo sát
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


# 2. Bộ khảo sát lớn / Bài thi (Gom N phần khảo sát lẻ theo thứ tự)
class CompositeSurvey(models.Model):
    title = models.CharField(max_length=255, verbose_name="Tên bộ khảo sát")
    slug = models.SlugField(max_length=255, blank=True, null=True, unique=True)
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả bộ khảo sát")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)
    surveys = models.ManyToManyField(
        Survey, 
        through='CompositeSurveyItem', 
        related_name='composite_surveys',
        verbose_name="Các phần khảo sát thành phần"
    )

    class Meta:
        verbose_name = "Bộ khảo sát tổng hợp"
        verbose_name_plural = "Các bộ khảo sát tổng hợp"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        base_slug = slugify(self.title) if self.title else 'composite-survey'
        expected_slug = f"{base_slug}-{self.pk}"

        if is_new or self.slug != expected_slug:
            self.slug = expected_slug
            super().save(update_fields=['slug'])

    def __str__(self):
        return self.title


# 3. Bảng trung gian định vị thứ tự từng phần trong Bộ khảo sát (Linh hoạt N phần)
class CompositeSurveyItem(models.Model):
    composite_survey = models.ForeignKey(
        CompositeSurvey, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    survey = models.ForeignKey(
        Survey, 
        on_delete=models.CASCADE,
        verbose_name="Phần khảo sát"
    )
    name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Tên phần hiển thị",
        help_text="VD: Phần I, Phần II, Chương 1... (Nếu để trống sẽ dùng tên mặc định của bài khảo sát)"
    )
    order = models.PositiveIntegerField(default=1, verbose_name="Thứ tự hiển thị (Phần thứ N)")

    class Meta:
        ordering = ['order']
        unique_together = ['composite_survey', 'order']
        verbose_name = "Cấu trúc phần khảo sát"
        verbose_name_plural = "Cấu trúc các phần khảo sát"

    def __str__(self):
        display_name = self.name if self.name else self.survey.title
        return f"{display_name} (Thứ tự: {self.order})"


# 4. Ngưỡng điểm & Kết luận (Dùng trực tiếp trường group để phân loại)
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
    title = models.CharField(max_length=255, verbose_name="Mức độ")
    description = models.TextField(verbose_name="Nhận xét chi tiết")
    recommendation = models.TextField(blank=True, null=True, verbose_name="Lời khuyên")

    class Meta:
        ordering = ['min_score']

    def __str__(self):
        group_name = self.group.name if self.group else "Tổng hợp chung"
        return f"{self.survey.title} [{group_name}]: {self.min_score} - {self.max_score}đ ({self.title})"


# 5. Lượt nộp bài (Liên kết với CompositeSurvey và Lead để gom nhóm lịch sử làm bài)
class Submission(models.Model):
    composite_survey = models.ForeignKey(
        CompositeSurvey, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='submissions',
        verbose_name="Thuộc bộ khảo sát"
    )
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    # 🔗 Liên kết khóa ngoại với Lead (Quản lý hồ sơ người tham gia ẩn danh hoặc có tài khoản)
    lead = models.ForeignKey(
        'core.Lead', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='submissions',
        verbose_name="Người tham gia (Lead)"
    )
    
    session_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    email = models.EmailField(blank=True, null=True, help_text="Email của người làm khảo sát (tùy chọn)")
    
    # Lưu điểm chi tiết theo từng nhóm (A, B, C, D...)
    score_a = models.IntegerField(default=0)
    score_b = models.IntegerField(default=0)
    score_c = models.IntegerField(default=0)
    score_d = models.IntegerField(default=0)
    
    # Lưu điểm tổng hợp
    score_difficulties = models.IntegerField(default=0)
    
    total_score = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target_title = self.composite_survey.title if self.composite_survey else (self.survey.title if self.survey else "Khảo sát")
        participant_name = self.lead.full_name if (self.lead and self.lead.full_name) else (self.email or "Ẩn danh")
        return f"Lượt nộp #{self.id} - {participant_name} - {target_title} (Tổng: {self.total_score}đ)"

    
# 6. Chi tiết từng câu trả lời
class Answer(models.Model):
    submission = models.ForeignKey(Submission, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)

class SurveySubmission(models.Model):
    """Lưu vết điểm số chi tiết cho từng Survey con trong một lượt làm bài CompositeSurvey."""
    submission = models.ForeignKey(
        Submission, 
        on_delete=models.CASCADE, 
        related_name='survey_results',
        verbose_name="Lượt làm bài"
    )
    survey = models.ForeignKey(
        Survey, 
        on_delete=models.CASCADE, 
        verbose_name="Khảo sát con"
    )
    score = models.IntegerField(default=0, verbose_name="Điểm đạt được")

    class Meta:
        unique_together = ('submission', 'survey')
        verbose_name = "Kết quả khảo sát con"
        verbose_name_plural = "Kết quả các khảo sát con"

    def __str__(self):
        return f"Submission #{self.submission_id} - {self.survey.title}: {self.score}đ"