"""
Topics views module
Optimized for M1 MacBook with async support and caching
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .models import Topic, TopicTag, TopicSyncLog
from .services import topics_service
from .serializers import TopicSerializer, TopicHierarchySerializer
import logging

logger = logging.getLogger(__name__)


# Web Views (HTML Templates)

class TopicsOverviewView(TemplateView):
    """
    Main topics overview page with table view
    Enhanced version of the original topics_table_view
    """
    template_name = 'topics/overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get query parameters
            search_query = self.request.GET.get('search', '').strip()
            level_filter = self.request.GET.get('level')
            page_num = self.request.GET.get('page', 1)
            
            # Fetch topics
            if search_query:
                topics = topics_service.search_topics(search_query)
                context['search_query'] = search_query
            elif level_filter is not None:
                try:
                    level = int(level_filter)
                    topics = topics_service.get_topics_by_level(level)
                    context['level_filter'] = level
                except ValueError:
                    topics = topics_service.get_all_topics()
            else:
                topics = topics_service.get_all_topics()
            
            # Pagination
            paginator = Paginator(topics, 25)  # 25 topics per page
            page_obj = paginator.get_page(page_num)
            
            context.update({
                'topics': page_obj.object_list,
                'page_obj': page_obj,
                'total_topics': len(topics),
                'paginator': paginator,
            })
            
            # Add level statistics
            all_topics = topics_service.get_all_topics()
            level_stats = {}
            for topic in all_topics:
                level = topic.get('level', 0)
                level_stats[level] = level_stats.get(level, 0) + 1
            
            context['level_stats'] = sorted(level_stats.items())
            
        except Exception as e:
            logger.error(f"Error in TopicsOverviewView: {e}")
            context.update({
                'error': str(e),
                'topics': [],
                'total_topics': 0,
            })
        
        return context


class TopicDetailView(DetailView):
    """
    Detailed view for a single topic
    """
    template_name = 'topics/detail.html'
    context_object_name = 'topic'
    
    def get_object(self, queryset=None):
        topic_id = self.kwargs.get('topic_id')
        slug = self.kwargs.get('slug')
        
        if slug:
            # Try to get from Django model first for slug support
            try:
                django_topic = get_object_or_404(Topic, slug=slug)
                topic_id = django_topic.neo4j_id
            except Topic.DoesNotExist:
                raise Http404("Topic not found")
        
        if not topic_id:
            raise Http404("Topic not found")
        
        topic = topics_service.get_topic_by_id(topic_id)
        if not topic:
            raise Http404("Topic not found")
        
        return topic
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic = self.object
        
        # Get related topics (children and siblings)
        try:
            # Get children
            all_topics = topics_service.get_all_topics()
            children = [t for t in all_topics if t.get('parent') == topic['id']]
            
            # Get siblings (same parent)
            parent_id = topic.get('parent')
            siblings = []
            if parent_id:
                siblings = [t for t in all_topics if t.get('parent') == parent_id and t['id'] != topic['id']]
            
            # Get parent
            parent = None
            if parent_id:
                parent = next((t for t in all_topics if t['id'] == parent_id), None)
            
            context.update({
                'children': children,
                'siblings': siblings,
                'parent': parent,
                'breadcrumbs': self._get_breadcrumbs(topic, all_topics),
            })
            
        except Exception as e:
            logger.error(f"Error getting related topics: {e}")
            context.update({
                'children': [],
                'siblings': [],
                'parent': None,
                'breadcrumbs': [],
            })
        
        return context
    
    def _get_breadcrumbs(self, topic, all_topics):
        """Generate breadcrumb navigation"""
        breadcrumbs = []
        current = topic
        
        while current:
            breadcrumbs.insert(0, current)
            parent_id = current.get('parent')
            if parent_id:
                current = next((t for t in all_topics if t['id'] == parent_id), None)
            else:
                break
        
        return breadcrumbs


class TopicsHierarchyView(TemplateView):
    """
    Interactive hierarchy view of topics
    """
    template_name = 'topics/hierarchy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            root_id = self.request.GET.get('root')
            hierarchy = topics_service.get_topic_hierarchy(root_id)
            context['hierarchy'] = hierarchy
            
        except Exception as e:
            logger.error(f"Error in TopicsHierarchyView: {e}")
            context.update({
                'error': str(e),
                'hierarchy': {'topics': [], 'total_count': 0},
            })
        
        return context


# API Views (JSON Responses)

class TopicsListAPIView(APIView):
    """
    API endpoint for listing topics with filtering and pagination
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Query parameters
            search = request.GET.get('search', '').strip()
            level = request.GET.get('level')
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Fetch topics
            if search:
                topics = topics_service.search_topics(search)
            elif level is not None:
                try:
                    level_int = int(level)
                    topics = topics_service.get_topics_by_level(level_int)
                except ValueError:
                    topics = topics_service.get_all_topics()
            else:
                topics = topics_service.get_all_topics()
            
            # Pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_topics = topics[start_idx:end_idx]
            
            return Response({
                'results': paginated_topics,
                'count': len(topics),
                'page': page,
                'page_size': page_size,
                'total_pages': (len(topics) + page_size - 1) // page_size,
            })
            
        except Exception as e:
            logger.error(f"Error in TopicsListAPIView: {e}")
            return Response(
                {'error': 'Failed to fetch topics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopicDetailAPIView(APIView):
    """
    API endpoint for topic details
    """
    permission_classes = [AllowAny]
    
    def get(self, request, topic_id):
        try:
            topic = topics_service.get_topic_by_id(topic_id)
            if not topic:
                return Response(
                    {'error': 'Topic not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(topic)
            
        except Exception as e:
            logger.error(f"Error in TopicDetailAPIView: {e}")
            return Response(
                {'error': 'Failed to fetch topic'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopicsHierarchyAPIView(APIView):
    """
    API endpoint for topic hierarchy
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            root_id = request.GET.get('root')
            hierarchy = topics_service.get_topic_hierarchy(root_id)
            
            return Response(hierarchy)
            
        except Exception as e:
            logger.error(f"Error in TopicsHierarchyAPIView: {e}")
            return Response(
                {'error': 'Failed to fetch hierarchy'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopicsSyncAPIView(APIView):
    """
    API endpoint for syncing topics from Neo4j
    """
    permission_classes = [AllowAny]  # Consider adding proper permissions
    
    def post(self, request):
        try:
            force = request.data.get('force', False)
            success, message, count = topics_service.sync_topics_from_neo4j(force=force)
            
            return Response({
                'success': success,
                'message': message,
                'records_processed': count,
            }, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in TopicsSyncAPIView: {e}")
            return Response(
                {'error': 'Sync failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Utility views

@api_view(['GET'])
@permission_classes([AllowAny])
def topics_stats_view(request):
    """
    Get topics statistics
    """
    try:
        all_topics = topics_service.get_all_topics()
        
        # Calculate statistics
        total_count = len(all_topics)
        level_counts = {}
        tag_counts = {}
        
        for topic in all_topics:
            level = topic.get('level', 0)
            level_counts[level] = level_counts.get(level, 0) + 1
            
            tags = topic.get('tags', [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get sync logs
        recent_syncs = TopicSyncLog.objects.filter(
            success=True
        ).order_by('-completed_at')[:5]
        
        sync_history = []
        for sync in recent_syncs:
            sync_history.append({
                'type': sync.sync_type,
                'completed_at': sync.completed_at,
                'records_processed': sync.records_processed,
            })
        
        # Cache stats
        cache_stats = topics_service.get_cache_stats()
        
        return Response({
            'total_topics': total_count,
            'level_distribution': level_counts,
            'top_tags': sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'recent_syncs': sync_history,
            'cache_stats': cache_stats,
        })
        
    except Exception as e:
        logger.error(f"Error in topics_stats_view: {e}")
        return Response(
            {'error': 'Failed to fetch statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Backwards compatibility function
def topics_table_view(request):
    """
    Backwards compatibility wrapper for the original topics_table_view
    Redirects to the new TopicsOverviewView
    """
    view = TopicsOverviewView.as_view()
    return view(request)
