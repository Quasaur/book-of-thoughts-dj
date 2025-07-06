"""
Topics serializers for Django REST Framework
Optimized for M1 MacBook performance
"""

from rest_framework import serializers
from .models import Topic, TopicTag, TopicSyncLog


class TopicTagSerializer(serializers.ModelSerializer):
    """Serializer for topic tags"""
    
    class Meta:
        model = TopicTag
        fields = ['tag', 'created_at']


class TopicSerializer(serializers.ModelSerializer):
    """
    Serializer for Topic model with additional computed fields
    """
    tags = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()
    is_root = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = [
            'id', 'neo4j_id', 'title', 'description', 'level', 'parent_id',
            'slug', 'meta_description', 'is_active',
            'created_at', 'updated_at', 'last_synced',
            'tags', 'children_count', 'absolute_url', 'is_root'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_synced']
    
    def get_tags(self, obj):
        """Get list of tag names"""
        return [tag.tag for tag in obj.topic_tags.all()]
    
    def get_children_count(self, obj):
        """Get count of child topics"""
        # This would require a separate query to Neo4j or caching
        # For now, return 0 as placeholder
        return 0
    
    def get_absolute_url(self, obj):
        """Get absolute URL for this topic"""
        return obj.get_absolute_url()
    
    def get_is_root(self, obj):
        """Check if this is a root topic"""
        return obj.is_root_topic


class TopicHierarchySerializer(serializers.Serializer):
    """
    Serializer for hierarchical topic data from Neo4j
    """
    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    level = serializers.IntegerField()
    parent = serializers.CharField(allow_null=True, required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    children = serializers.ListField(required=False)
    has_children = serializers.BooleanField(default=False)
    is_root = serializers.BooleanField(default=False)
    display_title = serializers.CharField(required=False)
    short_description = serializers.CharField(required=False)
    
    def to_representation(self, instance):
        """
        Custom serialization for nested hierarchy
        """
        data = super().to_representation(instance)
        
        # Recursively serialize children
        if 'children' in instance and instance['children']:
            children_serializer = TopicHierarchySerializer(
                instance['children'], 
                many=True, 
                context=self.context
            )
            data['children'] = children_serializer.data
        
        return data


class TopicSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for sync log entries"""
    
    duration = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = TopicSyncLog
        fields = [
            'id', 'sync_type', 'started_at', 'completed_at',
            'success', 'records_processed', 'error_message',
            'duration', 'status'
        ]
    
    def get_duration(self, obj):
        """Calculate sync duration in seconds"""
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return delta.total_seconds()
        return None
    
    def get_status(self, obj):
        """Get human-readable status"""
        if obj.completed_at is None:
            return 'Running'
        elif obj.success:
            return 'Success'
        else:
            return 'Failed'


class TopicCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new topics (primarily for Neo4j)
    """
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, required=False)
    parent_id = serializers.CharField(allow_blank=True, required=False)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    
    def validate_title(self, value):
        """Validate topic title"""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_tags(self, value):
        """Validate and clean tags"""
        if value:
            # Remove duplicates and clean whitespace
            cleaned_tags = list(set(tag.strip().lower() for tag in value if tag.strip()))
            return cleaned_tags
        return []


class TopicUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating existing topics
    """
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    is_active = serializers.BooleanField(required=False)
    
    def validate_title(self, value):
        """Validate topic title"""
        if value is not None and not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip() if value else value
    
    def validate_tags(self, value):
        """Validate and clean tags"""
        if value is not None:
            # Remove duplicates and clean whitespace
            cleaned_tags = list(set(tag.strip().lower() for tag in value if tag.strip()))
            return cleaned_tags
        return value


class TopicStatsSerializer(serializers.Serializer):
    """
    Serializer for topic statistics
    """
    total_topics = serializers.IntegerField()
    level_distribution = serializers.DictField()
    top_tags = serializers.ListField()
    recent_syncs = serializers.ListField()
    cache_stats = serializers.DictField()


class TopicSearchSerializer(serializers.Serializer):
    """
    Serializer for topic search results
    """
    query = serializers.CharField()
    results = TopicHierarchySerializer(many=True)
    total_results = serializers.IntegerField()
    search_time = serializers.FloatField(required=False)