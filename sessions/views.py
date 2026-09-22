import uuid
from datetime import date, timedelta
from django.db.models import Sum, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from common.response import success_response, error_response
from academic.models import AcademicTopic
from skills.models import SkillTopic
from .models import TopicSession
from .serializers import (
    TopicSessionSerializer,
    TopicSessionResponseSerializer,
    SessionStartRequestSerializer,
    SessionUpdateRequestSerializer,
    TopicTimeResponseSerializer,
    SubSkillTimeResponseSerializer,
    SkillTimeResponseSerializer,
    OverviewAnalyticsResponseSerializer,
)


class SessionStartView(APIView):
    """Start a new study session."""
    permission_classes = [IsAuthenticated]
    serializer_class = SessionStartRequestSerializer

    @extend_schema(
        tags=['Study Sessions'],
        summary='Start new session',
        description='Start a new study session for an academic or skill topic (stopwatch or timer mode).',
        request=SessionStartRequestSerializer,
        responses={201: TopicSessionResponseSerializer},
    )
    def post(self, request):
        # Prevent starting a new session if one is already active
        active = TopicSession.objects.filter(
            user=request.user,
            is_completed=False
        ).first()
        if active:
            return error_response(
                "A session is already active. End it before starting a new one.",
                status=400
            )

        topic_type = request.data.get('topic_type')   # 'academic' or 'skill'
        topic_id   = request.data.get('topic_id')
        mode       = request.data.get('mode', 'stopwatch')
        timer_goal = request.data.get('timer_goal_seconds')
        started_at = request.data.get('started_at')
        rec_id     = request.data.get('id')

        if topic_type not in ['academic', 'skill']:
            return error_response("topic_type must be 'academic' or 'skill'", status=400)
        if not topic_id:
            return error_response("topic_id is required", status=400)
        if not started_at:
            return error_response("started_at is required", status=400)
        if mode not in ['stopwatch', 'timer']:
            return error_response("mode must be 'stopwatch' or 'timer'", status=400)
        if mode == 'timer' and not timer_goal:
            return error_response("timer_goal_seconds is required for timer mode", status=400)

        academic_topic = None
        skill_topic = None

        if topic_type == 'academic':
            academic_topic = get_object_or_404(
                AcademicTopic,
                id=topic_id,
                chapter__subject__semester__user=request.user,
                is_deleted=False
            )
        else:
            skill_topic = get_object_or_404(
                SkillTopic,
                id=topic_id,
                sub_skill__skill__user=request.user,
                is_deleted=False
            )

        session = TopicSession.objects.create(
            id=rec_id if rec_id else uuid.uuid4(),
            user=request.user,
            academic_topic=academic_topic,
            skill_topic=skill_topic,
            mode=mode,
            timer_goal_seconds=timer_goal if mode == 'timer' else None,
            started_at=started_at,
            duration_seconds=0,
            is_completed=False,
        )
        return success_response(TopicSessionSerializer(session).data, status=201)


class SessionUpdateView(APIView):
    """Pause (update duration) or end a session."""
    permission_classes = [IsAuthenticated]
    serializer_class = SessionUpdateRequestSerializer

    @extend_schema(
        tags=['Study Sessions'],
        summary='Update or end session',
        description='Update duration seconds and/or mark a study session as completed.',
        request=SessionUpdateRequestSerializer,
        responses={200: TopicSessionResponseSerializer},
    )
    def patch(self, request, pk):
        session = get_object_or_404(
            TopicSession, id=pk, user=request.user
        )
        if session.is_completed:
            return error_response("Session already completed", status=400)

        duration_seconds = request.data.get('duration_seconds')
        is_completed     = request.data.get('is_completed')
        ended_at         = request.data.get('ended_at')

        if duration_seconds is not None:
            session.duration_seconds = duration_seconds
        if is_completed is not None:
            session.is_completed = is_completed
        if ended_at is not None:
            session.ended_at = ended_at

        session.save()
        return success_response(TopicSessionSerializer(session).data, status=200)


class ActiveSessionView(APIView):
    """Returns the currently active (not completed) session, if any."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Study Sessions'],
        summary='Get active session',
        description='Returns the currently active (not completed) session, or null if no session is running.',
        responses={200: TopicSessionResponseSerializer},
    )
    def get(self, request):
        session = TopicSession.objects.filter(
            user=request.user,
            is_completed=False
        ).first()
        if session:
            return success_response(TopicSessionSerializer(session).data, status=200)
        return success_response(None, status=200)


class TopicTimeView(APIView):
    """Total time spent on a single topic."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Analytics'],
        summary='Topic total study time',
        description='Returns total seconds studied for a specific academic or skill topic.',
        parameters=[
            OpenApiParameter(name='topic_type', type=str, location=OpenApiParameter.QUERY, required=True, enum=['academic', 'skill'], description='Type of topic'),
            OpenApiParameter(name='topic_id', type=str, location=OpenApiParameter.QUERY, required=True, description='UUID of the topic'),
        ],
        responses={200: TopicTimeResponseSerializer},
    )
    def get(self, request):
        topic_type = request.query_params.get('topic_type')
        topic_id   = request.query_params.get('topic_id')

        if topic_type not in ['academic', 'skill']:
            return error_response("topic_type must be 'academic' or 'skill'", status=400)
        if not topic_id:
            return error_response("topic_id is required", status=400)

        filter_kwargs = {
            'user': request.user,
            'is_completed': True,
        }
        if topic_type == 'academic':
            filter_kwargs['academic_topic_id'] = topic_id
        else:
            filter_kwargs['skill_topic_id'] = topic_id

        result = TopicSession.objects.filter(**filter_kwargs).aggregate(
            total=Sum('duration_seconds')
        )
        return success_response({
            'topic_type': topic_type,
            'topic_id': topic_id,
            'total_seconds': result['total'] or 0,
        }, status=200)


class SubSkillTimeView(APIView):
    """Total time spent on all topics under a sub-skill."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Analytics'],
        summary='Sub-skill total study time',
        description='Returns total seconds studied for all topics belonging to a sub-skill.',
        parameters=[
            OpenApiParameter(name='sub_skill_id', type=str, location=OpenApiParameter.QUERY, required=True, description='UUID of the sub-skill'),
        ],
        responses={200: SubSkillTimeResponseSerializer},
    )
    def get(self, request):
        sub_skill_id = request.query_params.get('sub_skill_id')
        if not sub_skill_id:
            return error_response("sub_skill_id is required", status=400)

        result = TopicSession.objects.filter(
            user=request.user,
            skill_topic__sub_skill_id=sub_skill_id,
            is_completed=True,
        ).aggregate(total=Sum('duration_seconds'))

        return success_response({
            'sub_skill_id': sub_skill_id,
            'total_seconds': result['total'] or 0,
        }, status=200)


class SkillTimeView(APIView):
    """Total time spent on all topics under a skill."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Analytics'],
        summary='Skill total study time',
        description='Returns total seconds studied across all sub-skills under a parent skill.',
        parameters=[
            OpenApiParameter(name='skill_id', type=str, location=OpenApiParameter.QUERY, required=True, description='UUID of the skill'),
        ],
        responses={200: SkillTimeResponseSerializer},
    )
    def get(self, request):
        skill_id = request.query_params.get('skill_id')
        if not skill_id:
            return error_response("skill_id is required", status=400)

        result = TopicSession.objects.filter(
            user=request.user,
            skill_topic__sub_skill__skill_id=skill_id,
            is_completed=True,
        ).aggregate(total=Sum('duration_seconds'))

        return success_response({
            'skill_id': skill_id,
            'total_seconds': result['total'] or 0,
        }, status=200)


class OverviewAnalyticsView(APIView):
    """
    Academic vs Skill time breakdown for a period.

    Query params:
      period: 'daily' | 'weekly' | 'monthly' | 'yearly'
      date:   YYYY-MM-DD (any date within the desired period)
              defaults to today
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Analytics'],
        summary='Overview study analytics',
        description='Academic vs Skill study time breakdown, daily timeline, and top 5 topics for daily, weekly, monthly, or yearly periods.',
        parameters=[
            OpenApiParameter(name='period', type=str, location=OpenApiParameter.QUERY, required=False, default='weekly', enum=['daily', 'weekly', 'monthly', 'yearly'], description='Analytics time period'),
            OpenApiParameter(name='date', type=str, location=OpenApiParameter.QUERY, required=False, description='Reference date formatted as YYYY-MM-DD (defaults to today)'),
        ],
        responses={200: OverviewAnalyticsResponseSerializer},
    )
    def get(self, request):
        period = request.query_params.get('period', 'weekly')
        date_str = request.query_params.get('date')

        if period not in ['daily', 'weekly', 'monthly', 'yearly']:
            return error_response("period must be daily, weekly, monthly, or yearly", status=400)

        try:
            ref_date = date.fromisoformat(date_str) if date_str else date.today()
        except ValueError:
            return error_response("date must be YYYY-MM-DD format", status=400)

        # Calculate start and end of the period
        if period == 'daily':
            start = ref_date
            end   = ref_date
        elif period == 'weekly':
            start = ref_date - timedelta(days=ref_date.weekday())  # Monday
            end   = start + timedelta(days=6)                       # Sunday
        elif period == 'monthly':
            start = ref_date.replace(day=1)
            # Last day of month
            next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
            end = next_month - timedelta(days=1)
        else:  # yearly
            start = ref_date.replace(month=1, day=1)
            end   = ref_date.replace(month=12, day=31)

        qs = TopicSession.objects.filter(
            user=request.user,
            is_completed=True,
            started_at__date__gte=start,
            started_at__date__lte=end,
        )

        totals = qs.aggregate(
            academic_seconds=Sum(
                'duration_seconds',
                filter=Q(academic_topic__isnull=False)
            ),
            skill_seconds=Sum(
                'duration_seconds',
                filter=Q(skill_topic__isnull=False)
            ),
        )

        # Daily breakdown within the period (for bar chart)
        daily_qs = qs.annotate(day=TruncDate('started_at')).values('day').annotate(
            academic=Sum('duration_seconds', filter=Q(academic_topic__isnull=False)),
            skill=Sum('duration_seconds', filter=Q(skill_topic__isnull=False)),
        ).order_by('day')

        daily_data = [
            {
                'date': str(row['day']),
                'academic_seconds': row['academic'] or 0,
                'skill_seconds': row['skill'] or 0,
            }
            for row in daily_qs
        ]

        # Top 5 topics in this period
        top_academic = (
            qs.filter(academic_topic__isnull=False)
            .values('academic_topic_id', 'academic_topic__title')
            .annotate(total=Sum('duration_seconds'))
            .order_by('-total')[:5]
        )
        top_skill = (
            qs.filter(skill_topic__isnull=False)
            .values('skill_topic_id', 'skill_topic__title')
            .annotate(total=Sum('duration_seconds'))
            .order_by('-total')[:5]
        )

        academic_sec = totals['academic_seconds'] or 0
        skill_sec    = totals['skill_seconds'] or 0

        return success_response({
            'period': period,
            'start_date': str(start),
            'end_date': str(end),
            'academic_seconds': academic_sec,
            'skill_seconds': skill_sec,
            'total_seconds': academic_sec + skill_sec,
            'daily_breakdown': daily_data,
            'top_academic_topics': [
                {
                    'topic_id': str(r['academic_topic_id']),
                    'title': r['academic_topic__title'],
                    'total_seconds': r['total'],
                }
                for r in top_academic
            ],
            'top_skill_topics': [
                {
                    'topic_id': str(r['skill_topic_id']),
                    'title': r['skill_topic__title'],
                    'total_seconds': r['total'],
                }
                for r in top_skill
            ],
        }, status=200)
