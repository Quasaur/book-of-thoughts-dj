from django.urls import path
from . import views

app_name = 'topics_app'

urlpatterns = [
    path('', views.topics_view, name='topics_view'),
    path('api/data/', views.topics_data_api, name='topics_data'),
    path('api/list/', views.TopicsListView.as_view(), name='topics_list'),
    path('api/detail/<str:topic_id>/', views.topic_detail, name='topic_detail'),
]