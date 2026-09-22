from django.db import models
from django.conf import settings
from common.models import BaseModel


class Semester(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='semesters'
    )
    name = models.CharField(max_length=100)
    year = models.IntegerField()

    class Meta:
        ordering = ['-year', 'name']

    def __str__(self):
        return f"{self.name} ({self.year})"


class Subject(BaseModel):
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='subjects'
    )
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AcademicWantToLearn(BaseModel):
    """A 'want to learn later' item under a Subject."""
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='want_to_learn'
    )
    title = models.CharField(max_length=300)
    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title


class Chapter(BaseModel):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='chapters'
    )
    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.name


class AcademicTopic(BaseModel):
    """A learned topic inside a Chapter. Contains content blocks."""
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='topics'
    )
    title = models.CharField(max_length=300)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title


class AcademicTopicBlock(BaseModel):
    """
    A content block inside an AcademicTopic.

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
    topic = models.ForeignKey(
        AcademicTopic,
        on_delete=models.CASCADE,
        related_name='blocks'
    )
    type = models.CharField(max_length=10, choices=BLOCK_TYPES)
    content = models.JSONField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.topic.title} - {self.type} ({self.order})"
