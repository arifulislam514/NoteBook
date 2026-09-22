import uuid
from rest_framework import serializers
from .models import (
    Skill,
    SubSkill,
    SkillWantToLearn,
    SkillTopic,
    EvaluationQuestion,
    EvaluationAnswer,
    EvaluationAnswerBlock,
)


class EvaluationQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationQuestion
        fields = ['id', 'level', 'text', 'order', 'is_default', 'updated_at']
        read_only_fields = ['id', 'is_default', 'updated_at']


class SkillSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)

    class Meta:
        model = Skill
        fields = ['id', 'name', 'updated_at']
        read_only_fields = ['updated_at']


class SubSkillSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    skill_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = SubSkill
        fields = ['id', 'skill_id', 'name', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['skill_id'] = str(instance.skill_id)
        return ret

    def create(self, validated_data):
        skill_id = validated_data.pop('skill_id')
        return SubSkill.objects.create(skill_id=skill_id, **validated_data)


class SkillWantToLearnSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    sub_skill_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = SkillWantToLearn
        fields = ['id', 'sub_skill_id', 'title', 'is_done', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['sub_skill_id'] = str(instance.sub_skill_id)
        return ret

    def create(self, validated_data):
        sub_skill_id = validated_data.pop('sub_skill_id')
        return SkillWantToLearn.objects.create(sub_skill_id=sub_skill_id, **validated_data)


class SkillTopicSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    sub_skill_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = SkillTopic
        fields = ['id', 'sub_skill_id', 'title', 'current_level', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['sub_skill_id'] = str(instance.sub_skill_id)
        return ret

    def create(self, validated_data):
        sub_skill_id = validated_data.pop('sub_skill_id')
        return SkillTopic.objects.create(sub_skill_id=sub_skill_id, **validated_data)


class EvaluationAnswerBlockSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    answer_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = EvaluationAnswerBlock
        fields = ['id', 'answer_id', 'type', 'content', 'order', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'answer_id') and instance.answer_id:
            ret['answer_id'] = str(instance.answer_id)
        return ret

    def create(self, validated_data):
        answer_id = validated_data.pop('answer_id')
        return EvaluationAnswerBlock.objects.create(answer_id=answer_id, **validated_data)


class EvaluationAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationAnswer
        # question_id replaces question_index
        # level is kept (denormalized from question.level)
        fields = ['id', 'skill_topic_id', 'level', 'question_id', 'updated_at']
        read_only_fields = ['id', 'level', 'updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'skill_topic_id') and instance.skill_topic_id:
            ret['skill_topic_id'] = str(instance.skill_topic_id)
        if hasattr(instance, 'question_id') and instance.question_id:
            ret['question_id'] = str(instance.question_id)
        return ret


class EvaluationAnswerDetailSerializer(serializers.ModelSerializer):
    blocks = EvaluationAnswerBlockSerializer(many=True, read_only=True)
    question_text = serializers.CharField(source='question.text', read_only=True)

    class Meta:
        model = EvaluationAnswer
        fields = ['id', 'skill_topic_id', 'level', 'question_id',
                  'question_text', 'blocks', 'updated_at']
        read_only_fields = ['id', 'level', 'question_text', 'updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'skill_topic_id') and instance.skill_topic_id:
            ret['skill_topic_id'] = str(instance.skill_topic_id)
        if hasattr(instance, 'question_id') and instance.question_id:
            ret['question_id'] = str(instance.question_id)
        return ret


