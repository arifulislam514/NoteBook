from rest_framework import serializers
from .models import TopicSession


class TopicSessionSerializer(serializers.ModelSerializer):
    # Include topic names for the active session indicator on mobile
    academic_topic_title = serializers.CharField(
        source='academic_topic.title', read_only=True, default=None
    )
    skill_topic_title = serializers.CharField(
        source='skill_topic.title', read_only=True, default=None
    )

    class Meta:
        model = TopicSession
        fields = [
            'id', 'mode', 'timer_goal_seconds',
            'academic_topic_id', 'academic_topic_title',
            'skill_topic_id', 'skill_topic_title',
            'started_at', 'ended_at',
            'duration_seconds', 'is_completed',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'academic_topic_id') and instance.academic_topic_id:
            ret['academic_topic_id'] = str(instance.academic_topic_id)
        if hasattr(instance, 'skill_topic_id') and instance.skill_topic_id:
            ret['skill_topic_id'] = str(instance.skill_topic_id)
        return ret
