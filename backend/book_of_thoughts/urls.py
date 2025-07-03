from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views, test_views
from thoughts_api.views import topics_table_view

urlpatterns = [
    path('', views.index, name='index'),
    path('test/', test_views.test, name='test'),
    path('admin/', admin.site.urls),
    path('api/', include('thoughts_api.urls')),
    path('graph/', include('graph_app.urls')),
    path('topics/', topics_table_view, name='topics-table'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
