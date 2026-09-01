# serializers.py (trong app quản lý khảo sát của bạn)
from rest_framework import serializers
from .models import Survey, CompositeSurvey, CompositeSurveyItem, Question, Option, Category

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'score']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)
    group_code = serializers.CharField(source='group.code', read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'group_code', 'options']

class SurveySerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Survey
        fields = ['id', 'title', 'slug', 'description', 'category_name', 'questions']

# 🎯 Serializer rút gọn dùng cho màn hình danh sách (Danh sách các bộ khảo sát)
class CompositeSurveyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositeSurvey
        fields = ['id', 'title', 'slug', 'description', 'created_at']

# Serializer dùng cho cấu trúc phần tử trong Bộ khảo sát tổng hợp
class CompositeSurveyItemSerializer(serializers.ModelSerializer):
    survey = SurveySerializer(read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = CompositeSurveyItem
        fields = ['order', 'name', 'display_name', 'survey']

    def get_display_name(self, obj):
        return obj.name if obj.name else obj.survey.title

# Serializer chi tiết dùng cho cấu trúc Bộ khảo sát tổng hợp
class CompositeSurveyDetailSerializer(serializers.ModelSerializer):
    items = CompositeSurveyItemSerializer(many=True, read_only=True)

    class Meta:
        model = CompositeSurvey  # Đã sửa lại đúng model chính xác
        fields = ['id', 'title', 'slug', 'description', 'items']