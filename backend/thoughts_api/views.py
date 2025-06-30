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

