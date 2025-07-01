#!/usr/bin/env python3
"""
Export entire AuraDB contents to a single Cypher query file
"""

import os
import sys
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class AuraDBExporter:
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.username = os.getenv('NEO4J_USERNAME')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Missing Neo4j connection parameters. Check your .env file.")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def export_to_cypher(self, output_file="auradb_export.cypher"):
        """Export all nodes and relationships to Cypher CREATE statements"""
        
        print(f"Starting export to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"// AuraDB Export Generated on {datetime.now().isoformat()}\n")
            f.write(f"// Database: {self.database}\n")
            f.write("// This file contains CREATE statements to recreate the entire database\n\n")
            
            # Clear existing data
            f.write("// Clear existing data\n")
            f.write("MATCH (n) DETACH DELETE n;\n\n")
            
            # Export constraints and indexes first
            self._export_schema(f)
            
            # Export nodes
            self._export_nodes(f)
            
            # Export relationships
            self._export_relationships(f)
            
        print(f"Export completed: {output_file}")
    
    def _export_schema(self, file_handle):
        """Export database schema (constraints and indexes)"""
        file_handle.write("// Database Schema\n")
        
        with self.driver.session(database=self.database) as session:
            # Get constraints
            constraints = session.run("SHOW CONSTRAINTS").data()
            if constraints:
                file_handle.write("// Constraints\n")
                for constraint in constraints:
                    if 'labelsOrTypes' in constraint and 'properties' in constraint:
                        labels = constraint['labelsOrTypes']
                        properties = constraint['properties']
                        if labels and properties:
                            label = labels[0] if isinstance(labels, list) else labels
                            prop = properties[0] if isinstance(properties, list) else properties
                            file_handle.write(f"CREATE CONSTRAINT FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE;\n")
                file_handle.write("\n")
            
            # Get indexes
            indexes = session.run("SHOW INDEXES").data()
            if indexes:
                file_handle.write("// Indexes\n")
                for index in indexes:
                    if 'labelsOrTypes' in index and 'properties' in index:
                        labels = index['labelsOrTypes']
                        properties = index['properties']
                        if labels and properties:
                            label = labels[0] if isinstance(labels, list) else labels
                            prop = properties[0] if isinstance(properties, list) else properties
                            file_handle.write(f"CREATE INDEX FOR (n:{label}) ON (n.{prop});\n")
                file_handle.write("\n")
    
    def _export_nodes(self, file_handle):
        """Export all nodes as CREATE statements"""
        file_handle.write("// Nodes\n")
        
        with self.driver.session(database=self.database) as session:
            # Get all nodes
            result = session.run("MATCH (n) RETURN n ORDER BY id(n)")
            
            for record in result:
                node = record['n']
                labels = ':'.join(node.labels)
                
                # Convert properties to Cypher format
                props = self._format_properties(dict(node))
                
                if props:
                    file_handle.write(f"CREATE (:{labels} {props});\n")
                else:
                    file_handle.write(f"CREATE (:{labels});\n")
        
        file_handle.write("\n")
    
    def _export_relationships(self, file_handle):
        """Export all relationships as MATCH + CREATE statements"""
        file_handle.write("// Relationships\n")
        
        with self.driver.session(database=self.database) as session:
            # Get all relationships with their nodes
            result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN a, r, b
                ORDER BY id(r)
            """)
            
            for record in result:
                start_node = record['a']
                relationship = record['r']
                end_node = record['b']
                
                # Create MATCH patterns for start and end nodes
                start_labels = ':'.join(start_node.labels)
                end_labels = ':'.join(end_node.labels)
                
                # Use unique properties to identify nodes
                start_match = self._get_node_match_pattern(start_node, start_labels)
                end_match = self._get_node_match_pattern(end_node, end_labels)
                
                # Format relationship properties
                rel_props = self._format_properties(dict(relationship))
                rel_type = relationship.type
                
                if rel_props:
                    file_handle.write(f"MATCH {start_match}, {end_match} CREATE (a)-[:{rel_type} {rel_props}]->(b);\n")
                else:
                    file_handle.write(f"MATCH {start_match}, {end_match} CREATE (a)-[:{rel_type}]->(b);\n")
        
        file_handle.write("\n")
    
    def _get_node_match_pattern(self, node, labels):
        """Generate a MATCH pattern to uniquely identify a node"""
        props = dict(node)
        
        # Try to use 'name' property first as it seems to be the primary identifier
        if 'name' in props:
            name_value = self._format_value(props['name'])
            return f"(a:{labels} {{name: {name_value}}})"
        
        # Fall back to 'id' if available
        if 'id' in props:
            id_value = self._format_value(props['id'])
            return f"(a:{labels} {{id: {id_value}}})"
        
        # Use all properties to ensure uniqueness
        formatted_props = self._format_properties(props)
        if formatted_props:
            return f"(a:{labels} {formatted_props})"
        else:
            return f"(a:{labels})"
    
    def _format_properties(self, props):
        """Format properties dictionary as Cypher property map"""
        if not props:
            return ""
        
        formatted_props = []
        for key, value in props.items():
            formatted_props.append(f"{key}: {self._format_value(value)}")
        
        return "{" + ", ".join(formatted_props) + "}"
    
    def _format_value(self, value):
        """Format a single value for Cypher"""
        if value is None:
            return "null"
        elif isinstance(value, str):
            # Escape quotes and special characters
            escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
            return f'"{escaped}"'
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            formatted_items = [self._format_value(item) for item in value]
            return "[" + ", ".join(formatted_items) + "]"
        else:
            # Convert to string and treat as string
            escaped = str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
            return f'"{escaped}"'

def main():
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    else:
        output_file = f"auradb_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cypher"
    
    exporter = None
    try:
        exporter = AuraDBExporter()
        exporter.export_to_cypher(output_file)
        print(f"\nExport successful! File saved as: {output_file}")
        print(f"To import into another Neo4j instance, run: cypher-shell -f {output_file}")
        
    except Exception as e:
        print(f"Export failed: {e}")
        sys.exit(1)
    finally:
        if exporter:
            exporter.close()

if __name__ == "__main__":
    main()