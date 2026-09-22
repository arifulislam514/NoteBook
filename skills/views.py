import uuid
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from common.response import success_response, error_response
from .models import (
    Skill,
    SubSkill,
    SkillWantToLearn,
    SkillTopic,
    EvaluationQuestion,
    EvaluationAnswer,
    EvaluationAnswerBlock,
)
from .serializers import (
    SkillSerializer,
    SubSkillSerializer,
    SkillWantToLearnSerializer,
    SkillTopicSerializer,
    EvaluationQuestionSerializer,
    EvaluationAnswerSerializer,
    EvaluationAnswerDetailSerializer,
    EvaluationAnswerBlockSerializer,
)

DEFAULT_QUESTIONS = {
    'basic': [
        'এই topic টা এক বাক্যে কী? নিজের ভাষায় বলো।',
        'এটা কেন দরকার? কোন সমস্যা solve করে?',
        'এর প্রধান ৩–৫টা উপাদান বা ধারণা কী কী?',
        'একটা real-life উদাহরণ দাও।',
        'এই topic না থাকলে কী হতো?',
    ],
    'intermediate': [
        'এটা কখন ব্যবহার করবো, কখন করবো না?',
        'Step-by-step কীভাবে apply করা হয়?',
        'নিজে একটা ছোট example তৈরি করতে পারবে?',
        'সবচেয়ে common ভুল কী? কীভাবে এড়ানো যায়?',
        'একজন বন্ধুকে ৫ মিনিটে বোঝাতে পারবে?',
    ],
    'advanced': [
        'এর সবচেয়ে বড় limitation বা দুর্বলতা কী?',
        'কোন situation এ এটা কাজ করবে না?',
        'এর alternatives কী? কোনটা কখন ভালো?',
        'এর পেছনে মূল mechanism বা কারণ কী?',
        'এটাকে আরো efficient বা ভালো করা যায় কীভাবে?',
    ],
    'expert': [
        'এই topic নিয়ে এমন কিছু জানো যা বেশিরভাগ মানুষ জানে না?',
        'এটাকে অন্য একটা বিষয়ের সাথে combine করে সমস্যা solve করতে পারো?',
        'এই topic এ সবচেয়ে বড় debate বা unsolved question কী?',
        'এই topic নিয়ে তোমার নিজের unique insight আছে?',
        'এই topic এ একটা complete guide লিখতে পারবে?',
    ],
}


def seed_default_questions(user, level):
    """
    Create the 5 default questions for a user+level if none exist yet.
    Called lazily on first GET /api/skills/questions/?level={level}.
    """
    if EvaluationQuestion.objects.filter(
        user=user, level=level, is_deleted=False
    ).exists():
        return  # already seeded

    questions_to_create = [
        EvaluationQuestion(
            user=user,
            level=level,
            text=text,
            order=idx,
            is_default=True,
        )
        for idx, text in enumerate(DEFAULT_QUESTIONS.get(level, []))
    ]
    EvaluationQuestion.objects.bulk_create(questions_to_create)



class SkillListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        skills = Skill.objects.filter(user=request.user, is_deleted=False)
        serializer = SkillSerializer(skills, many=True)
        return success_response(serializer.data, status=200)

    def post(self, request):
        serializer = SkillSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        skill = serializer.save(user=request.user)
        return success_response(SkillSerializer(skill).data, status=201)


class SkillDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        skill = get_object_or_404(Skill, id=pk, user=request.user, is_deleted=False)
        serializer = SkillSerializer(skill, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        skill = serializer.save()
        return success_response(SkillSerializer(skill).data, status=200)

    def delete(self, request, pk):
        skill = get_object_or_404(Skill, id=pk, user=request.user, is_deleted=False)
        skill.is_deleted = True
        skill.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class SubSkillListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        skill_id = request.query_params.get('skill_id')
        queryset = SubSkill.objects.filter(skill__user=request.user, is_deleted=False)
        if skill_id:
            get_object_or_404(Skill, id=skill_id, user=request.user, is_deleted=False)
            queryset = queryset.filter(skill_id=skill_id)
        serializer = SubSkillSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    def post(self, request):
        skill_id = request.data.get('skill_id')
        if not skill_id:
            return error_response("skill_id is required", status=400)
        get_object_or_404(Skill, id=skill_id, user=request.user, is_deleted=False)

        serializer = SubSkillSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        sub_skill = serializer.save()
        return success_response(SubSkillSerializer(sub_skill).data, status=201)


class SubSkillDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        sub_skill = get_object_or_404(SubSkill, id=pk, skill__user=request.user, is_deleted=False)
        serializer = SubSkillSerializer(sub_skill, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        sub_skill = serializer.save()
        return success_response(SubSkillSerializer(sub_skill).data, status=200)

    def delete(self, request, pk):
        sub_skill = get_object_or_404(SubSkill, id=pk, skill__user=request.user, is_deleted=False)
        sub_skill.is_deleted = True
        sub_skill.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class SkillWantToLearnListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub_skill_id = request.query_params.get('sub_skill_id')
        queryset = SkillWantToLearn.objects.filter(sub_skill__skill__user=request.user, is_deleted=False)
        if sub_skill_id:
            get_object_or_404(SubSkill, id=sub_skill_id, skill__user=request.user, is_deleted=False)
            queryset = queryset.filter(sub_skill_id=sub_skill_id)
        serializer = SkillWantToLearnSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    def post(self, request):
        sub_skill_id = request.data.get('sub_skill_id')
        if not sub_skill_id:
            return error_response("sub_skill_id is required", status=400)
        get_object_or_404(SubSkill, id=sub_skill_id, skill__user=request.user, is_deleted=False)

        serializer = SkillWantToLearnSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        item = serializer.save()
        return success_response(SkillWantToLearnSerializer(item).data, status=201)


class SkillWantToLearnDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        item = get_object_or_404(SkillWantToLearn, id=pk, sub_skill__skill__user=request.user, is_deleted=False)
        serializer = SkillWantToLearnSerializer(item, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        item = serializer.save()
        return success_response(SkillWantToLearnSerializer(item).data, status=200)

    def delete(self, request, pk):
        item = get_object_or_404(SkillWantToLearn, id=pk, sub_skill__skill__user=request.user, is_deleted=False)
        item.is_deleted = True
        item.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class SkillTopicListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub_skill_id = request.query_params.get('sub_skill_id')
        queryset = SkillTopic.objects.filter(sub_skill__skill__user=request.user, is_deleted=False)
        if sub_skill_id:
            get_object_or_404(SubSkill, id=sub_skill_id, skill__user=request.user, is_deleted=False)
            queryset = queryset.filter(sub_skill_id=sub_skill_id)
        serializer = SkillTopicSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    def post(self, request):
        sub_skill_id = request.data.get('sub_skill_id')
        if not sub_skill_id:
            return error_response("sub_skill_id is required", status=400)
        get_object_or_404(SubSkill, id=sub_skill_id, skill__user=request.user, is_deleted=False)

        serializer = SkillTopicSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        topic = serializer.save()
        return success_response(SkillTopicSerializer(topic).data, status=201)


class SkillTopicDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        topic = get_object_or_404(SkillTopic, id=pk, sub_skill__skill__user=request.user, is_deleted=False)
        serializer = SkillTopicSerializer(topic, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        topic = serializer.save()
        return success_response(SkillTopicSerializer(topic).data, status=200)

    def delete(self, request, pk):
        topic = get_object_or_404(SkillTopic, id=pk, sub_skill__skill__user=request.user, is_deleted=False)
        topic.is_deleted = True
        topic.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class EvaluationQuestionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        level = request.query_params.get('level')
        if not level:
            return error_response("level query param is required", status=400)
        if level not in ['basic', 'intermediate', 'advanced', 'expert']:
            return error_response("Invalid level. Must be one of: basic, intermediate, advanced, expert", status=400)

        # Auto-seed defaults if user has no questions for this level yet
        seed_default_questions(request.user, level)

        questions = EvaluationQuestion.objects.filter(
            user=request.user,
            level=level,
            is_deleted=False
        )
        serializer = EvaluationQuestionSerializer(questions, many=True)
        return success_response(serializer.data, status=200)

    def post(self, request):
        serializer = EvaluationQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        rec_id = request.data.get('id')
        save_kwargs = {'user': request.user, 'is_default': False}
        if rec_id:
            save_kwargs['id'] = rec_id
        question = serializer.save(**save_kwargs)
        return success_response(EvaluationQuestionSerializer(question).data, status=201)


class EvaluationQuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        question = get_object_or_404(
            EvaluationQuestion, id=pk, user=request.user, is_deleted=False
        )
        serializer = EvaluationQuestionSerializer(question, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        question = serializer.save()
        return success_response(EvaluationQuestionSerializer(question).data, status=200)

    def delete(self, request, pk):
        question = get_object_or_404(
            EvaluationQuestion, id=pk, user=request.user, is_deleted=False
        )
        # Soft-delete question
        question.is_deleted = True
        question.save(update_fields=['is_deleted', 'updated_at'])
        # Soft-delete all answers linked to this question
        EvaluationAnswer.objects.filter(
            question=question,
            skill_topic__sub_skill__skill__user=request.user
        ).update(is_deleted=True)
        return success_response({"detail": "Deleted"}, status=200)


class EvaluationQuestionReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        questions_data = request.data.get('questions')
        if not isinstance(questions_data, list):
            return error_response("questions must be a list", status=400)
        for item in questions_data:
            q_id = item.get('id')
            new_order = item.get('order')
            if q_id is not None and new_order is not None:
                EvaluationQuestion.objects.filter(
                    id=q_id,
                    user=request.user,
                    is_deleted=False
                ).update(order=new_order)
        return success_response({"detail": "Reordered"}, status=200)


class EvaluationAnswerListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        skill_topic_id = request.query_params.get('skill_topic_id')
        level = request.query_params.get('level')
        queryset = EvaluationAnswer.objects.filter(
            skill_topic__sub_skill__skill__user=request.user,
            is_deleted=False
        )
        if skill_topic_id:
            get_object_or_404(
                SkillTopic, id=skill_topic_id,
                sub_skill__skill__user=request.user, is_deleted=False
            )
            queryset = queryset.filter(skill_topic_id=skill_topic_id)
        if level:
            queryset = queryset.filter(level=level)
        serializer = EvaluationAnswerSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    def post(self, request):
        question_id = request.data.get('question_id')
        if not question_id:
            return error_response("question_id is required", status=400)

        question = get_object_or_404(
            EvaluationQuestion, id=question_id, user=request.user, is_deleted=False
        )
        skill_topic_id = request.data.get('skill_topic_id')
        if not skill_topic_id:
            return error_response("skill_topic_id is required", status=400)

        skill_topic = get_object_or_404(
            SkillTopic, id=skill_topic_id,
            sub_skill__skill__user=request.user, is_deleted=False
        )
        if EvaluationAnswer.objects.filter(
            skill_topic=skill_topic, question=question, is_deleted=False
        ).exists():
            return error_response("Answer already exists for this question", status=400)

        existing_deleted = EvaluationAnswer.objects.filter(
            skill_topic=skill_topic, question=question, is_deleted=True
        ).first()
        if existing_deleted:
            existing_deleted.is_deleted = False
            existing_deleted.level = question.level
            existing_deleted.save(update_fields=['is_deleted', 'level', 'updated_at'])
            return success_response(EvaluationAnswerSerializer(existing_deleted).data, status=201)

        rec_id = request.data.get('id')
        answer = EvaluationAnswer.objects.create(
            id=rec_id if rec_id else uuid.uuid4(),
            skill_topic=skill_topic,
            question=question,
            level=question.level,
        )
        return success_response(EvaluationAnswerSerializer(answer).data, status=201)



class EvaluationAnswerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        answer = get_object_or_404(
            EvaluationAnswer,
            id=pk,
            skill_topic__sub_skill__skill__user=request.user,
            is_deleted=False
        )
        serializer = EvaluationAnswerDetailSerializer(answer)
        return success_response(serializer.data, status=200)

    def delete(self, request, pk):
        answer = get_object_or_404(
            EvaluationAnswer,
            id=pk,
            skill_topic__sub_skill__skill__user=request.user,
            is_deleted=False
        )
        answer.is_deleted = True
        answer.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class EvaluationAnswerBlockListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        answer_id = request.query_params.get('answer_id')
        queryset = EvaluationAnswerBlock.objects.filter(
            answer__skill_topic__sub_skill__skill__user=request.user,
            is_deleted=False
        )
        if answer_id:
            get_object_or_404(
                EvaluationAnswer,
                id=answer_id,
                skill_topic__sub_skill__skill__user=request.user,
                is_deleted=False
            )
            queryset = queryset.filter(answer_id=answer_id)
        serializer = EvaluationAnswerBlockSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    def post(self, request):
        answer_id = request.data.get('answer_id')
        if not answer_id:
            return error_response("answer_id is required", status=400)
        get_object_or_404(
            EvaluationAnswer,
            id=answer_id,
            skill_topic__sub_skill__skill__user=request.user,
            is_deleted=False
        )

        serializer = EvaluationAnswerBlockSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        block = serializer.save()
        return success_response(EvaluationAnswerBlockSerializer(block).data, status=201)


class EvaluationAnswerBlockDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        block = get_object_or_404(
            EvaluationAnswerBlock,
            id=pk,
            answer__skill_topic__sub_skill__skill__user=request.user,
            is_deleted=False
        )
        serializer = EvaluationAnswerBlockSerializer(block, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        block = serializer.save()
        return success_response(EvaluationAnswerBlockSerializer(block).data, status=200)

    def delete(self, request, pk):
        block = get_object_or_404(
            EvaluationAnswerBlock,
            id=pk,
            answer__skill_topic__sub_skill__skill__user=request.user,
            is_deleted=False
        )
        block.is_deleted = True
        block.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class EvaluationAnswerBlockReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        blocks_data = request.data.get('blocks')
        if not isinstance(blocks_data, list):
            return error_response("blocks must be a list", status=400)

        for item in blocks_data:
            block_id = item.get('id')
            new_order = item.get('order')
            if block_id is not None and new_order is not None:
                EvaluationAnswerBlock.objects.filter(
                    id=block_id,
                    answer__skill_topic__sub_skill__skill__user=request.user,
                    is_deleted=False
                ).update(order=new_order)

        return success_response({"detail": "Reordered"}, status=200)
