from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Topic, TopicTag, TopicSyncLog


class TopicTagInline(admin.TabularInline):
    """Inline admin for topic tags"""
    model = TopicTag
    extra = 1
    fields = ['tag']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    """Enhanced admin for Topic model"""
    
    list_display = [
        'title', 'level', 'parent_id', 'is_active', 
        'last_synced', 'get_tags_display', 'get_neo4j_link'
    ]
    list_filter = ['level', 'is_active', 'last_synced', 'created_at']
    search_fields = ['title', 'description', 'neo4j_id', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['neo4j_id', 'last_synced', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'meta_description')
        }),
        ('Hierarchy', {
            'fields': ('level', 'parent_id')
        }),
        ('Neo4j Integration', {
            'fields': ('neo4j_id', 'last_synced'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TopicTagInline]
    
    actions = ['sync_from_neo4j', 'mark_active', 'mark_inactive']
    
    def get_tags_display(self, obj):
        """Display tags in admin list"""
        tags = obj.topic_tags.all()[:3]
        tag_list = [tag.tag for tag in tags]
        if obj.topic_tags.count() > 3:
            tag_list.append(f"... (+{obj.topic_tags.count() - 3} more)")
        return ', '.join(tag_list) if tag_list else 'No tags'
    get_tags_display.short_description = 'Tags'
    
    def get_neo4j_link(self, obj):
        """Link to view in Neo4j browser (if available)"""
        if obj.neo4j_id:
            return format_html(
                '<a href="{}" target="_blank">View in Neo4j</a>',
                f"neo4j://localhost:7687/browser/?cmd=match&arg=(n:TOPIC {{name: '{obj.neo4j_id}'}}) return n"
            )
        return 'No Neo4j ID'
    get_neo4j_link.short_description = 'Neo4j'
    
    def sync_from_neo4j(self, request, queryset):
        """Admin action to sync selected topics from Neo4j"""
        from .services import topics_service
        
        success_count = 0
        for topic in queryset:
            try:
                neo4j_data = topics_service.get_topic_by_id(topic.neo4j_id)
                if neo4j_data:
                    # Update topic with fresh data
                    topic.title = neo4j_data.get('title', topic.title)
                    topic.description = neo4j_data.get('description', topic.description)
                    topic.level = neo4j_data.get('level', topic.level)
                    topic.parent_id = neo4j_data.get('parent', topic.parent_id)
                    topic.save()
                    success_count += 1
            except Exception as e:
                self.message_user(request, f"Error syncing {topic.title}: {e}", level='ERROR')
        
        self.message_user(request, f"Successfully synced {success_count} topics from Neo4j")
    sync_from_neo4j.short_description = "Sync selected topics from Neo4j"
    
    def mark_active(self, request, queryset):
        """Mark topics as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Marked {updated} topics as active")
    mark_active.short_description = "Mark selected topics as active"
    
    def mark_inactive(self, request, queryset):
        """Mark topics as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Marked {updated} topics as inactive")
    mark_inactive.short_description = "Mark selected topics as inactive"


@admin.register(TopicTag)
class TopicTagAdmin(admin.ModelAdmin):
    """Admin for topic tags"""
    
    list_display = ['topic', 'tag', 'created_at']
    list_filter = ['tag', 'created_at']
    search_fields = ['topic__title', 'tag']
    raw_id_fields = ['topic']


@admin.register(TopicSyncLog)
class TopicSyncLogAdmin(admin.ModelAdmin):
    """Admin for sync logs"""
    
    list_display = [
        'sync_type', 'started_at', 'completed_at', 'success', 
        'records_processed', 'get_duration'
    ]
    list_filter = ['sync_type', 'success', 'started_at']
    readonly_fields = [
        'sync_type', 'started_at', 'completed_at', 'success',
        'records_processed', 'error_message', 'get_duration'
    ]
    search_fields = ['error_message']
    
    def get_duration(self, obj):
        """Calculate and display sync duration"""
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            seconds = delta.total_seconds()
            if seconds < 60:
                return f"{seconds:.1f} seconds"
            else:
                minutes = seconds / 60
                return f"{minutes:.1f} minutes"
        return "In progress" if not obj.completed_at else "Unknown"
    get_duration.short_description = 'Duration'
    
    def has_add_permission(self, request):
        """Disable manual creation of sync logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make sync logs read-only"""
        return False
