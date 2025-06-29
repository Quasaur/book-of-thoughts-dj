from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from .neo4j_service import neo4j_service
import logging

logger = logging.getLogger(__name__)

class ThoughtsListView(APIView):
    """API view for listing thoughts"""
    
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            skip = (page - 1) * page_size
            
            thoughts = neo4j_service.get_all_thoughts(skip=skip, limit=page_size)
            
            return Response({
                'results': thoughts,
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f"Error fetching thoughts: {e}")
            return Response(
                {'error': 'Failed to fetch thoughts'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TopicsListView(APIView):
    """API view for listing topics"""
    
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            skip = (page - 1) * page_size
            
            topics = neo4j_service.get_all_topics(skip=skip, limit=page_size)
            
            return Response({
                'results': topics,
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f"Error fetching topics: {e}")
            return Response(
                {'error': 'Failed to fetch topics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class QuotesListView(APIView):
    """API view for listing quotes"""
    
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            skip = (page - 1) * page_size
            
            quotes = neo4j_service.get_all_quotes(skip=skip, limit=page_size)
            
            return Response({
                'results': quotes,
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return Response(
                {'error': 'Failed to fetch quotes'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PassagesListView(APIView):
    """API view for listing Bible passages"""
    
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            skip = (page - 1) * page_size
            
            passages = neo4j_service.get_all_passages(skip=skip, limit=page_size)
            
            return Response({
                'results': passages,
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f"Error fetching passages: {e}")
            return Response(
                {'error': 'Failed to fetch passages'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ItemDetailView(APIView):
    """API view for getting specific items by ID and type"""
    
    def get(self, request, item_type, item_id):
        try:
            # Validate item type
            valid_types = ['Thought', 'Topic', 'Quote', 'Passage']
            if item_type not in valid_types:
                return Response(
                    {'error': 'Invalid item type'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item = neo4j_service.get_item_by_id(item_id, item_type)
            
            if not item:
                raise Http404("Item not found")
            
            return Response(item)
        except Http404:
            return Response(
                {'error': 'Item not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error fetching item: {e}")
            return Response(
                {'error': 'Failed to fetch item'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SearchView(APIView):
    """API view for searching content"""
    
    def get(self, request):
        try:
            search_term = request.GET.get('q', '').strip()
            if not search_term:
                return Response(
                    {'error': 'Search term is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            skip = (page - 1) * page_size
            
            results = neo4j_service.search_content(
                search_term, 
                skip=skip, 
                limit=page_size
            )
            
            return Response({
                'results': results,
                'search_term': search_term,
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return Response(
                {'error': 'Search failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GraphDataView(APIView):
    """API view for getting graph visualization data"""
    
    def get(self, request):
        try:
            node_id = request.GET.get('node_id')
            node_type = request.GET.get('node_type')
            
            graph_data = neo4j_service.get_graph_data(node_id, node_type)
            
            if graph_data:
                return Response(graph_data[0])
            else:
                return Response({'nodes': [], 'links': []})
        except Exception as e:
            logger.error(f"Error fetching graph data: {e}")
            return Response(
                {'error': 'Failed to fetch graph data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TagsView(APIView):
    """API view for listing tags"""
    
    def get(self, request):
        try:
            tags = neo4j_service.get_tags()
            return Response({'results': tags})
        except Exception as e:
            logger.error(f"Error fetching tags: {e}")
            return Response(
                {'error': 'Failed to fetch tags'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TagItemsView(APIView):
    """API view for getting items by tag"""
    
    def get(self, request, tag_name):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            skip = (page - 1) * page_size
            
            items = neo4j_service.get_items_by_tag(
                tag_name, 
                skip=skip, 
                limit=page_size
            )
            
            return Response({
                'results': items,
                'tag': tag_name,
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f"Error fetching items by tag: {e}")
            return Response(
                {'error': 'Failed to fetch items by tag'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RecentItemsView(APIView):
    """API view for getting recently modified items"""
    
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            skip = (page - 1) * page_size
            
            # Get recent items across all types
            query = """
            CALL {
                MATCH (t:Thought)
                RETURN t.id as id, t.title as title, t.content as content,
                       'Thought' as type, t.last_modified as last_modified
                UNION
                MATCH (t:Topic)
                RETURN t.id as id, t.title as title, t.description as content,
                       'Topic' as type, t.last_modified as last_modified
                UNION
                MATCH (q:Quote)
                RETURN q.id as id, q.title as title, q.content as content,
                       'Quote' as type, q.last_modified as last_modified
                UNION
                MATCH (p:Passage)
                RETURN p.id as id, p.title as title, p.content as content,
                       'Passage' as type, p.last_modified as last_modified
            }
            RETURN id, title, content, type, last_modified
            ORDER BY last_modified DESC
            SKIP $skip LIMIT $limit
            """
            
            recent_items = neo4j_service.run_query(query, {"skip": skip, "limit": page_size})
            
            return Response({
                'results': recent_items,
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f"Error fetching recent items: {e}")
            return Response(
                {'error': 'Failed to fetch recent items'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )