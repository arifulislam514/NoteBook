from django.urls import path
from .views import SyncPushView

urlpatterns = [
    path('push/', SyncPushView.as_view(), name='sync_push'),
]
