from django.db import models
from django.utils import timezone


class TopicQuerySet(models.QuerySet):
    """Custom QuerySet for Topic model"""
    
    def active(self):
        """Return only active topics"""
        return self.filter(is_active=True)
    
    def by_level(self, level):
        """Filter topics by level"""
        return self.filter(level=level)


class TopicManager(models.Manager):
    """Custom manager for Topic model"""
    
    def get_queryset(self):
        return TopicQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def by_level(self, level):
        return self.get_queryset().by_level(level)


class Topic(models.Model):
    """
    Topic model for caching and additional metadata
    Note: This is used alongside Neo4j for caching and Django-specific features
    """
    
    # Core fields that mirror Neo4j
    neo4j_id = models.CharField(max_length=255, unique=True, db_index=True,
                               help_text="Corresponding Neo4j node ID")
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    level = models.IntegerField(default=0, db_index=True)
    parent_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Additional Django-specific fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced = models.DateTimeField(auto_now=True,
                                      help_text="Last sync with Neo4j")
    
    # SEO and metadata
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    meta_description = models.TextField(blank=True, max_length=160)
    
    # Custom manager
    objects = TopicManager()
    
    class Meta:
        ordering = ['level', 'title']
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'
        indexes = [
            models.Index(fields=['level', 'title']),
            models.Index(fields=['neo4j_id']),
            models.Index(fields=['is_active', 'level']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def is_root_topic(self):
        """Check if this is a root-level topic"""
        return self.level == 0 or not self.parent_id
    
    def get_absolute_url(self):
        """Get the absolute URL for this topic"""
        from django.urls import reverse
        return reverse('topics:detail', kwargs={'slug': self.slug})


class TopicTag(models.Model):
    """Tags for topics (separate model for better performance)"""
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='topic_tags')
    tag = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['topic', 'tag']
        indexes = [
            models.Index(fields=['tag']),
        ]
    
    def __str__(self):
        return f"{self.topic.title} - {self.tag}"


class TopicSyncLog(models.Model):
    """Log for tracking Neo4j sync operations"""
    
    SYNC_TYPES = [
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync'),
        ('single', 'Single Topic Sync'),
    ]
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=False)
    records_processed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.sync_type} sync - {status} - {self.started_at}"
    
    def mark_completed(self, success=True, records_processed=0, error_message=""):
        """Mark the sync as completed"""
        self.completed_at = timezone.now()
        self.success = success
        self.records_processed = records_processed
        self.error_message = error_message
        self.save()
