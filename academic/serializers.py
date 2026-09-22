import uuid
from rest_framework import serializers
from .models import (
    Semester,
    Subject,
    AcademicWantToLearn,
    Chapter,
    AcademicTopic,
    AcademicTopicBlock,
)


class SemesterSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)

    class Meta:
        model = Semester
        fields = ['id', 'name', 'year', 'updated_at']
        read_only_fields = ['updated_at']


class SubjectSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    semester_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'semester_id', 'name', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['semester_id'] = str(instance.semester_id)
        return ret

    def create(self, validated_data):
        semester_id = validated_data.pop('semester_id')
        return Subject.objects.create(semester_id=semester_id, **validated_data)


class AcademicWantToLearnSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    subject_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = AcademicWantToLearn
        fields = ['id', 'subject_id', 'title', 'is_done', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['subject_id'] = str(instance.subject_id)
        return ret

    def create(self, validated_data):
        subject_id = validated_data.pop('subject_id')
        return AcademicWantToLearn.objects.create(subject_id=subject_id, **validated_data)


class ChapterSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    subject_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'subject_id', 'name', 'order', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['subject_id'] = str(instance.subject_id)
        return ret

    def create(self, validated_data):
        subject_id = validated_data.pop('subject_id')
        return Chapter.objects.create(subject_id=subject_id, **validated_data)


class AcademicTopicSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    chapter_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = AcademicTopic
        fields = ['id', 'chapter_id', 'title', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['chapter_id'] = str(instance.chapter_id)
        return ret

    def create(self, validated_data):
        chapter_id = validated_data.pop('chapter_id')
        return AcademicTopic.objects.create(chapter_id=chapter_id, **validated_data)


class AcademicTopicBlockSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    topic_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = AcademicTopicBlock
        fields = ['id', 'topic_id', 'type', 'content', 'order', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['topic_id'] = str(instance.topic_id)
        return ret

    def create(self, validated_data):
        topic_id = validated_data.pop('topic_id')
        return AcademicTopicBlock.objects.create(topic_id=topic_id, **validated_data)


class BlockOrderItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="Block UUID")
    order = serializers.IntegerField(help_text="New display order")


class AcademicTopicBlockReorderRequestSerializer(serializers.Serializer):
    blocks = BlockOrderItemSerializer(many=True, help_text="List of blocks with updated order values")
