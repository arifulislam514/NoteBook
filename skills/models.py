from django.db import models
from django.conf import settings
from common.models import BaseModel

LEVEL_CHOICES = [
    ('none', 'Not Started'),
    ('basic', 'Basic'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
    ('expert', 'Expert'),
]

EVAL_LEVEL_CHOICES = [
    ('basic', 'Basic'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
    ('expert', 'Expert'),
]


class Skill(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skills'
    )
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SubSkill(BaseModel):
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='sub_skills'
    )
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SkillWantToLearn(BaseModel):
    """A 'want to learn later' item under a SubSkill."""
    sub_skill = models.ForeignKey(
        SubSkill,
        on_delete=models.CASCADE,
        related_name='want_to_learn'
    )
    title = models.CharField(max_length=300)
    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title


class SkillTopic(BaseModel):
    """
    A topic under a SubSkill.
    Each topic is evaluated using a 4-level system (Basic → Expert).
    current_level reflects the highest level the user has completed.
    """
    sub_skill = models.ForeignKey(
        SubSkill,
        on_delete=models.CASCADE,
        related_name='topics'
    )
    title = models.CharField(max_length=300)
    current_level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='none'
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title


class EvaluationQuestion(BaseModel):
    """
    Stores evaluation question text per user per level.
    Each user gets their own copy of the default questions,
    which they can edit, delete, or add to.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='evaluation_questions'
    )
    level = models.CharField(max_length=20, choices=EVAL_LEVEL_CHOICES)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=True)
    # is_default=True  → seeded from system defaults
    # is_default=False → user created this question themselves

    class Meta:
        ordering = ['level', 'order']

    def __str__(self):
        return f"[{self.level}] {self.text[:60]}"


class EvaluationAnswer(BaseModel):
    """
    One answer record per (skill_topic, question).
    The actual answer content is stored in EvaluationAnswerBlock.
    """
    skill_topic = models.ForeignKey(
        SkillTopic,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    level = models.CharField(max_length=20, choices=EVAL_LEVEL_CHOICES)
    question = models.ForeignKey(
        EvaluationQuestion,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    class Meta:
        unique_together = ['skill_topic', 'question']
        ordering = ['level', 'question__order']

    def __str__(self):
        return f"{self.skill_topic.title} - {self.level} Q{self.question.order + 1}"


class EvaluationAnswerBlock(BaseModel):
    """
    A content block inside an EvaluationAnswer.

    JSON content structure per type:
      text  → {"value": "some text"}
      code  → {"language": "python", "value": "print('hello')"}
      link  → {"url": "https://...", "label": "optional label"}
      image → {"url": "https://cloudinary.com/...", "caption": "optional"}
    """
    BLOCK_TYPES = [
        ('text', 'Text'),
        ('code', 'Code'),
        ('link', 'Link'),
        ('image', 'Image'),
    ]
    answer = models.ForeignKey(
        EvaluationAnswer,
        on_delete=models.CASCADE,
        related_name='blocks'
    )
    type = models.CharField(max_length=10, choices=BLOCK_TYPES)
    content = models.JSONField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.answer} - {self.type} ({self.order})"
