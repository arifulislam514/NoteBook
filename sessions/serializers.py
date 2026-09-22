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


class TopicSessionResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    data = TopicSessionSerializer(allow_null=True)


class SessionStartRequestSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False, help_text="Optional client-generated session UUID")
    topic_type = serializers.ChoiceField(choices=['academic', 'skill'], help_text="Type of topic")
    topic_id = serializers.UUIDField(help_text="UUID of the academic or skill topic")
    mode = serializers.ChoiceField(choices=['stopwatch', 'timer'], default='stopwatch')
    timer_goal_seconds = serializers.IntegerField(required=False, allow_null=True, help_text="Required when mode is timer")
    started_at = serializers.DateTimeField(help_text="Session start timestamp in ISO 8601")


class SessionUpdateRequestSerializer(serializers.Serializer):
    duration_seconds = serializers.IntegerField(required=False, help_text="Accumulated duration in seconds")
    is_completed = serializers.BooleanField(required=False, help_text="Whether session is ended/completed")
    ended_at = serializers.DateTimeField(required=False, allow_null=True, help_text="End timestamp in ISO 8601")


class TopicTimeResponseDataSerializer(serializers.Serializer):
    topic_type = serializers.CharField()
    topic_id = serializers.UUIDField()
    total_seconds = serializers.IntegerField()


class TopicTimeResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    data = TopicTimeResponseDataSerializer()


class SubSkillTimeResponseDataSerializer(serializers.Serializer):
    sub_skill_id = serializers.UUIDField()
    total_seconds = serializers.IntegerField()


class SubSkillTimeResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    data = SubSkillTimeResponseDataSerializer()


class SkillTimeResponseDataSerializer(serializers.Serializer):
    skill_id = serializers.UUIDField()
    total_seconds = serializers.IntegerField()


class SkillTimeResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    data = SkillTimeResponseDataSerializer()


class DailyBreakdownItemSerializer(serializers.Serializer):
    date = serializers.DateField()
    academic_seconds = serializers.IntegerField()
    skill_seconds = serializers.IntegerField()


class TopTopicItemSerializer(serializers.Serializer):
    topic_id = serializers.UUIDField()
    title = serializers.CharField()
    total_seconds = serializers.IntegerField()


class OverviewAnalyticsDataSerializer(serializers.Serializer):
    period = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    academic_seconds = serializers.IntegerField()
    skill_seconds = serializers.IntegerField()
    total_seconds = serializers.IntegerField()
    daily_breakdown = DailyBreakdownItemSerializer(many=True)
    top_academic_topics = TopTopicItemSerializer(many=True)
    top_skill_topics = TopTopicItemSerializer(many=True)


class OverviewAnalyticsResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    data = OverviewAnalyticsDataSerializer()
