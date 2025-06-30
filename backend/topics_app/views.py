from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from thoughts_api.neo4j_service import neo4j_service
import logging

logger = logging.getLogger(__name__)

def topics_view(request):
    """Render the dedicated topics page"""
    return render(request, 'topics_app/topics.html')

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

def topics_data_api(request):
    """API endpoint for topics data - separate from thoughts_api"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        skip = (page - 1) * page_size
        
        topics = neo4j_service.get_all_topics(skip=skip, limit=page_size)
        
        # Format the data for the table view
        formatted_topics = []
        for topic in topics:
            formatted_topics.append({
                'id': topic.get('id'),
                'name': topic.get('id'),  # Using id as name since that's the actual name field
                'alias': topic.get('title'),  # This is actually the alias field
                'parent': topic.get('parent'),
                'level': topic.get('level'),
                'tags': topic.get('tags') or [],
                'notes': topic.get('description'),  # This is the notes field
                'description_content': topic.get('en_description')  # Description node content
            })
        
        return JsonResponse({
            'results': formatted_topics,
            'page': page,
            'page_size': page_size
        }, safe=False)
    except Exception as e:
        logger.error(f"Error fetching topics: {e}")
        return JsonResponse({'error': 'Failed to fetch topics'}, status=500)

def topic_detail(request, topic_id):
    """Get detailed information about a specific topic including DESCRIPTION node"""
    try:
        # Get the topic data
        topic_data = neo4j_service.get_item_by_id(topic_id, 'Topic')
        if not topic_data:
            return JsonResponse({'error': 'Topic not found'}, status=404)
        
        # Get the DESCRIPTION node and notes for this topic
        detail_query = """
        MATCH (t:TOPIC {name: $topic_id})
        OPTIONAL MATCH (t)-[:HAS_DESCRIPTION]->(d:DESCRIPTION)
        RETURN t.notes as notes, d.en_content as description_content, d.name as description_id
        """
        detail_result = neo4j_service.run_query(detail_query, {"topic_id": topic_id})
        
        # Add notes and description data to topic data
        if detail_result and len(detail_result) > 0:
            detail = detail_result[0]
            topic_data['notes'] = detail.get('notes')
            topic_data['description_node'] = {
                'content': detail.get('description_content'),
                'id': detail.get('description_id')
            }
        else:
            topic_data['notes'] = None
            topic_data['description_node'] = None
            
        return JsonResponse(topic_data, safe=False)
    except Exception as e:
        logger.error(f"Error fetching topic detail: {e}")
        return JsonResponse({'error': str(e)}, status=500)
