# thoughts_api/urls.py
from django.urls import path
from .views import (
    ThoughtsListView, TopicsListView, QuotesListView, PassagesListView,
    ItemDetailView, SearchView, GraphDataView, TagsView, TagItemsView
)

urlpatterns = [
    path('thoughts/', ThoughtsListView.as_view(), name='thoughts-list'),
    path('topics/', TopicsListView.as_view(), name='topics-list'),
    path('quotes/', QuotesListView.as_view(), name='quotes-list'),
    path('passages/', PassagesListView.as_view(), name='passages-list'),
    path('search/', SearchView.as_view(), name='search'),
    path('graph/', GraphDataView.as_view(), name='graph-data'),
    path('tags/', TagsView.as_view(), name='tags-list'),
    path('tags/<str:tag_name>/', TagItemsView.as_view(), name='tag-items'),
    path('<str:item_type>/<str:item_id>/', ItemDetailView.as_view(), name='item-detail'),
]