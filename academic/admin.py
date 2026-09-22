from django.contrib import admin
from .models import (
    Semester,
    Subject,
    AcademicWantToLearn,
    Chapter,
    AcademicTopic,
    AcademicTopicBlock,
)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'year', 'user', 'is_deleted', 'created_at')
    list_filter = ('year', 'is_deleted')
    search_fields = ('name',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'semester', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('name',)


@admin.register(AcademicWantToLearn)
class AcademicWantToLearnAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'subject', 'is_done', 'is_deleted', 'created_at')
    list_filter = ('is_done', 'is_deleted')
    search_fields = ('title',)


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'subject', 'order', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('name',)


@admin.register(AcademicTopic)
class AcademicTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'chapter', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('title',)


@admin.register(AcademicTopicBlock)
class AcademicTopicBlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic', 'type', 'order', 'is_deleted', 'created_at')
    list_filter = ('type', 'is_deleted')
