from django.urls import path
from .views import (
    SkillListCreateView,
    SkillDetailView,
    SubSkillListCreateView,
    SubSkillDetailView,
    SkillWantToLearnListCreateView,
    SkillWantToLearnDetailView,
    SkillTopicListCreateView,
    SkillTopicDetailView,
    EvaluationQuestionListCreateView,
    EvaluationQuestionDetailView,
    EvaluationQuestionReorderView,
    EvaluationAnswerListCreateView,
    EvaluationAnswerDetailView,
    EvaluationAnswerBlockListCreateView,
    EvaluationAnswerBlockDetailView,
    EvaluationAnswerBlockReorderView,
)

urlpatterns = [
    path('', SkillListCreateView.as_view(), name='skill_list_create'),
    path('<uuid:pk>/', SkillDetailView.as_view(), name='skill_detail'),

    path('sub-skills/', SubSkillListCreateView.as_view(), name='sub_skill_list_create'),
    path('sub-skills/<uuid:pk>/', SubSkillDetailView.as_view(), name='sub_skill_detail'),

    path('want-to-learn/', SkillWantToLearnListCreateView.as_view(), name='skill_want_to_learn_list_create'),
    path('want-to-learn/<uuid:pk>/', SkillWantToLearnDetailView.as_view(), name='skill_want_to_learn_detail'),

    path('topics/', SkillTopicListCreateView.as_view(), name='skill_topic_list_create'),
    path('topics/<uuid:pk>/', SkillTopicDetailView.as_view(), name='skill_topic_detail'),

    path('questions/', EvaluationQuestionListCreateView.as_view(), name='evaluation_question_list_create'),
    path('questions/reorder/', EvaluationQuestionReorderView.as_view(), name='evaluation_question_reorder'),
    path('questions/<uuid:pk>/', EvaluationQuestionDetailView.as_view(), name='evaluation_question_detail'),

    path('evaluation-answers/', EvaluationAnswerListCreateView.as_view(), name='evaluation_answer_list_create'),
    path('evaluation-answers/<uuid:pk>/', EvaluationAnswerDetailView.as_view(), name='evaluation_answer_detail'),

    path('answer-blocks/', EvaluationAnswerBlockListCreateView.as_view(), name='evaluation_answer_block_list_create'),
    path('answer-blocks/reorder/', EvaluationAnswerBlockReorderView.as_view(), name='evaluation_answer_block_reorder'),
    path('answer-blocks/<uuid:pk>/', EvaluationAnswerBlockDetailView.as_view(), name='evaluation_answer_block_detail'),
    
]
