from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from common.response import success_response, error_response
from .models import (
    Semester,
    Subject,
    AcademicWantToLearn,
    Chapter,
    AcademicTopic,
    AcademicTopicBlock,
)
from .serializers import (
    SemesterSerializer,
    SubjectSerializer,
    AcademicWantToLearnSerializer,
    ChapterSerializer,
    AcademicTopicSerializer,
    AcademicTopicBlockSerializer,
    AcademicTopicBlockReorderRequestSerializer,
)


class SemesterListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SemesterSerializer

    @extend_schema(
        tags=['Academic - Semesters'],
        summary='List all semesters',
        description='Returns all active semesters belonging to the authenticated user.',
        responses={200: SemesterSerializer(many=True)},
    )
    def get(self, request):
        semesters = Semester.objects.filter(user=request.user, is_deleted=False)
        serializer = SemesterSerializer(semesters, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Academic - Semesters'],
        summary='Create semester',
        description='Create a new semester record.',
        request=SemesterSerializer,
        responses={201: SemesterSerializer},
    )
    def post(self, request):
        serializer = SemesterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        semester = serializer.save(user=request.user)
        return success_response(SemesterSerializer(semester).data, status=201)


class SemesterDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SemesterSerializer

    @extend_schema(
        tags=['Academic - Semesters'],
        summary='Update semester',
        description='Partially update an existing semester by its UUID.',
        request=SemesterSerializer,
        responses={200: SemesterSerializer},
    )
    def patch(self, request, pk):
        semester = get_object_or_404(Semester, id=pk, user=request.user, is_deleted=False)
        serializer = SemesterSerializer(semester, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        semester = serializer.save()
        return success_response(SemesterSerializer(semester).data, status=200)

    @extend_schema(
        tags=['Academic - Semesters'],
        summary='Delete semester',
        description='Soft delete a semester by marking is_deleted=True.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        semester = get_object_or_404(Semester, id=pk, user=request.user, is_deleted=False)
        semester.is_deleted = True
        semester.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class SubjectListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubjectSerializer

    @extend_schema(
        tags=['Academic - Subjects'],
        summary='List subjects',
        description='List subjects belonging to the user. Optionally filter by semester_id.',
        parameters=[
            OpenApiParameter(name='semester_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter subjects by semester UUID'),
        ],
        responses={200: SubjectSerializer(many=True)},
    )
    def get(self, request):
        semester_id = request.query_params.get('semester_id')
        queryset = Subject.objects.filter(semester__user=request.user, is_deleted=False)
        if semester_id:
            # validate semester belongs to request.user
            get_object_or_404(Semester, id=semester_id, user=request.user, is_deleted=False)
            queryset = queryset.filter(semester_id=semester_id)
        serializer = SubjectSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Academic - Subjects'],
        summary='Create subject',
        description='Create a new subject under a valid semester_id.',
        request=SubjectSerializer,
        responses={201: SubjectSerializer},
    )
    def post(self, request):
        semester_id = request.data.get('semester_id')
        if not semester_id:
            return error_response("semester_id is required", status=400)
        get_object_or_404(Semester, id=semester_id, user=request.user, is_deleted=False)

        serializer = SubjectSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        subject = serializer.save()
        return success_response(SubjectSerializer(subject).data, status=201)


class SubjectDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubjectSerializer

    @extend_schema(
        tags=['Academic - Subjects'],
        summary='Update subject',
        description='Partially update an existing subject.',
        request=SubjectSerializer,
        responses={200: SubjectSerializer},
    )
    def patch(self, request, pk):
        subject = get_object_or_404(Subject, id=pk, semester__user=request.user, is_deleted=False)
        serializer = SubjectSerializer(subject, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        subject = serializer.save()
        return success_response(SubjectSerializer(subject).data, status=200)

    @extend_schema(
        tags=['Academic - Subjects'],
        summary='Delete subject',
        description='Soft delete a subject by its UUID.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        subject = get_object_or_404(Subject, id=pk, semester__user=request.user, is_deleted=False)
        subject.is_deleted = True
        subject.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class AcademicWantToLearnListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AcademicWantToLearnSerializer

    @extend_schema(
        tags=['Academic - Want to Learn'],
        summary='List academic want-to-learn items',
        description='List wish-list topics to learn for subjects. Optionally filter by subject_id.',
        parameters=[
            OpenApiParameter(name='subject_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter by subject UUID'),
        ],
        responses={200: AcademicWantToLearnSerializer(many=True)},
    )
    def get(self, request):
        subject_id = request.query_params.get('subject_id')
        queryset = AcademicWantToLearn.objects.filter(subject__semester__user=request.user, is_deleted=False)
        if subject_id:
            get_object_or_404(Subject, id=subject_id, semester__user=request.user, is_deleted=False)
            queryset = queryset.filter(subject_id=subject_id)
        serializer = AcademicWantToLearnSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Academic - Want to Learn'],
        summary='Create academic want-to-learn item',
        description='Create a new topic wishlist item under a subject.',
        request=AcademicWantToLearnSerializer,
        responses={201: AcademicWantToLearnSerializer},
    )
    def post(self, request):
        subject_id = request.data.get('subject_id')
        if not subject_id:
            return error_response("subject_id is required", status=400)
        get_object_or_404(Subject, id=subject_id, semester__user=request.user, is_deleted=False)

        serializer = AcademicWantToLearnSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        item = serializer.save()
        return success_response(AcademicWantToLearnSerializer(item).data, status=201)


class AcademicWantToLearnDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AcademicWantToLearnSerializer

    @extend_schema(
        tags=['Academic - Want to Learn'],
        summary='Update academic want-to-learn item',
        description='Partially update status (is_done) or title of a want-to-learn item.',
        request=AcademicWantToLearnSerializer,
        responses={200: AcademicWantToLearnSerializer},
    )
    def patch(self, request, pk):
        item = get_object_or_404(AcademicWantToLearn, id=pk, subject__semester__user=request.user, is_deleted=False)
        serializer = AcademicWantToLearnSerializer(item, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        item = serializer.save()
        return success_response(AcademicWantToLearnSerializer(item).data, status=200)

    @extend_schema(
        tags=['Academic - Want to Learn'],
        summary='Delete academic want-to-learn item',
        description='Soft delete a want-to-learn item.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        item = get_object_or_404(AcademicWantToLearn, id=pk, subject__semester__user=request.user, is_deleted=False)
        item.is_deleted = True
        item.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class ChapterListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChapterSerializer

    @extend_schema(
        tags=['Academic - Chapters'],
        summary='List chapters',
        description='List chapters for subjects. Optionally filter by subject_id.',
        parameters=[
            OpenApiParameter(name='subject_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter by subject UUID'),
        ],
        responses={200: ChapterSerializer(many=True)},
    )
    def get(self, request):
        subject_id = request.query_params.get('subject_id')
        queryset = Chapter.objects.filter(subject__semester__user=request.user, is_deleted=False)
        if subject_id:
            get_object_or_404(Subject, id=subject_id, semester__user=request.user, is_deleted=False)
            queryset = queryset.filter(subject_id=subject_id)
        serializer = ChapterSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Academic - Chapters'],
        summary='Create chapter',
        description='Create a chapter under a subject.',
        request=ChapterSerializer,
        responses={201: ChapterSerializer},
    )
    def post(self, request):
        subject_id = request.data.get('subject_id')
        if not subject_id:
            return error_response("subject_id is required", status=400)
        get_object_or_404(Subject, id=subject_id, semester__user=request.user, is_deleted=False)

        serializer = ChapterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        chapter = serializer.save()
        return success_response(ChapterSerializer(chapter).data, status=201)


class ChapterDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChapterSerializer

    @extend_schema(
        tags=['Academic - Chapters'],
        summary='Update chapter',
        description='Partially update chapter name or order.',
        request=ChapterSerializer,
        responses={200: ChapterSerializer},
    )
    def patch(self, request, pk):
        chapter = get_object_or_404(Chapter, id=pk, subject__semester__user=request.user, is_deleted=False)
        serializer = ChapterSerializer(chapter, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        chapter = serializer.save()
        return success_response(ChapterSerializer(chapter).data, status=200)

    @extend_schema(
        tags=['Academic - Chapters'],
        summary='Delete chapter',
        description='Soft delete a chapter.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        chapter = get_object_or_404(Chapter, id=pk, subject__semester__user=request.user, is_deleted=False)
        chapter.is_deleted = True
        chapter.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class AcademicTopicListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AcademicTopicSerializer

    @extend_schema(
        tags=['Academic - Topics'],
        summary='List academic topics',
        description='List topics under chapters. Optionally filter by chapter_id.',
        parameters=[
            OpenApiParameter(name='chapter_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter by chapter UUID'),
        ],
        responses={200: AcademicTopicSerializer(many=True)},
    )
    def get(self, request):
        chapter_id = request.query_params.get('chapter_id')
        queryset = AcademicTopic.objects.filter(chapter__subject__semester__user=request.user, is_deleted=False)
        if chapter_id:
            get_object_or_404(Chapter, id=chapter_id, subject__semester__user=request.user, is_deleted=False)
            queryset = queryset.filter(chapter_id=chapter_id)
        serializer = AcademicTopicSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Academic - Topics'],
        summary='Create academic topic',
        description='Create a new topic under a chapter.',
        request=AcademicTopicSerializer,
        responses={201: AcademicTopicSerializer},
    )
    def post(self, request):
        chapter_id = request.data.get('chapter_id')
        if not chapter_id:
            return error_response("chapter_id is required", status=400)
        get_object_or_404(Chapter, id=chapter_id, subject__semester__user=request.user, is_deleted=False)

        serializer = AcademicTopicSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        topic = serializer.save()
        return success_response(AcademicTopicSerializer(topic).data, status=201)


class AcademicTopicDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AcademicTopicSerializer

    @extend_schema(
        tags=['Academic - Topics'],
        summary='Update academic topic',
        description='Partially update topic title.',
        request=AcademicTopicSerializer,
        responses={200: AcademicTopicSerializer},
    )
    def patch(self, request, pk):
        topic = get_object_or_404(AcademicTopic, id=pk, chapter__subject__semester__user=request.user, is_deleted=False)
        serializer = AcademicTopicSerializer(topic, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        topic = serializer.save()
        return success_response(AcademicTopicSerializer(topic).data, status=200)

    @extend_schema(
        tags=['Academic - Topics'],
        summary='Delete academic topic',
        description='Soft delete an academic topic.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        topic = get_object_or_404(AcademicTopic, id=pk, chapter__subject__semester__user=request.user, is_deleted=False)
        topic.is_deleted = True
        topic.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class AcademicTopicBlockListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AcademicTopicBlockSerializer

    @extend_schema(
        tags=['Academic - Topic Blocks'],
        summary='List topic blocks',
        description='List content blocks (text, image, markdown, code, etc.) for a topic. Optionally filter by topic_id.',
        parameters=[
            OpenApiParameter(name='topic_id', type=str, location=OpenApiParameter.QUERY, required=False, description='Filter by topic UUID'),
        ],
        responses={200: AcademicTopicBlockSerializer(many=True)},
    )
    def get(self, request):
        topic_id = request.query_params.get('topic_id')
        queryset = AcademicTopicBlock.objects.filter(
            topic__chapter__subject__semester__user=request.user,
            is_deleted=False
        )
        if topic_id:
            get_object_or_404(AcademicTopic, id=topic_id, chapter__subject__semester__user=request.user, is_deleted=False)
            queryset = queryset.filter(topic_id=topic_id)
        serializer = AcademicTopicBlockSerializer(queryset, many=True)
        return success_response(serializer.data, status=200)

    @extend_schema(
        tags=['Academic - Topic Blocks'],
        summary='Create topic block',
        description='Add a new content block to an academic topic.',
        request=AcademicTopicBlockSerializer,
        responses={201: AcademicTopicBlockSerializer},
    )
    def post(self, request):
        topic_id = request.data.get('topic_id')
        if not topic_id:
            return error_response("topic_id is required", status=400)
        get_object_or_404(AcademicTopic, id=topic_id, chapter__subject__semester__user=request.user, is_deleted=False)

        serializer = AcademicTopicBlockSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        block = serializer.save()
        return success_response(AcademicTopicBlockSerializer(block).data, status=201)


class AcademicTopicBlockDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AcademicTopicBlockSerializer

    @extend_schema(
        tags=['Academic - Topic Blocks'],
        summary='Update topic block',
        description='Partially update content or order of a topic block.',
        request=AcademicTopicBlockSerializer,
        responses={200: AcademicTopicBlockSerializer},
    )
    def patch(self, request, pk):
        block = get_object_or_404(
            AcademicTopicBlock,
            id=pk,
            topic__chapter__subject__semester__user=request.user,
            is_deleted=False
        )
        serializer = AcademicTopicBlockSerializer(block, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(str(serializer.errors), status=400)
        block = serializer.save()
        return success_response(AcademicTopicBlockSerializer(block).data, status=200)

    @extend_schema(
        tags=['Academic - Topic Blocks'],
        summary='Delete topic block',
        description='Soft delete a topic block.',
        responses={200: dict},
    )
    def delete(self, request, pk):
        block = get_object_or_404(
            AcademicTopicBlock,
            id=pk,
            topic__chapter__subject__semester__user=request.user,
            is_deleted=False
        )
        block.is_deleted = True
        block.save(update_fields=['is_deleted', 'updated_at'])
        return success_response({"detail": "Deleted"}, status=200)


class AcademicTopicBlockReorderView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AcademicTopicBlockReorderRequestSerializer

    @extend_schema(
        tags=['Academic - Topic Blocks'],
        summary='Reorder topic blocks',
        description='Batch update the display order of multiple blocks within a topic.',
        request=AcademicTopicBlockReorderRequestSerializer,
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
                AcademicTopicBlock.objects.filter(
                    id=block_id,
                    topic__chapter__subject__semester__user=request.user,
                    is_deleted=False
                ).update(order=new_order)

        return success_response({"detail": "Reordered"}, status=200)
