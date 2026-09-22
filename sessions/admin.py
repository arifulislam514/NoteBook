from django.contrib import admin
from .models import TopicSession


@admin.register(TopicSession)
class TopicSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'mode', 'duration_seconds', 'is_completed', 'started_at', 'ended_at')
    list_filter = ('mode', 'is_completed')
    search_fields = ('user__email', 'academic_topic__title', 'skill_topic__title')
