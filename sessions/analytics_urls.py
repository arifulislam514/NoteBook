from django.urls import path
from .views import TopicTimeView, SubSkillTimeView, SkillTimeView, OverviewAnalyticsView

urlpatterns = [
    path('topic/', TopicTimeView.as_view(), name='analytics_topic'),
    path('sub-skill/', SubSkillTimeView.as_view(), name='analytics_sub_skill'),
    path('skill/', SkillTimeView.as_view(), name='analytics_skill'),
    path('overview/', OverviewAnalyticsView.as_view(), name='analytics_overview'),
]
