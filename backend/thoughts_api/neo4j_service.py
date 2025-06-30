from neo4j import GraphDatabase
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def run_query(self, query, parameters=None):
        """Execute a Cypher query and return results"""
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            raise
    
    def get_all_thoughts(self, skip=0, limit=20):
        """Get all thoughts with pagination"""
        query = """
        MATCH (t:THOUGHT)
        OPTIONAL MATCH (t)-[:HAS_CONTENT]->(c:CONTENT)
        RETURN t.id as ID, t.name as Name, t.parent as Parent, t.tags as Tags, 
               t.level as Level
        ORDER BY t.name DESC
        """
        return self.run_query(query, {"skip": skip, "limit": limit})
    
    def get_all_topics(self, skip=0, limit=20):
        """Get all topics with pagination"""
        query = """
        MATCH (t:TOPIC)
        OPTIONAL MATCH (t)-[:HAS_THOUGHT]->(thought:THOUGHT)
        OPTIONAL MATCH (t)-[:HAS_DESCRIPTION]->(desc:DESCRIPTION)
        RETURN t.name as id, t.alias as title, t.notes as description,
               t.level as level, t.parent as parent,
               count(DISTINCT thought) as thought_count,
               t.tags as tags,
               desc.en_content as en_description
        ORDER BY t.level ASC, t.name ASC
        SKIP $skip LIMIT $limit
        """
        return self.run_query(query, {"skip": skip, "limit": limit})
    
    def get_all_quotes(self, skip=0, limit=20):
        """Get all quotes with pagination"""
        query = """
        MATCH (q:QUOTE)
        OPTIONAL MATCH (q)-[:HAS_CONTENT]->(content:CONTENT)
        OPTIONAL MATCH (q)<-[:HAS_CHILD]-(parent:TOPIC)
        RETURN q.name as id, q.alias as title, content.en_content as content,
               q.author as author, q.source as source,
               q.level as level, q.parent as parent,
               q.tags as tags,
               parent.name as parent_topic
        ORDER BY q.name ASC
        SKIP $skip LIMIT $limit
        """
        return self.run_query(query, {"skip": skip, "limit": limit})
    
    def get_all_passages(self, skip=0, limit=20):
        """Get all Bible passages with pagination"""
        query = """
        MATCH (p:PASSAGE)
        OPTIONAL MATCH (p)-[:HAS_CONTENT]->(content:CONTENT)
        OPTIONAL MATCH (p)<-[:HAS_CHILD]-(parent:TOPIC)
        RETURN p.name as id, p.alias as title, content.en_content as content,
               p.book as book, p.chapter as chapter, p.verse as verse,
               p.level as level, p.parent as parent,
               p.tags as tags,
               parent.name as parent_topic
        ORDER BY p.book, p.chapter, p.verse
        SKIP $skip LIMIT $limit
        """
        return self.run_query(query, {"skip": skip, "limit": limit})
    
    def get_item_by_id(self, item_id, node_type):
        """Get a specific item by ID and type"""
        query = f"""
        MATCH (n:{node_type} {{name: $item_id}})
        OPTIONAL MATCH (n)-[:HAS_CONTENT]->(content:CONTENT)
        OPTIONAL MATCH (n)-[:HAS_DESCRIPTION]->(desc:DESCRIPTION)
        OPTIONAL MATCH (n)-[:HAS_CHILD]->(child)
        OPTIONAL MATCH (n)<-[:HAS_CHILD]-(parent)
        RETURN n, 
               content.en_content as content,
               desc.en_content as description,
               n.tags as tags,
               collect(DISTINCT {{name: child.name, alias: child.alias, type: labels(child)[0]}}) as children,
               parent.name as parent_name,
               parent.alias as parent_alias
        """
        result = self.run_query(query, {"item_id": item_id})
        return result[0] if result else None
    
    def search_content(self, search_term, skip=0, limit=20):
        """Search across all content types"""
        query = """
        CALL {
            MATCH (t:THOUGHT)
            OPTIONAL MATCH (t)-[:HAS_CONTENT]->(c:CONTENT)
            WHERE toLower(t.alias) CONTAINS toLower($term) 
               OR toLower(t.name) CONTAINS toLower($term)
               OR toLower(c.en_content) CONTAINS toLower($term)
               OR ANY(tag IN t.tags WHERE toLower(tag) CONTAINS toLower($term))
            RETURN t.name as id, t.alias as title, c.en_content as content,
                   'THOUGHT' as type, t.level as level, t.tags as tags
            UNION
            MATCH (t:TOPIC)
            OPTIONAL MATCH (t)-[:HAS_DESCRIPTION]->(d:DESCRIPTION)
            WHERE toLower(t.alias) CONTAINS toLower($term) 
               OR toLower(t.name) CONTAINS toLower($term)
               OR toLower(d.en_content) CONTAINS toLower($term)
               OR ANY(tag IN t.tags WHERE toLower(tag) CONTAINS toLower($term))
            RETURN t.name as id, t.alias as title, d.en_content as content,
                   'TOPIC' as type, t.level as level, t.tags as tags
            UNION
            MATCH (q:QUOTE)
            OPTIONAL MATCH (q)-[:HAS_CONTENT]->(c:CONTENT)
            WHERE toLower(q.alias) CONTAINS toLower($term) 
               OR toLower(q.name) CONTAINS toLower($term)
               OR toLower(c.en_content) CONTAINS toLower($term)
               OR ANY(tag IN q.tags WHERE toLower(tag) CONTAINS toLower($term))
            RETURN q.name as id, q.alias as title, c.en_content as content,
                   'QUOTE' as type, q.level as level, q.tags as tags
            UNION
            MATCH (p:PASSAGE)
            OPTIONAL MATCH (p)-[:HAS_CONTENT]->(c:CONTENT)
            WHERE toLower(p.alias) CONTAINS toLower($term) 
               OR toLower(p.name) CONTAINS toLower($term)
               OR toLower(c.en_content) CONTAINS toLower($term)
               OR ANY(tag IN p.tags WHERE toLower(tag) CONTAINS toLower($term))
            RETURN p.name as id, p.alias as title, c.en_content as content,
                   'PASSAGE' as type, p.level as level, p.tags as tags
        }
        RETURN id, title, content, type, level, tags
        ORDER BY level ASC, title ASC
        SKIP $skip LIMIT $limit
        """
        return self.run_query(query, {"term": search_term, "skip": skip, "limit": limit})
    
    def get_graph_data(self, node_id=None, node_type=None):
        """Get graph data for visualization"""
        if node_id and node_type:
            # Get focused graph around specific node
            query = f"""
            MATCH (center:{node_type} {{name: $node_id}})
            OPTIONAL MATCH (center)-[r1]-(connected)
            OPTIONAL MATCH (connected)-[r2]-(secondLevel)
            WHERE distance(center, secondLevel) <= 2
            WITH collect(DISTINCT center) + collect(DISTINCT connected) + collect(DISTINCT secondLevel) as nodes,
                 collect(DISTINCT r1) + collect(DISTINCT r2) as relationships
            UNWIND nodes as n
            UNWIND relationships as r
            RETURN collect(DISTINCT {{
                id: n.name, 
                title: n.alias, 
                type: labels(n)[0],
                level: n.level,
                tags: n.tags,
                group: CASE labels(n)[0]
                    WHEN 'TOPIC' THEN 1
                    WHEN 'THOUGHT' THEN 2
                    WHEN 'QUOTE' THEN 3
                    WHEN 'PASSAGE' THEN 4
                    WHEN 'CONTENT' THEN 5
                    WHEN 'DESCRIPTION' THEN 6
                    ELSE 7
                END
            }}) as nodes,
            collect(DISTINCT {{
                source: startNode(r).name,
                target: endNode(r).name,
                type: type(r)
            }}) as links
            """
            return self.run_query(query, {"node_id": node_id})
        else:
            # Get overall graph structure
            query = """
            MATCH (n)
            WHERE n:TOPIC OR n:THOUGHT OR n:QUOTE OR n:PASSAGE OR n:CONTENT OR n:DESCRIPTION
            OPTIONAL MATCH (n)-[r]-(m)
            WHERE m:TOPIC OR m:THOUGHT OR m:QUOTE OR m:PASSAGE OR m:CONTENT OR m:DESCRIPTION
            WITH collect(DISTINCT n) + collect(DISTINCT m) as allNodes, collect(DISTINCT r) as allRels
            UNWIND allNodes as node
            UNWIND allRels as rel
            RETURN collect(DISTINCT {
                id: node.name, 
                title: node.alias, 
                type: labels(node)[0],
                level: node.level,
                tags: node.tags,
                group: CASE labels(node)[0]
                    WHEN 'TOPIC' THEN 1
                    WHEN 'THOUGHT' THEN 2
                    WHEN 'QUOTE' THEN 3
                    WHEN 'PASSAGE' THEN 4
                    WHEN 'CONTENT' THEN 5
                    WHEN 'DESCRIPTION' THEN 6
                    ELSE 7
                END
            }) as nodes,
            collect(DISTINCT {
                source: startNode(rel).name,
                target: endNode(rel).name,
                type: type(rel)
            }) as links
            LIMIT 500
            """
            return self.run_query(query)
    
    def get_tags(self):
        """Get all tags with usage count"""
        query = """
        MATCH (n) WHERE n.tags IS NOT NULL RETURN n.tags AS allTags
        """
        return self.run_query(query)
    
    def get_items_by_tag(self, tag_name, skip=0, limit=20):
        """Get all items with a specific tag (using node properties)"""
        query = """
        MATCH (item)
        WHERE item.tags IS NOT NULL AND $tag_name IN item.tags
        AND (labels(item)[0] = 'TOPIC' OR labels(item)[0] = 'THOUGHT' OR labels(item)[0] = 'QUOTE' OR labels(item)[0] = 'PASSAGE')
        OPTIONAL MATCH (item)-[:HAS_CONTENT]->(content:CONTENT)
        OPTIONAL MATCH (item)-[:HAS_DESCRIPTION]->(desc:DESCRIPTION)
        RETURN item.name as id, item.alias as title, 
               CASE 
                   WHEN content.en_content IS NOT NULL THEN content.en_content
                   WHEN desc.en_content IS NOT NULL THEN desc.en_content
                   WHEN item.notes IS NOT NULL THEN item.notes
                   ELSE ''
               END as content,
               labels(item)[0] as type,
               item.level as level,
               item.tags as tags
        ORDER BY item.level ASC, item.name ASC
        SKIP $skip LIMIT $limit
        """
        return self.run_query(query, {"tag_name": tag_name, "skip": skip, "limit": limit})

# Global service instance
neo4j_service = Neo4jService()