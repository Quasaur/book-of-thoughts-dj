from django.shortcuts import render

def index(request):
    """Render the main React-based frontend"""
    return render(request, 'index.html')