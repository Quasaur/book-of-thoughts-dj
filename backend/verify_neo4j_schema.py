#!/usr/bin/env python3
"""
Script to verify Neo4j database schema matches the neo4j_service.py expectations and tests.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

# Add the Django project to the path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
load_dotenv()

class Neo4jSchemaVerifier:
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.username = os.getenv('NEO4J_USERNAME')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Missing Neo4j connection parameters in environment variables")
        
        self.driver = None
        self.schema_info = {}
    
    def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Test connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_result = result.single()
                if test_result and test_result['test'] == 1:
                    print("✅ Successfully connected to Neo4j database")
                    return True
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def run_query(self, query, parameters=None):
        """Execute a query and return results"""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []
    
    def get_node_labels(self):
        """Get all node labels in the database"""
        query = "CALL db.labels()"
        results = self.run_query(query)
        labels = [record['label'] for record in results]
        self.schema_info['node_labels'] = labels
        return labels
    
    def get_relationship_types(self):
        """Get all relationship types in the database"""
        query = "CALL db.relationshipTypes()"
        results = self.run_query(query)
        rel_types = [record['relationshipType'] for record in results]
        self.schema_info['relationship_types'] = rel_types
        return rel_types
    
    def get_node_properties(self, label):
        """Get properties for a specific node label"""
        query = f"MATCH (n:{label}) RETURN keys(n) as properties LIMIT 10"
        results = self.run_query(query)
        properties = set()
        for record in results:
            properties.update(record['properties'])
        return list(properties)
    
    def get_sample_nodes(self, label, limit=3):
        """Get sample nodes for a specific label"""
        query = f"MATCH (n:{label}) RETURN n LIMIT {limit}"
        results = self.run_query(query)
        return [record['n'] for record in results]
    
    def verify_expected_schema(self):
        """Verify the database schema matches expectations from neo4j_service.py"""
        print("\n🔍 Verifying Neo4j Schema...")
        
        # Expected node labels based on neo4j_service.py
        expected_labels = [
            'THOUGHT',      # Used in get_all_thoughts()
            'Topic',        # Used in get_all_topics()
            'Quote',        # Used in get_all_quotes()
            'Passage',      # Used in get_all_passages()
            'Tag',          # Used in get_tags(), get_items_by_tag()
            'CONTENT',      # Used in get_all_thoughts()
            'Thought'       # Used in search_content() (different from THOUGHT)
        ]
        
        # Expected relationship types
        expected_relationships = [
            'HAS_CONTENT',  # Used in get_all_thoughts()
            'BELONGS_TO',   # Used in get_all_topics(), get_all_quotes(), get_all_passages()
            'HAS_TAG'       # Used throughout for tag relationships
        ]
        
        # Get actual schema
        actual_labels = self.get_node_labels()
        actual_relationships = self.get_relationship_types()
        
        print(f"\n📊 Database Schema Summary:")
        print(f"   Node Labels: {len(actual_labels)}")
        print(f"   Relationship Types: {len(actual_relationships)}")
        
        # Check node labels
        print(f"\n🏷️  Node Labels Analysis:")
        print(f"   Expected: {expected_labels}")
        print(f"   Actual:   {actual_labels}")
        
        missing_labels = set(expected_labels) - set(actual_labels)
        extra_labels = set(actual_labels) - set(expected_labels)
        
        if missing_labels:
            print(f"   ⚠️  Missing labels: {list(missing_labels)}")
        if extra_labels:
            print(f"   ℹ️  Extra labels: {list(extra_labels)}")
        if not missing_labels:
            print(f"   ✅ All expected labels found!")
        
        # Check relationship types
        print(f"\n🔗 Relationship Types Analysis:")
        print(f"   Expected: {expected_relationships}")
        print(f"   Actual:   {actual_relationships}")
        
        missing_rels = set(expected_relationships) - set(actual_relationships)
        extra_rels = set(actual_relationships) - set(expected_relationships)
        
        if missing_rels:
            print(f"   ⚠️  Missing relationships: {list(missing_rels)}")
        if extra_rels:
            print(f"   ℹ️  Extra relationships: {list(extra_rels)}")
        if not missing_rels:
            print(f"   ✅ All expected relationships found!")
        
        return {
            'missing_labels': list(missing_labels),
            'extra_labels': list(extra_labels),
            'missing_relationships': list(missing_rels),
            'extra_relationships': list(extra_rels)
        }
    
    def analyze_node_properties(self):
        """Analyze node properties for each label"""
        print(f"\n🔍 Node Properties Analysis:")
        
        labels = self.get_node_labels()
        for label in labels:
            properties = self.get_node_properties(label)
            sample_nodes = self.get_sample_nodes(label, 2)
            
            print(f"\n   {label}:")
            print(f"     Properties: {properties}")
            if sample_nodes:
                print(f"     Sample data: {sample_nodes[0] if sample_nodes else 'No samples'}")
    
    def verify_service_queries(self):
        """Test if the queries from neo4j_service.py would work"""
        print(f"\n🧪 Testing Service Queries...")
        
        # Test get_all_thoughts query structure
        thoughts_query = """
        MATCH (t:THOUGHT)
        OPTIONAL MATCH (t)-[:HAS_CONTENT]->(c:CONTENT)
        RETURN t.id as ID, t.name as Name, t.parent as Parent, t.tags as Tags, 
               t.level as Level
        ORDER BY t.name DESC
        LIMIT 1
        """
        
        try:
            result = self.run_query(thoughts_query)
            print(f"   ✅ get_all_thoughts query: {'Works' if result is not None else 'Failed'}")
        except Exception as e:
            print(f"   ❌ get_all_thoughts query failed: {e}")
        
        # Test get_all_topics query structure
        topics_query = """
        MATCH (t:Topic)
        OPTIONAL MATCH (t)<-[:BELONGS_TO]-(thought:Thought)
        OPTIONAL MATCH (t)-[:HAS_TAG]->(tag:Tag)
        RETURN t.id as id, t.title as title, t.description as description,
               t.created_date as created_date, t.last_modified as last_modified,
               count(DISTINCT thought) as thought_count,
               collect(DISTINCT tag.name) as tags
        ORDER BY t.title ASC
        LIMIT 1
        """
        
        try:
            result = self.run_query(topics_query)
            print(f"   ✅ get_all_topics query: {'Works' if result is not None else 'Failed'}")
        except Exception as e:
            print(f"   ❌ get_all_topics query failed: {e}")
        
        # Test other key queries...
        queries_to_test = [
            ("get_all_quotes", "MATCH (q:Quote) RETURN count(q) as count"),
            ("get_all_passages", "MATCH (p:Passage) RETURN count(p) as count"),
            ("get_tags", "MATCH (n) WHERE n.tags IS NOT NULL RETURN count(n) as count"),
        ]
        
        for query_name, query in queries_to_test:
            try:
                result = self.run_query(query)
                print(f"   ✅ {query_name} query: {'Works' if result is not None else 'Failed'}")
            except Exception as e:
                print(f"   ❌ {query_name} query failed: {e}")
    
    def generate_report(self):
        """Generate a comprehensive schema verification report"""
        print(f"\n📋 Generating Schema Verification Report...")
        
        # Connect to database
        if not self.connect():
            return False
        
        try:
            # Verify schema
            schema_issues = self.verify_expected_schema()
            
            # Analyze properties
            self.analyze_node_properties()
            
            # Test service queries
            self.verify_service_queries()
            
            # Summary
            print(f"\n📊 SUMMARY:")
            if not any(schema_issues.values()):
                print(f"   ✅ Schema matches expectations perfectly!")
            else:
                print(f"   ⚠️  Schema has some discrepancies:")
                for issue_type, issues in schema_issues.items():
                    if issues:
                        print(f"     - {issue_type}: {issues}")
            
            return True
            
        finally:
            self.close()

def main():
    """Main function to run schema verification"""
    print("🚀 Neo4j Schema Verification Tool")
    print("=" * 50)
    
    try:
        verifier = Neo4jSchemaVerifier()
        verifier.generate_report()
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())