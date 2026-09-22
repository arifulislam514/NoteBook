from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/academic/', include('academic.urls')),
    path('api/skills/', include('skills.urls')),
    path('api/', include('upload.urls')),
    path('api/sync/', include('sync.urls')),
    path('api/sessions/', include('sessions.urls')),
    path('api/analytics/', include('sessions.analytics_urls')),
]
