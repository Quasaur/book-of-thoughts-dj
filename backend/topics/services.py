"""
Topics service module for Neo4j integration and business logic
Optimized for M1 MacBook performance
"""

from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from thoughts_api.neo4j_service import neo4j_service
from .models import Topic, TopicTag, TopicSyncLog
import logging

logger = logging.getLogger(__name__)


class TopicsService:
    """
    Service class for managing topics with Neo4j and Django integration
    Provides caching, sync, and enhanced query capabilities
    """
    
    CACHE_TIMEOUT = 300  # 5 minutes
    CACHE_PREFIX = 'topics:'
    
    def __init__(self):
        self.neo4j = neo4j_service
    
    def get_all_topics(self, use_cache: bool = True, sync_if_missing: bool = True) -> List[Dict]:
        """
        Get all topics with intelligent caching
        
        Args:
            use_cache: Whether to use Redis/Django cache
            sync_if_missing: Whether to sync from Neo4j if cache is empty
            
        Returns:
            List of topic dictionaries
        """
        cache_key = f"{self.CACHE_PREFIX}all"
        
        if use_cache:
            cached_topics = cache.get(cache_key)
            if cached_topics:
                logger.debug("Returning cached topics")
                return cached_topics
        
        try:
            # Get from Neo4j
            topics = self.neo4j.get_all_topics()
            
            # Enhanced topic data with additional processing
            enhanced_topics = []
            for topic in topics:
                enhanced_topic = self._enhance_topic_data(topic)
                enhanced_topics.append(enhanced_topic)
            
            # Cache the results
            if use_cache:
                cache.set(cache_key, enhanced_topics, self.CACHE_TIMEOUT)
                logger.debug(f"Cached {len(enhanced_topics)} topics")
            
            # Optionally sync to Django models for additional features
            if sync_if_missing:
                self._sync_topics_to_django(enhanced_topics, sync_type='incremental')
            
            return enhanced_topics
            
        except Exception as e:
            logger.error(f"Error fetching topics: {e}")
            # Fallback to Django models if Neo4j fails
            return self._get_topics_from_django()
    
    def get_topic_by_id(self, topic_id: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Get a specific topic by ID
        
        Args:
            topic_id: Topic identifier
            use_cache: Whether to use caching
            
        Returns:
            Topic dictionary or None
        """
        cache_key = f"{self.CACHE_PREFIX}detail:{topic_id}"
        
        if use_cache:
            cached_topic = cache.get(cache_key)
            if cached_topic:
                return cached_topic
        
        try:
            topic = self.neo4j.get_item_by_id(topic_id, 'TOPIC')
            if topic:
                enhanced_topic = self._enhance_topic_data(topic)
                
                if use_cache:
                    cache.set(cache_key, enhanced_topic, self.CACHE_TIMEOUT)
                
                return enhanced_topic
            
        except Exception as e:
            logger.error(f"Error fetching topic {topic_id}: {e}")
            
        return None
    
    def get_topics_by_level(self, level: int, use_cache: bool = True) -> List[Dict]:
        """
        Get topics filtered by hierarchical level
        
        Args:
            level: Topic level (0 = root, 1 = first level, etc.)
            use_cache: Whether to use caching
            
        Returns:
            List of topic dictionaries
        """
        cache_key = f"{self.CACHE_PREFIX}level:{level}"
        
        if use_cache:
            cached_topics = cache.get(cache_key)
            if cached_topics:
                return cached_topics
        
        all_topics = self.get_all_topics(use_cache=use_cache)
        level_topics = [t for t in all_topics if t.get('level') == level]
        
        if use_cache:
            cache.set(cache_key, level_topics, self.CACHE_TIMEOUT)
        
        return level_topics
    
    def search_topics(self, query: str, use_cache: bool = True) -> List[Dict]:
        """
        Search topics by title, description, or tags
        
        Args:
            query: Search query
            use_cache: Whether to use caching
            
        Returns:
            List of matching topic dictionaries
        """
        cache_key = f"{self.CACHE_PREFIX}search:{query.lower()}"
        
        if use_cache:
            cached_results = cache.get(cache_key)
            if cached_results:
                return cached_results
        
        try:
            # Use Neo4j search functionality
            results = self.neo4j.search_content(query)
            topic_results = [r for r in results if r.get('type') == 'TOPIC']
            
            enhanced_results = []
            for topic in topic_results:
                enhanced_topic = self._enhance_topic_data(topic)
                enhanced_results.append(enhanced_topic)
            
            if use_cache:
                cache.set(cache_key, enhanced_results, self.CACHE_TIMEOUT // 2)  # Shorter cache for search
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error searching topics: {e}")
            return []
    
    def get_topic_hierarchy(self, root_id: Optional[str] = None) -> Dict:
        """
        Get hierarchical topic structure
        
        Args:
            root_id: Starting point (None for full hierarchy)
            
        Returns:
            Nested dictionary representing topic hierarchy
        """
        all_topics = self.get_all_topics()
        
        if root_id:
            # Filter to specific subtree
            root_topic = next((t for t in all_topics if t['id'] == root_id), None)
            if not root_topic:
                return {}
            topics = [t for t in all_topics if t['id'] == root_id or t.get('parent') == root_id]
        else:
            topics = all_topics
        
        return self._build_hierarchy(topics)
    
    def sync_topics_from_neo4j(self, force: bool = False) -> Tuple[bool, str, int]:
        """
        Sync topics from Neo4j to Django models
        
        Args:
            force: Force full sync even if recent sync exists
            
        Returns:
            Tuple of (success, message, records_processed)
        """
        sync_log = TopicSyncLog.objects.create(sync_type='full')
        
        try:
            # Check if recent sync exists
            if not force:
                recent_sync = TopicSyncLog.objects.filter(
                    sync_type='full',
                    success=True,
                    started_at__gte=timezone.now() - timezone.timedelta(hours=1)
                ).first()
                
                if recent_sync:
                    sync_log.mark_completed(False, 0, "Recent sync exists, use force=True to override")
                    return False, "Recent sync exists", 0
            
            # Get all topics from Neo4j
            neo4j_topics = self.neo4j.get_all_topics()
            records_processed = 0
            
            for topic_data in neo4j_topics:
                try:
                    self._sync_single_topic(topic_data)
                    records_processed += 1
                except Exception as e:
                    logger.error(f"Error syncing topic {topic_data.get('id')}: {e}")
            
            # Clear cache after sync
            self.clear_cache()
            
            sync_log.mark_completed(True, records_processed)
            return True, f"Successfully synced {records_processed} topics", records_processed
            
        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            sync_log.mark_completed(False, 0, error_msg)
            logger.error(error_msg)
            return False, error_msg, 0
    
    def clear_cache(self):
        """Clear all topics-related cache"""
        cache_keys = [
            f"{self.CACHE_PREFIX}all",
            f"{self.CACHE_PREFIX}hierarchy",
        ]
        
        # Clear specific level caches (0-10 levels should be enough)
        for level in range(11):
            cache_keys.append(f"{self.CACHE_PREFIX}level:{level}")
        
        cache.delete_many(cache_keys)
        logger.info("Cleared topics cache")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics for monitoring"""
        stats = {
            'cache_timeout': self.CACHE_TIMEOUT,
            'cache_prefix': self.CACHE_PREFIX,
        }
        
        # Check if main cache keys exist
        main_keys = [
            f"{self.CACHE_PREFIX}all",
            f"{self.CACHE_PREFIX}hierarchy",
        ]
        
        for key in main_keys:
            stats[key.replace(self.CACHE_PREFIX, '')] = cache.get(key) is not None
        
        return stats
    
    # Private methods
    
    def _enhance_topic_data(self, topic: Dict) -> Dict:
        """
        Enhance topic data with additional computed fields
        
        Args:
            topic: Raw topic data from Neo4j
            
        Returns:
            Enhanced topic dictionary
        """
        enhanced = topic.copy()
        
        # Add computed fields
        enhanced['is_root'] = enhanced.get('level', 0) == 0
        enhanced['has_children'] = False  # Will be computed in hierarchy building
        
        # Format tags
        tags = enhanced.get('tags', [])
        if isinstance(tags, str):
            tags = [tags] if tags else []
        enhanced['tags'] = tags
        
        # Add display title
        enhanced['display_title'] = enhanced.get('title') or enhanced.get('id', 'Untitled')
        
        # Add short description
        description = enhanced.get('description', '') or enhanced.get('en_description', '')
        if description and len(description) > 150:
            enhanced['short_description'] = description[:147] + '...'
        else:
            enhanced['short_description'] = description
        
        return enhanced
    
    def _get_topics_from_django(self) -> List[Dict]:
        """Fallback method to get topics from Django models"""
        try:
            topics = Topic.objects.active().values(
                'neo4j_id', 'title', 'description', 'level', 'parent_id',
                'slug', 'created_at', 'updated_at'
            )
            
            result = []
            for topic in topics:
                # Convert to format similar to Neo4j
                result.append({
                    'id': topic['neo4j_id'],
                    'title': topic['title'],
                    'description': topic['description'],
                    'level': topic['level'],
                    'parent': topic['parent_id'],
                    'slug': topic['slug'],
                    'tags': [],  # Would need to fetch separately
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching from Django models: {e}")
            return []
    
    def _sync_single_topic(self, topic_data: Dict):
        """Sync a single topic to Django model"""
        neo4j_id = topic_data.get('id')
        if not neo4j_id:
            return
        
        topic, created = Topic.objects.update_or_create(
            neo4j_id=neo4j_id,
            defaults={
                'title': topic_data.get('title', ''),
                'description': topic_data.get('description', '') or topic_data.get('en_description', ''),
                'level': topic_data.get('level', 0),
                'parent_id': topic_data.get('parent'),
                'last_synced': timezone.now(),
            }
        )
        
        # Sync tags
        tags = topic_data.get('tags', [])
        if isinstance(tags, str):
            tags = [tags] if tags else []
        
        # Clear existing tags and add new ones
        TopicTag.objects.filter(topic=topic).delete()
        for tag in tags:
            TopicTag.objects.create(topic=topic, tag=tag)
        
        return topic
    
    def _build_hierarchy(self, topics: List[Dict]) -> Dict:
        """Build hierarchical structure from flat topic list"""
        # Create lookup tables
        topics_by_id = {t['id']: t.copy() for t in topics}
        children_by_parent = {}
        
        # Group children by parent
        for topic in topics:
            parent_id = topic.get('parent')
            if parent_id and parent_id in topics_by_id:
                if parent_id not in children_by_parent:
                    children_by_parent[parent_id] = []
                children_by_parent[parent_id].append(topic['id'])
        
        # Add children to topics and mark parents
        for topic_id, topic in topics_by_id.items():
            children_ids = children_by_parent.get(topic_id, [])
            topic['children'] = [topics_by_id[child_id] for child_id in children_ids if child_id in topics_by_id]
            topic['has_children'] = len(topic['children']) > 0
            
            # Recursively build children
            if topic['children']:
                for child in topic['children']:
                    child['children'] = self._get_topic_children(child['id'], topics_by_id, children_by_parent)
        
        # Return root topics
        root_topics = [t for t in topics_by_id.values() if not t.get('parent') or t.get('parent') not in topics_by_id]
        
        return {
            'topics': root_topics,
            'total_count': len(topics),
            'root_count': len(root_topics),
        }
    
    def _get_topic_children(self, topic_id: str, topics_by_id: Dict, children_by_parent: Dict) -> List[Dict]:
        """Recursively get children for a topic"""
        children_ids = children_by_parent.get(topic_id, [])
        children = []
        
        for child_id in children_ids:
            if child_id in topics_by_id:
                child = topics_by_id[child_id].copy()
                child['children'] = self._get_topic_children(child_id, topics_by_id, children_by_parent)
                children.append(child)
        
        return children


# Global service instance
topics_service = TopicsService()