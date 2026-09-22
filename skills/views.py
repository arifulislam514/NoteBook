import uuid
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
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
    EvaluationQuestionReorderRequestSerializer,
    EvaluationAnswerCreateRequestSerializer,
    EvaluationAnswerBlockReorderRequestSerializer,
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
    serializer_class = SkillSerializer

    @extend_schema(
        tags=['Skills'],
        summary='List skills',
        description='Returns all active skills belonging to the authenticated user.',
        responses={200: SkillSerializer(many=True)},
    )
    def get(self, request):
        skills = Skill.objects.filter(user=request.user, is_deleted=False)
        serializer = SkillSerializer(skills, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Skills'],
        summary='Create skill',
        description='Create a new skill category.',
        request=SkillSerializer,
        responses={201: SkillSerializer},
    )
    def post(self, request):
        serializer = SkillSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        skill = serializer.save(user=request.user)
        return success_response(SkillSerializer(skill).data, status=201)


class SkillDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SkillSerializer

    @extend_schema(
        tags=['Skills'],
        summary='Update skill',
        description='Partially update skill name.',
        request=SkillSerializer,
        responses={200: SkillSerializer},
    )
    def patch(self, request, pk):
        skill = get_object_or_404(Skill, id=pk, user=request.user, is_deleted=False)
        serializer = SkillSerializer(skill, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        skill = serializer.save()
        return success_response(SkillSerializer(skill).data, status=200)

    @extend_schema(
        tags=['Skills'],
        summary='Delete skill',
        description='Soft delete a skill.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        skill = get_object_or_404(Skill, id=pk, user=request.user, is_deleted=False)
        skill.is_deleted = True
        skill.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class SubSkillListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubSkillSerializer

    @extend_schema(
        tags=['Skills - Sub-Skills'],
        summary='List sub-skills',
        description='List sub-skills belonging to user. Optionally filter by skill_id.',
        parameters=[
            OpenApiParameter(name='skill_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter by parent skill UUID'),
        ],
        responses={200: SubSkillSerializer(many=True)},
    )
    def get(self, request):
        skill_id = request.query_params.get('skill_id')
        queryset = SubSkill.objects.filter(skill__user=request.user, is_deleted=False)
        if skill_id:
            get_object_or_404(Skill, id=skill_id, user=request.user, is_deleted=False)
            queryset = queryset.filter(skill_id=skill_id)
        serializer = SubSkillSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Skills - Sub-Skills'],
        summary='Create sub-skill',
        description='Create a sub-skill under a parent skill_id.',
        request=SubSkillSerializer,
        responses={201: SubSkillSerializer},
    )
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
    serializer_class = SubSkillSerializer

    @extend_schema(
        tags=['Skills - Sub-Skills'],
        summary='Update sub-skill',
        description='Partially update sub-skill name.',
        request=SubSkillSerializer,
        responses={200: SubSkillSerializer},
    )
    def patch(self, request, pk):
        sub_skill = get_object_or_404(SubSkill, id=pk, skill__user=request.user, is_deleted=False)
        serializer = SubSkillSerializer(sub_skill, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        sub_skill = serializer.save()
        return success_response(SubSkillSerializer(sub_skill).data, status=200)

    @extend_schema(
        tags=['Skills - Sub-Skills'],
        summary='Delete sub-skill',
        description='Soft delete a sub-skill.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        sub_skill = get_object_or_404(SubSkill, id=pk, skill__user=request.user, is_deleted=False)
        sub_skill.is_deleted = True
        sub_skill.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class SkillWantToLearnListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SkillWantToLearnSerializer

    @extend_schema(
        tags=['Skills - Want to Learn'],
        summary='List skill want-to-learn items',
        description='List wish-list topics under sub-skills. Optionally filter by sub_skill_id.',
        parameters=[
            OpenApiParameter(name='sub_skill_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter by sub-skill UUID'),
        ],
        responses={200: SkillWantToLearnSerializer(many=True)},
    )
    def get(self, request):
        sub_skill_id = request.query_params.get('sub_skill_id')
        queryset = SkillWantToLearn.objects.filter(sub_skill__skill__user=request.user, is_deleted=False)
        if sub_skill_id:
            get_object_or_404(SubSkill, id=sub_skill_id, skill__user=request.user, is_deleted=False)
            queryset = queryset.filter(sub_skill_id=sub_skill_id)
        serializer = SkillWantToLearnSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Skills - Want to Learn'],
        summary='Create skill want-to-learn item',
        description='Add a want-to-learn wish item under a sub-skill.',
        request=SkillWantToLearnSerializer,
        responses={201: SkillWantToLearnSerializer},
    )
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
    serializer_class = SkillWantToLearnSerializer

    @extend_schema(
        tags=['Skills - Want to Learn'],
        summary='Update skill want-to-learn item',
        description='Partially update status (is_done) or title.',
        request=SkillWantToLearnSerializer,
        responses={200: SkillWantToLearnSerializer},
    )
    def patch(self, request, pk):
        item = get_object_or_404(SkillWantToLearn, id=pk, sub_skill__skill__user=request.user, is_deleted=False)
        serializer = SkillWantToLearnSerializer(item, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        item = serializer.save()
        return success_response(SkillWantToLearnSerializer(item).data, status=200)

    @extend_schema(
        tags=['Skills - Want to Learn'],
        summary='Delete skill want-to-learn item',
        description='Soft delete a want-to-learn item.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        item = get_object_or_404(SkillWantToLearn, id=pk, sub_skill__skill__user=request.user, is_deleted=False)
        item.is_deleted = True
        item.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class SkillTopicListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SkillTopicSerializer

    @extend_schema(
        tags=['Skills - Topics'],
        summary='List skill topics',
        description='List topics under a sub-skill. Optionally filter by sub_skill_id.',
        parameters=[
            OpenApiParameter(name='sub_skill_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter by sub-skill UUID'),
        ],
        responses={200: SkillTopicSerializer(many=True)},
    )
    def get(self, request):
        sub_skill_id = request.query_params.get('sub_skill_id')
        queryset = SkillTopic.objects.filter(sub_skill__skill__user=request.user, is_deleted=False)
        if sub_skill_id:
            get_object_or_404(SubSkill, id=sub_skill_id, skill__user=request.user, is_deleted=False)
            queryset = queryset.filter(sub_skill_id=sub_skill_id)
        serializer = SkillTopicSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Skills - Topics'],
        summary='Create skill topic',
        description='Create a new topic under a sub-skill.',
        request=SkillTopicSerializer,
        responses={201: SkillTopicSerializer},
    )
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
    serializer_class = SkillTopicSerializer

    @extend_schema(
        tags=['Skills - Topics'],
        summary='Update skill topic',
        description='Partially update topic title or current_level.',
        request=SkillTopicSerializer,
        responses={200: SkillTopicSerializer},
    )
    def patch(self, request, pk):
        topic = get_object_or_404(SkillTopic, id=pk, sub_skill__skill__user=request.user, is_deleted=False)
        serializer = SkillTopicSerializer(topic, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        topic = serializer.save()
        return success_response(SkillTopicSerializer(topic).data, status=200)

    @extend_schema(
        tags=['Skills - Topics'],
        summary='Delete skill topic',
        description='Soft delete a skill topic.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        topic = get_object_or_404(SkillTopic, id=pk, sub_skill__skill__user=request.user, is_deleted=False)
        topic.is_deleted = True
        topic.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class EvaluationQuestionListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EvaluationQuestionSerializer

    @extend_schema(
        tags=['Skills - Evaluation Questions'],
        summary='List evaluation questions',
        description='Retrieve evaluation questions for a specific mastery level (basic, intermediate, advanced, expert). Auto-seeds defaults if not seeded yet.',
        parameters=[
            OpenApiParameter(name='level', type=str, location=OpenApiParameter.QUERY, required=True, enum=['basic', 'intermediate', 'advanced', 'expert'], description='Mastery level'),
        ],
        responses={200: EvaluationQuestionSerializer(many=True)},
    )
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

    @extend_schema(
        tags=['Skills - Evaluation Questions'],
        summary='Create evaluation question',
        description='Create a custom evaluation question for a mastery level.',
        request=EvaluationQuestionSerializer,
        responses={201: EvaluationQuestionSerializer},
    )
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
    serializer_class = EvaluationQuestionSerializer

    @extend_schema(
        tags=['Skills - Evaluation Questions'],
        summary='Update evaluation question',
        description='Partially update question text or order.',
        request=EvaluationQuestionSerializer,
        responses={200: EvaluationQuestionSerializer},
    )
    def patch(self, request, pk):
        question = get_object_or_404(
            EvaluationQuestion, id=pk, user=request.user, is_deleted=False
        )
        serializer = EvaluationQuestionSerializer(question, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        question = serializer.save()
        return success_response(EvaluationQuestionSerializer(question).data, status=200)

    @extend_schema(
        tags=['Skills - Evaluation Questions'],
        summary='Delete evaluation question',
        description='Soft delete an evaluation question and cascade delete linked answers.',
        responses={200: dict},
    )
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
    serializer_class = EvaluationQuestionReorderRequestSerializer

    @extend_schema(
        tags=['Skills - Evaluation Questions'],
        summary='Reorder evaluation questions',
        description='Batch update display ordering of evaluation questions.',
        request=EvaluationQuestionReorderRequestSerializer,
        responses={200: dict},
    )
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
    serializer_class = EvaluationAnswerCreateRequestSerializer

    @extend_schema(
        tags=['Skills - Evaluation Answers'],
        summary='List evaluation answers',
        description='List evaluation answers. Optionally filter by skill_topic_id and mastery level.',
        parameters=[
            OpenApiParameter(name='skill_topic_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter by skill topic UUID'),
            OpenApiParameter(name='level', type=str, location=OpenApiParameter.QUERY, required=False, enum=['basic', 'intermediate', 'advanced', 'expert'], description='Filter by level'),
        ],
        responses={200: EvaluationAnswerSerializer(many=True)},
    )
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

    @extend_schema(
        tags=['Skills - Evaluation Answers'],
        summary='Create evaluation answer',
        description='Submit an evaluation answer linking a skill topic and an evaluation question.',
        request=EvaluationAnswerCreateRequestSerializer,
        responses={201: EvaluationAnswerSerializer},
    )
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

    @extend_schema(
        tags=['Skills - Evaluation Answers'],
        summary='Get evaluation answer with blocks',
        description='Retrieve an evaluation answer including its nested content blocks and question text.',
        responses={200: EvaluationAnswerDetailSerializer},
    )
    def get(self, request, pk):
        answer = get_object_or_404(
            EvaluationAnswer,
            id=pk,
            skill_topic__sub_skill__skill__user=request.user,
            is_deleted=False
        )
        serializer = EvaluationAnswerDetailSerializer(answer)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Skills - Evaluation Answers'],
        summary='Delete evaluation answer',
        description='Soft delete an evaluation answer.',
        responses={200: dict},
    )
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
    serializer_class = EvaluationAnswerBlockSerializer

    @extend_schema(
        tags=['Skills - Evaluation Answer Blocks'],
        summary='List answer blocks',
        description='List content blocks for an answer. Optionally filter by answer_id.',
        parameters=[
            OpenApiParameter(name='answer_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter by answer UUID'),
        ],
        responses={200: EvaluationAnswerBlockSerializer(many=True)},
    )
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

    @extend_schema(
        tags=['Skills - Evaluation Answer Blocks'],
        summary='Create answer block',
        description='Add a new content block to an evaluation answer.',
        request=EvaluationAnswerBlockSerializer,
        responses={201: EvaluationAnswerBlockSerializer},
    )
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
    serializer_class = EvaluationAnswerBlockSerializer

    @extend_schema(
        tags=['Skills - Evaluation Answer Blocks'],
        summary='Update answer block',
        description='Partially update content or order of an answer block.',
        request=EvaluationAnswerBlockSerializer,
        responses={200: EvaluationAnswerBlockSerializer},
    )
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

    @extend_schema(
        tags=['Skills - Evaluation Answer Blocks'],
        summary='Delete answer block',
        description='Soft delete an answer block.',
        responses={200: dict},
    )
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
    serializer_class = EvaluationAnswerBlockReorderRequestSerializer

    @extend_schema(
        tags=['Skills - Evaluation Answer Blocks'],
        summary='Reorder answer blocks',
        description='Batch update the order of blocks for an evaluation answer.',
        request=EvaluationAnswerBlockReorderRequestSerializer,
        responses={200: dict},
    )
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
