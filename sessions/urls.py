from django.urls import path
from .views import SessionStartView, SessionUpdateView, ActiveSessionView

urlpatterns = [
    path('start/', SessionStartView.as_view(), name='session_start'),
    path('active/', ActiveSessionView.as_view(), name='session_active'),
    path('<uuid:pk>/', SessionUpdateView.as_view(), name='session_update'),
]
