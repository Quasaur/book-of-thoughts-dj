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
        topic_data = neo4j_service.get_item_by_id(topic_id, 'TOPIC')
        if not topic_data:
            return JsonResponse({'error': 'Topic not found'}, status=404)
        
        # Get the DESCRIPTION node and notes for this topic
        detail_query = """
        MATCH (t:TOPIC {name: $topic_id})
        OPTIONAL MATCH (t)-[r:HAS_DESCRIPTION]->(d:DESCRIPTION)
        RETURN t.notes as notes, 
               d.en_content as en_content,
               d.es_content as es_content, 
               d.fr_content as fr_content,
               d.hi_content as hi_content,
               d.zh_content as zh_content,
               d.cn_content as cn_content,
               d.ch_content as ch_content,
               d.name as description_id,
               d,
               r,
               t
        """
        detail_result = neo4j_service.run_query(detail_query, {"topic_id": topic_id})
        
        # Add notes and description data to topic data
        if detail_result and len(detail_result) > 0:
            detail = detail_result[0]
            logger.info(f"Detail result for {topic_id}: {detail}")
            topic_data['notes'] = detail.get('notes')
            
            # Try multiple possible field names for Chinese content
            chinese_content = detail.get('zh_content') or detail.get('cn_content') or detail.get('ch_content')
            
            topic_data['description_node'] = {
                'en_content': detail.get('en_content'),
                'es_content': detail.get('es_content'),
                'fr_content': detail.get('fr_content'),
                'hi_content': detail.get('hi_content'),
                'zh_content': chinese_content,
                'id': detail.get('description_id'),
                'raw_data': detail.get('d')  # Include raw node data for debugging
            }
        else:
            logger.info(f"No detail result found for {topic_id}")
            topic_data['notes'] = None
            topic_data['description_node'] = None
        
        # Ensure we have basic topic fields from the node data
        if 'n' in topic_data:
            node_data = topic_data['n']
            topic_response = {
                'id': node_data.get('name'),
                'name': node_data.get('name'),
                'alias': node_data.get('alias'),
                'parent': node_data.get('parent'),
                'level': node_data.get('level'),
                'tags': topic_data.get('tags') or [],
                'notes': topic_data.get('notes'),
                'description_node': topic_data.get('description_node')
            }
        else:
            # Fallback if node structure is different
            topic_response = topic_data
            
        return JsonResponse(topic_response, safe=False)
    except Exception as e:
        logger.error(f"Error fetching topic detail: {e}")
        return JsonResponse({'error': str(e)}, status=500)
