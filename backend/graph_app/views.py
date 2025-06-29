from django.shortcuts import render
from django.http import JsonResponse
from thoughts_api.neo4j_service import neo4j_service

def graph_view(request):
    """Render the dedicated graph visualization page"""
    return render(request, 'graph_app/graph.html')

def graph_data_api(request):
    """API endpoint for graph data - separate from thoughts_api"""
    try:
        graph_data = neo4j_service.get_graph_data()
        return JsonResponse(graph_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def graph_node_detail(request, node_id):
    """Get detailed information about a specific node"""
    try:
        # You can add specific node detail logic here
        node_data = neo4j_service.get_graph_data(node_id=node_id, node_type='TOPIC')
        return JsonResponse(node_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
