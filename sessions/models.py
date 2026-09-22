from django.db import models
from django.conf import settings
from common.models import BaseModel


class TopicSession(BaseModel):
    """
    One study session for a topic. Created when user starts the timer,
    updated on each pause, finalized when user ends the session.

    Only one of academic_topic or skill_topic will be set — not both.
    """
    MODE_CHOICES = [
        ('stopwatch', 'Stopwatch'),
        ('timer', 'Timer'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions'
    )

    # Exactly one of these will be non-null
    academic_topic = models.ForeignKey(
        'academic.AcademicTopic',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='sessions'
    )
    skill_topic = models.ForeignKey(
        'skills.SkillTopic',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='sessions'
    )

    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='stopwatch')

    # For timer mode: how many seconds the user set as goal (e.g. 1800 for 30 min)
    # null for stopwatch mode
    timer_goal_seconds = models.PositiveIntegerField(null=True, blank=True)

    started_at = models.DateTimeField()            # set by mobile client
    ended_at = models.DateTimeField(null=True, blank=True)  # set when session ends

    # Total accumulated seconds. Mobile updates this on each pause and on end.
    duration_seconds = models.PositiveIntegerField(default=0)

    # False = session in progress or paused
    # True  = session properly ended by user (or timer completed)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        topic = self.academic_topic or self.skill_topic
        return f"{self.user.email} — {topic} — {self.duration_seconds}s"
