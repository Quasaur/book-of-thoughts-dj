"""
Topics URL configuration
Optimized routing for M1 MacBook performance
"""

from django.urls import path, include
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from . import views

app_name = 'topics'

# Web views (HTML)
web_patterns = [
    path('', views.TopicsOverviewView.as_view(), name='overview'),
    path('hierarchy/', views.TopicsHierarchyView.as_view(), name='hierarchy'),
    path('topic/<str:topic_id>/', views.TopicDetailView.as_view(), name='detail'),
    path('slug/<slug:slug>/', views.TopicDetailView.as_view(), name='detail-by-slug'),
    
    # Backwards compatibility
    path('table/', views.topics_table_view, name='table'),
]

# API views (JSON)
api_patterns = [
    path('', views.TopicsListAPIView.as_view(), name='api-list'),
    path('<str:topic_id>/', views.TopicDetailAPIView.as_view(), name='api-detail'),
    path('hierarchy/data/', views.TopicsHierarchyAPIView.as_view(), name='api-hierarchy'),
    path('sync/', views.TopicsSyncAPIView.as_view(), name='api-sync'),
    path('stats/', views.topics_stats_view, name='api-stats'),
]

# Main URL patterns
urlpatterns = [
    # Web interface
    path('', include(web_patterns)),
    
    # API endpoints
    path('api/', include(api_patterns)),
]