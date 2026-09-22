from django.contrib import admin
from .models import (
    Skill,
    SubSkill,
    SkillWantToLearn,
    SkillTopic,
    EvaluationQuestion,
    EvaluationAnswer,
    EvaluationAnswerBlock,
)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('name',)


@admin.register(SubSkill)
class SubSkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'skill', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('name',)


@admin.register(SkillWantToLearn)
class SkillWantToLearnAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'sub_skill', 'is_done', 'is_deleted', 'created_at')
    list_filter = ('is_done', 'is_deleted')
    search_fields = ('title',)


@admin.register(SkillTopic)
class SkillTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'sub_skill', 'current_level', 'is_deleted', 'created_at')
    list_filter = ('current_level', 'is_deleted')
    search_fields = ('title',)


@admin.register(EvaluationQuestion)
class EvaluationQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'level', 'order', 'is_default', 'is_deleted', 'created_at')
    list_filter = ('level', 'is_default', 'is_deleted')
    search_fields = ('text',)


@admin.register(EvaluationAnswer)
class EvaluationAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'skill_topic', 'level', 'question', 'is_deleted', 'created_at')
    list_filter = ('level', 'is_deleted')


@admin.register(EvaluationAnswerBlock)
class EvaluationAnswerBlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'answer', 'type', 'order', 'is_deleted', 'created_at')
    list_filter = ('type', 'is_deleted')
