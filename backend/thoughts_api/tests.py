from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from django.conf import settings
from neo4j.exceptions import ServiceUnavailable, AuthError

from .neo4j_service import Neo4jService


class TestNeo4jService(TestCase):
    
    def setUp(self):
        self.mock_driver = Mock()
        self.mock_session = Mock()
        self.mock_result = Mock()
        
        # Create a proper context manager mock using MagicMock
        self.mock_session_context = MagicMock()
        self.mock_session_context.__enter__ = Mock(return_value=self.mock_session)
        self.mock_session_context.__exit__ = Mock(return_value=None)
        self.mock_driver.session.return_value = self.mock_session_context
        
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_init_creates_driver_with_correct_params(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        
        service = Neo4jService()
        
        mock_driver.assert_called_once_with(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        self.assertEqual(service.driver, self.mock_driver)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_close_calls_driver_close(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        service = Neo4jService()
        
        service.close()
        
        self.mock_driver.close.assert_called_once()
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_close_handles_none_driver(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        service = Neo4jService()
        service.driver = None
        
        service.close()
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_run_query_success(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        mock_record = Mock()
        mock_record.data.return_value = {'id': 1, 'name': 'test'}
        self.mock_session.run.return_value = [mock_record]
        
        service = Neo4jService()
        result = service.run_query("MATCH (n) RETURN n", {"param": "value"})
        
        self.mock_session.run.assert_called_once_with("MATCH (n) RETURN n", {"param": "value"})
        self.assertEqual(result, [{'id': 1, 'name': 'test'}])
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_run_query_with_no_parameters(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        mock_record = Mock()
        mock_record.data.return_value = {'count': 5}
        self.mock_session.run.return_value = [mock_record]
        
        service = Neo4jService()
        result = service.run_query("MATCH (n) RETURN count(n)")
        
        self.mock_session.run.assert_called_once_with("MATCH (n) RETURN count(n)", {})
        self.assertEqual(result, [{'count': 5}])
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    @patch('thoughts_api.neo4j_service.logger')
    def test_run_query_handles_exception(self, mock_logger, mock_driver):
        mock_driver.return_value = self.mock_driver
        self.mock_session.run.side_effect = ServiceUnavailable("Connection failed")
        
        service = Neo4jService()
        
        with self.assertRaises(ServiceUnavailable):
            service.run_query("MATCH (n) RETURN n")
        
        mock_logger.error.assert_called_once_with("Neo4j query error: Connection failed")
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_all_thoughts(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {'ID': 1, 'Name': 'Test Thought', 'Parent': None, 'Tags': ['tag1'], 'Level': 1}
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.get_all_thoughts(skip=10, limit=5)
            
            expected_query = """
        MATCH (t:THOUGHT)
        OPTIONAL MATCH (t)-[:HAS_CONTENT]->(c:CONTENT)
        RETURN t.id as ID, t.name as Name, t.parent as Parent, t.tags as Tags, 
               t.level as Level
        ORDER BY t.name DESC
        """
            mock_run_query.assert_called_once_with(expected_query, {"skip": 10, "limit": 5})
            self.assertEqual(result, expected_result)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_all_topics(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {
                'id': 1, 'title': 'Test Topic', 'description': 'Test description',
                'created_date': '2023-01-01', 'last_modified': '2023-01-02',
                'thought_count': 5, 'tags': ['tag1', 'tag2']
            }
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.get_all_topics(skip=0, limit=10)
            
            expected_query = """
        MATCH (t:Topic)
        OPTIONAL MATCH (t)<-[:BELONGS_TO]-(thought:Thought)
        OPTIONAL MATCH (t)-[:HAS_TAG]->(tag:Tag)
        RETURN t.id as id, t.title as title, t.description as description,
               t.created_date as created_date, t.last_modified as last_modified,
               count(DISTINCT thought) as thought_count,
               collect(DISTINCT tag.name) as tags
        ORDER BY t.title ASC
        SKIP $skip LIMIT $limit
        """
            mock_run_query.assert_called_once_with(expected_query, {"skip": 0, "limit": 10})
            self.assertEqual(result, expected_result)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_all_quotes(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {
                'id': 1, 'title': 'Test Quote', 'content': 'Quote content',
                'author': 'Test Author', 'source': 'Test Source',
                'created_date': '2023-01-01', 'last_modified': '2023-01-02',
                'tags': ['wisdom'], 'topics': ['philosophy']
            }
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.get_all_quotes(skip=5, limit=15)
            
            expected_query = """
        MATCH (q:Quote)
        OPTIONAL MATCH (q)-[:HAS_TAG]->(tag:Tag)
        OPTIONAL MATCH (q)-[:BELONGS_TO]->(topic:Topic)
        RETURN q.id as id, q.title as title, q.content as content,
               q.author as author, q.source as source,
               q.created_date as created_date, q.last_modified as last_modified,
               collect(DISTINCT tag.name) as tags,
               collect(DISTINCT topic.title) as topics
        ORDER BY q.last_modified DESC
        SKIP $skip LIMIT $limit
        """
            mock_run_query.assert_called_once_with(expected_query, {"skip": 5, "limit": 15})
            self.assertEqual(result, expected_result)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_all_passages(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {
                'id': 1, 'title': 'John 3:16', 'content': 'For God so loved the world...',
                'book': 'John', 'chapter': 3, 'verse': 16,
                'created_date': '2023-01-01', 'last_modified': '2023-01-02',
                'tags': ['love'], 'topics': ['salvation']
            }
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.get_all_passages()
            
            expected_query = """
        MATCH (p:Passage)
        OPTIONAL MATCH (p)-[:HAS_TAG]->(tag:Tag)
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(topic:Topic)
        RETURN p.id as id, p.title as title, p.content as content,
               p.book as book, p.chapter as chapter, p.verse as verse,
               p.created_date as created_date, p.last_modified as last_modified,
               collect(DISTINCT tag.name) as tags,
               collect(DISTINCT topic.title) as topics
        ORDER BY p.book, p.chapter, p.verse
        SKIP $skip LIMIT $limit
        """
            mock_run_query.assert_called_once_with(expected_query, {"skip": 0, "limit": 20})
            self.assertEqual(result, expected_result)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_item_by_id_found(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {
                'n': {'id': 123, 'title': 'Test Item'},
                'tags': ['tag1', 'tag2'],
                'topics': ['topic1'],
                'children': [{'id': 456, 'title': 'Child Item', 'type': 'Topic'}]
            }
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.get_item_by_id(123, "Topic")
            
            expected_query = """
        MATCH (n:Topic {id: $item_id})
        OPTIONAL MATCH (n)-[:HAS_TAG]->(tag:Tag)
        OPTIONAL MATCH (n)-[:BELONGS_TO]->(topic:Topic)
        OPTIONAL MATCH (n)<-[:BELONGS_TO]-(child)
        RETURN n, 
               collect(DISTINCT tag.name) as tags,
               collect(DISTINCT topic.title) as topics,
               collect(DISTINCT {id: child.id, title: child.title, type: labels(child)[0]}) as children
        """
            mock_run_query.assert_called_once_with(expected_query, {"item_id": 123})
            self.assertEqual(result, expected_result[0])
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_item_by_id_not_found(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        
        with patch.object(Neo4jService, 'run_query', return_value=[]) as mock_run_query:
            service = Neo4jService()
            result = service.get_item_by_id(999, "Topic")
            
            self.assertIsNone(result)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_search_content(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {
                'id': 1, 'title': 'Test Result', 'content': 'Search term found here',
                'type': 'Thought', 'last_modified': '2023-01-01'
            }
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.search_content("test search", skip=0, limit=10)
            
            expected_query = """
        CALL {
            MATCH (t:Thought)
            WHERE toLower(t.title) CONTAINS toLower($term) 
               OR toLower(t.content) CONTAINS toLower($term)
            RETURN t.id as id, t.title as title, t.content as content,
                   'Thought' as type, t.last_modified as last_modified
            UNION
            MATCH (t:Topic)
            WHERE toLower(t.title) CONTAINS toLower($term) 
               OR toLower(t.description) CONTAINS toLower($term)
            RETURN t.id as id, t.title as title, t.description as content,
                   'Topic' as type, t.last_modified as last_modified
            UNION
            MATCH (q:Quote)
            WHERE toLower(q.title) CONTAINS toLower($term) 
               OR toLower(q.content) CONTAINS toLower($term)
               OR toLower(q.author) CONTAINS toLower($term)
            RETURN q.id as id, q.title as title, q.content as content,
                   'Quote' as type, q.last_modified as last_modified
            UNION
            MATCH (p:Passage)
            WHERE toLower(p.title) CONTAINS toLower($term) 
               OR toLower(p.content) CONTAINS toLower($term)
               OR toLower(p.book) CONTAINS toLower($term)
            RETURN p.id as id, p.title as title, p.content as content,
                   'Passage' as type, p.last_modified as last_modified
        }
        RETURN id, title, content, type, last_modified
        ORDER BY last_modified DESC
        SKIP $skip LIMIT $limit
        """
            mock_run_query.assert_called_once_with(expected_query, {"term": "test search", "skip": 0, "limit": 10})
            self.assertEqual(result, expected_result)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_graph_data_with_node_id(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {
                'nodes': [
                    {'id': 1, 'title': 'Test Node', 'type': 'Topic', 'group': 1}
                ],
                'links': [
                    {'source': 1, 'target': 2, 'type': 'RELATED_TO'}
                ]
            }
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.get_graph_data(node_id=123, node_type="Topic")
            
            expected_query = """
            MATCH (center:Topic {id: $node_id})
            OPTIONAL MATCH (center)-[r1]-(connected)
            OPTIONAL MATCH (connected)-[r2]-(secondLevel)
            WHERE distance(center, secondLevel) <= 2
            WITH collect(DISTINCT center) + collect(DISTINCT connected) + collect(DISTINCT secondLevel) as nodes,
                 collect(DISTINCT r1) + collect(DISTINCT r2) as relationships
            UNWIND nodes as n
            UNWIND relationships as r
            RETURN collect(DISTINCT {
                id: n.id, 
                title: n.title, 
                type: labels(n)[0],
                group: CASE labels(n)[0]
                    WHEN 'Topic' THEN 1
                    WHEN 'Thought' THEN 2
                    WHEN 'Quote' THEN 3
                    WHEN 'Passage' THEN 4
                    ELSE 5
                END
            }) as nodes,
            collect(DISTINCT {
                source: startNode(r).id,
                target: endNode(r).id,
                type: type(r)
            }) as links
            """
            mock_run_query.assert_called_once_with(expected_query, {"node_id": 123})
            self.assertEqual(result, expected_result)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_graph_data_overall(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {
                'nodes': [
                    {'id': 1, 'title': 'Test Node', 'type': 'Topic', 'group': 1}
                ],
                'links': [
                    {'source': 1, 'target': 2, 'type': 'RELATED_TO'}
                ]
            }
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.get_graph_data()
            
            expected_query = """
            MATCH (n)
            WHERE n:Topic OR n:Thought OR n:Quote OR n:Passage
            OPTIONAL MATCH (n)-[r]-(m)
            WHERE m:Topic OR m:Thought OR m:Quote OR m:Passage
            RETURN collect(DISTINCT {
                id: n.id, 
                title: n.title, 
                type: labels(n)[0],
                group: CASE labels(n)[0]
                    WHEN 'Topic' THEN 1
                    WHEN 'Thought' THEN 2
                    WHEN 'Quote' THEN 3
                    WHEN 'Passage' THEN 4
                    ELSE 5
                END
            }) as nodes,
            collect(DISTINCT {
                source: startNode(r).id,
                target: endNode(r).id,
                type: type(r)
            }) as links
            LIMIT 500
            """
            mock_run_query.assert_called_once_with(expected_query)
            self.assertEqual(result, expected_result)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_tags(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {'allTags': ['tag1', 'tag2', 'tag3']}
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.get_tags()
            
            expected_query = """
        MATCH (n) WHERE n.tags IS NOT NULL RETURN n.tags AS allTags
        """
            mock_run_query.assert_called_once_with(expected_query)
            self.assertEqual(result, expected_result)
    
    @patch('thoughts_api.neo4j_service.GraphDatabase.driver')
    def test_get_items_by_tag(self, mock_driver):
        mock_driver.return_value = self.mock_driver
        expected_result = [
            {
                'id': 1, 'title': 'Tagged Item', 'content': 'Item content',
                'type': 'Topic', 'last_modified': '2023-01-01'
            }
        ]
        
        with patch.object(Neo4jService, 'run_query', return_value=expected_result) as mock_run_query:
            service = Neo4jService()
            result = service.get_items_by_tag("important", skip=5, limit=25)
            
            expected_query = """
        MATCH (tag:Tag {name: $tag_name})<-[:HAS_TAG]-(item)
        RETURN item.id as id, item.title as title, 
               CASE 
                   WHEN item.content IS NOT NULL THEN item.content
                   WHEN item.description IS NOT NULL THEN item.description
                   ELSE ''
               END as content,
               labels(item)[0] as type,
               item.last_modified as last_modified
        ORDER BY item.last_modified DESC
        SKIP $skip LIMIT $limit
        """
            mock_run_query.assert_called_once_with(expected_query, {"tag_name": "important", "skip": 5, "limit": 25})
            self.assertEqual(result, expected_result)
