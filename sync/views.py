from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from common.response import success_response, error_response
from .serializers import SyncPushRequestSerializer, SyncPushResponseSerializer

from academic.models import (
    Semester,
    Subject,
    AcademicWantToLearn,
    Chapter,
    AcademicTopic,
    AcademicTopicBlock,
)
from skills.models import (
    Skill,
    SubSkill,
    SkillWantToLearn,
    SkillTopic,
    EvaluationQuestion,
    EvaluationAnswer,
    EvaluationAnswerBlock,
)
from sessions.models import TopicSession


def parse_datetime_safe(dt_val):
    if not dt_val:
        return None
    if isinstance(dt_val, datetime):
        return dt_val if dt_val.tzinfo else dt_val.replace(tzinfo=timezone.utc)
    try:
        val_str = str(dt_val).replace('Z', '+00:00')
        parsed = datetime.fromisoformat(val_str)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def serialize_record(obj, fields):
    data = {}
    for f in fields:
        val = getattr(obj, f)
        if isinstance(val, datetime):
            data[f] = val.isoformat()
        elif hasattr(val, 'hex'):  # UUID
            data[f] = str(val)
        else:
            data[f] = val
    return data


class SyncPushView(APIView):
    permission_classes = [IsAuthenticated]

    MODEL_CONFIG = [
        {
            'key': 'semesters',
            'model': Semester,
            'is_user_top_level': True,
            'fields': ['id', 'name', 'year', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['name', 'year', 'is_deleted'],
            'filter_user': lambda u: Semester.objects.filter(user=u),
        },
        {
            'key': 'subjects',
            'model': Subject,
            'is_user_top_level': False,
            'fk_field': 'semester_id',
            'fields': ['id', 'semester_id', 'name', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['semester_id', 'name', 'is_deleted'],
            'filter_user': lambda u: Subject.objects.filter(semester__user=u),
        },
        {
            'key': 'academic_want_to_learn',
            'model': AcademicWantToLearn,
            'is_user_top_level': False,
            'fk_field': 'subject_id',
            'fields': ['id', 'subject_id', 'title', 'is_done', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['subject_id', 'title', 'is_done', 'is_deleted'],
            'filter_user': lambda u: AcademicWantToLearn.objects.filter(subject__semester__user=u),
        },
        {
            'key': 'chapters',
            'model': Chapter,
            'is_user_top_level': False,
            'fk_field': 'subject_id',
            'fields': ['id', 'subject_id', 'name', 'order', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['subject_id', 'name', 'order', 'is_deleted'],
            'filter_user': lambda u: Chapter.objects.filter(subject__semester__user=u),
        },
        {
            'key': 'academic_topics',
            'model': AcademicTopic,
            'is_user_top_level': False,
            'fk_field': 'chapter_id',
            'fields': ['id', 'chapter_id', 'title', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['chapter_id', 'title', 'is_deleted'],
            'filter_user': lambda u: AcademicTopic.objects.filter(chapter__subject__semester__user=u),
        },
        {
            'key': 'academic_topic_blocks',
            'model': AcademicTopicBlock,
            'is_user_top_level': False,
            'fk_field': 'topic_id',
            'fields': ['id', 'topic_id', 'type', 'content', 'order', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['topic_id', 'type', 'content', 'order', 'is_deleted'],
            'filter_user': lambda u: AcademicTopicBlock.objects.filter(topic__chapter__subject__semester__user=u),
        },
        {
            'key': 'skills',
            'model': Skill,
            'is_user_top_level': True,
            'fields': ['id', 'name', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['name', 'is_deleted'],
            'filter_user': lambda u: Skill.objects.filter(user=u),
        },
        {
            'key': 'sub_skills',
            'model': SubSkill,
            'is_user_top_level': False,
            'fk_field': 'skill_id',
            'fields': ['id', 'skill_id', 'name', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['skill_id', 'name', 'is_deleted'],
            'filter_user': lambda u: SubSkill.objects.filter(skill__user=u),
        },
        {
            'key': 'skill_want_to_learn',
            'model': SkillWantToLearn,
            'is_user_top_level': False,
            'fk_field': 'sub_skill_id',
            'fields': ['id', 'sub_skill_id', 'title', 'is_done', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['sub_skill_id', 'title', 'is_done', 'is_deleted'],
            'filter_user': lambda u: SkillWantToLearn.objects.filter(sub_skill__skill__user=u),
        },
        {
            'key': 'skill_topics',
            'model': SkillTopic,
            'is_user_top_level': False,
            'fk_field': 'sub_skill_id',
            'fields': ['id', 'sub_skill_id', 'title', 'current_level', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['sub_skill_id', 'title', 'current_level', 'is_deleted'],
            'filter_user': lambda u: SkillTopic.objects.filter(sub_skill__skill__user=u),
        },
        {
            'key': 'evaluation_questions',
            'model': EvaluationQuestion,
            'is_user_top_level': True,
            'fields': ['id', 'level', 'text', 'order', 'is_default', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['level', 'text', 'order', 'is_default', 'is_deleted'],
            'filter_user': lambda u: EvaluationQuestion.objects.filter(user=u),
        },
        {
            'key': 'evaluation_answers',
            'model': EvaluationAnswer,
            'is_user_top_level': False,
            'fk_field': 'skill_topic_id',
            'fields': ['id', 'skill_topic_id', 'level', 'question_id', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['skill_topic_id', 'level', 'question_id', 'is_deleted'],
            'filter_user': lambda u: EvaluationAnswer.objects.filter(skill_topic__sub_skill__skill__user=u),
        },
        {
            'key': 'evaluation_answer_blocks',
            'model': EvaluationAnswerBlock,
            'is_user_top_level': False,
            'fk_field': 'answer_id',
            'fields': ['id', 'answer_id', 'type', 'content', 'order', 'is_deleted', 'created_at', 'updated_at'],
            'update_fields': ['answer_id', 'type', 'content', 'order', 'is_deleted'],
            'filter_user': lambda u: EvaluationAnswerBlock.objects.filter(answer__skill_topic__sub_skill__skill__user=u),
        },
        {
            'key': 'topic_sessions',
            'model': TopicSession,
            'is_user_top_level': True,
            'fields': [
                'id', 'mode', 'timer_goal_seconds',
                'academic_topic_id', 'skill_topic_id',
                'started_at', 'ended_at',
                'duration_seconds', 'is_completed',
                'is_deleted', 'created_at', 'updated_at',
            ],
            'update_fields': [
                'duration_seconds', 'is_completed',
                'ended_at', 'is_deleted',
            ],
            'filter_user': lambda u: TopicSession.objects.filter(user=u),
        },
    ]

    serializer_class = SyncPushRequestSerializer

    @extend_schema(
        tags=['Data Synchronization'],
        summary='Bidirectional sync push',
        description='Upload client changes across all models and receive server-side changes since the last_sync timestamp.',
        request=SyncPushRequestSerializer,
        responses={200: SyncPushResponseSerializer},
    )
    def post(self, request):
        user = request.user
        data = request.data or {}
        last_sync_raw = data.get('last_sync')
        last_sync_dt = parse_datetime_safe(last_sync_raw)
        changes = data.get('changes', {})

        # Process client changes model by model
        for cfg in self.MODEL_CONFIG:
            model_key = cfg['key']
            model_cls = cfg['model']
            records = changes.get(model_key, [])
            if not isinstance(records, list):
                continue

            for record in records:
                rec_id = record.get('id')
                if not rec_id:
                    continue

                client_updated_at = parse_datetime_safe(record.get('updated_at')) or datetime.now(timezone.utc)
                server_obj = cfg['filter_user'](user).filter(id=rec_id).first()

                if server_obj is None:
                    # Case 1: Record does NOT exist on server (new from client)
                    create_kwargs = {'id': rec_id}
                    if cfg.get('is_user_top_level'):
                        create_kwargs['user'] = user

                    fields_to_create = cfg.get('create_fields') or [
                        f for f in cfg['fields'] if f not in ['id', 'created_at', 'updated_at']
                    ]
                    for field_name in fields_to_create:
                        if field_name in record:
                            create_kwargs[field_name] = record[field_name]

                    # Create and set updated_at manually via update
                    model_cls.objects.create(**create_kwargs)
                    model_cls.objects.filter(id=rec_id).update(updated_at=client_updated_at)
                else:
                    # Case 2: Record EXISTS on server
                    # Compare client_updated_at vs server_updated_at
                    server_updated_at = server_obj.updated_at
                    if server_updated_at.tzinfo is None:
                        server_updated_at = server_updated_at.replace(tzinfo=timezone.utc)

                    if client_updated_at > server_updated_at:
                        # Overwrite server with client data
                        update_kwargs = {'updated_at': client_updated_at}
                        for field_name in cfg['update_fields']:
                            if field_name in record:
                                update_kwargs[field_name] = record[field_name]

                        model_cls.objects.filter(id=rec_id).update(**update_kwargs)
                    # If server_updated_at >= client_updated_at: keep server data (do nothing)

        # After processing client changes, gather server changes
        server_changes = {}
        for cfg in self.MODEL_CONFIG:
            qs = cfg['filter_user'](user)
            if last_sync_dt:
                qs = qs.filter(updated_at__gt=last_sync_dt)

            server_changes[cfg['key']] = [
                serialize_record(item, cfg['fields'])
                for item in qs
            ]

        now_utc = datetime.now(timezone.utc).isoformat()
        return success_response({
            "server_changes": server_changes,
            "sync_time": now_utc,
        }, status=200)
