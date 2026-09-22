from rest_framework import serializers


class SyncPushChangesSerializer(serializers.Serializer):
    semesters = serializers.ListField(child=serializers.DictField(), required=False)
    subjects = serializers.ListField(child=serializers.DictField(), required=False)
    academic_want_to_learn = serializers.ListField(child=serializers.DictField(), required=False)
    chapters = serializers.ListField(child=serializers.DictField(), required=False)
    academic_topics = serializers.ListField(child=serializers.DictField(), required=False)
    academic_topic_blocks = serializers.ListField(child=serializers.DictField(), required=False)
    skills = serializers.ListField(child=serializers.DictField(), required=False)
    sub_skills = serializers.ListField(child=serializers.DictField(), required=False)
    skill_want_to_learn = serializers.ListField(child=serializers.DictField(), required=False)
    skill_topics = serializers.ListField(child=serializers.DictField(), required=False)
    evaluation_questions = serializers.ListField(child=serializers.DictField(), required=False)
    evaluation_answers = serializers.ListField(child=serializers.DictField(), required=False)
    evaluation_answer_blocks = serializers.ListField(child=serializers.DictField(), required=False)
    topic_sessions = serializers.ListField(child=serializers.DictField(), required=False)


class SyncPushRequestSerializer(serializers.Serializer):
    last_sync = serializers.DateTimeField(required=False, allow_null=True, help_text="ISO 8601 timestamp of last successful sync")
    changes = SyncPushChangesSerializer(required=False, help_text="Dictionary of model changes keyed by model name")


class SyncPushResponseDataSerializer(serializers.Serializer):
    server_changes = serializers.DictField(help_text="Dictionary of records updated on server since last_sync")
    sync_time = serializers.CharField(help_text="Current server UTC timestamp in ISO 8601 format")


class SyncPushResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    data = SyncPushResponseDataSerializer()
