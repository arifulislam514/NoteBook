from django.urls import path
from .views import (
    SemesterListCreateView,
    SemesterDetailView,
    SubjectListCreateView,
    SubjectDetailView,
    AcademicWantToLearnListCreateView,
    AcademicWantToLearnDetailView,
    ChapterListCreateView,
    ChapterDetailView,
    AcademicTopicListCreateView,
    AcademicTopicDetailView,
    AcademicTopicBlockListCreateView,
    AcademicTopicBlockDetailView,
    AcademicTopicBlockReorderView,
)

urlpatterns = [
    path('semesters/', SemesterListCreateView.as_view(), name='semester_list_create'),
    path('semesters/<uuid:pk>/', SemesterDetailView.as_view(), name='semester_detail'),

    path('subjects/', SubjectListCreateView.as_view(), name='subject_list_create'),
    path('subjects/<uuid:pk>/', SubjectDetailView.as_view(), name='subject_detail'),

    path('want-to-learn/', AcademicWantToLearnListCreateView.as_view(), name='academic_want_to_learn_list_create'),
    path('want-to-learn/<uuid:pk>/', AcademicWantToLearnDetailView.as_view(), name='academic_want_to_learn_detail'),

    path('chapters/', ChapterListCreateView.as_view(), name='chapter_list_create'),
    path('chapters/<uuid:pk>/', ChapterDetailView.as_view(), name='chapter_detail'),

    path('topics/', AcademicTopicListCreateView.as_view(), name='academic_topic_list_create'),
    path('topics/<uuid:pk>/', AcademicTopicDetailView.as_view(), name='academic_topic_detail'),

    path('topic-blocks/', AcademicTopicBlockListCreateView.as_view(), name='academic_topic_block_list_create'),
    path('topic-blocks/<uuid:pk>/', AcademicTopicBlockDetailView.as_view(), name='academic_topic_block_detail'),
    path('topic-blocks/reorder/', AcademicTopicBlockReorderView.as_view(), name='academic_topic_block_reorder'),
]
