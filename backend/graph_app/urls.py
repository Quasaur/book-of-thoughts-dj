from django.urls import path
from . import views

app_name = 'graph_app'

urlpatterns = [
    path('', views.graph_view, name='graph_view'),
    path('api/data/', views.graph_data_api, name='graph_data'),
    path('api/node/<str:node_id>/', views.graph_node_detail, name='node_detail'),
]