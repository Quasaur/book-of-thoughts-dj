#!/usr/bin/env python3
"""
Test script to verify neo4j_service.py functions work with the actual database schema.
"""

import os
import sys
import django
from pathlib import Path

# Add the Django project to the path
sys.path.append(str(Path(__file__).parent))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'book_of_thoughts.settings')
django.setup()

from thoughts_api.neo4j_service import neo4j_service

def test_service_functions():
    """Test each service function with actual database"""
    print("🧪 Testing Neo4j Service Functions")
    print("=" * 50)
    
    functions_to_test = [
        ('get_all_thoughts', lambda: neo4j_service.get_all_thoughts(limit=5)),
        ('get_all_topics', lambda: neo4j_service.get_all_topics(limit=5)),
        ('get_all_quotes', lambda: neo4j_service.get_all_quotes(limit=5)),
        ('get_all_passages', lambda: neo4j_service.get_all_passages(limit=5)),
        ('get_tags', lambda: neo4j_service.get_tags()),
        ('search_content', lambda: neo4j_service.search_content("God", limit=3)),
        ('get_graph_data', lambda: neo4j_service.get_graph_data()),
    ]
    
    results = {}
    
    for func_name, func_call in functions_to_test:
        print(f"\n🔍 Testing {func_name}...")
        try:
            result = func_call()
            results[func_name] = {
                'status': 'success',
                'result': result,
                'count': len(result) if isinstance(result, list) else 1
            }
            print(f"   ✅ Success: {len(result) if isinstance(result, list) else 1} results")
            if isinstance(result, list) and len(result) > 0:
                print(f"   📊 Sample result: {result[0]}")
        except Exception as e:
            results[func_name] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Error: {e}")
    
    # Test get_item_by_id with actual data
    print(f"\n🔍 Testing get_item_by_id...")
    try:
        # First get some actual data to test with
        thoughts = neo4j_service.get_all_thoughts(limit=1)
        if thoughts:
            # Try to get first thought by ID - but we need to figure out the ID format
            print(f"   📊 Sample thought: {thoughts[0]}")
            
            # The actual schema uses 'name' instead of 'id', so let's test with that
            if 'Name' in thoughts[0]:
                item = neo4j_service.get_item_by_id(thoughts[0]['Name'], 'THOUGHT')
                print(f"   ✅ get_item_by_id works: {item is not None}")
            else:
                print(f"   ⚠️  Could not test get_item_by_id - no ID field found")
        else:
            print(f"   ⚠️  No data to test get_item_by_id")
    except Exception as e:
        print(f"   ❌ get_item_by_id error: {e}")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_count = len(results)
    print(f"   ✅ Successful functions: {success_count}/{total_count}")
    
    if success_count < total_count:
        print(f"   ❌ Failed functions:")
        for func_name, result in results.items():
            if result['status'] == 'error':
                print(f"      - {func_name}: {result['error']}")
    
    return results

def analyze_schema_mismatch():
    """Analyze what needs to be updated in neo4j_service.py"""
    print(f"\n🔍 Schema Mismatch Analysis")
    print("=" * 50)
    
    print("Based on the actual database schema:")
    print("📊 Actual Node Labels: TOPIC, DESCRIPTION, THOUGHT, CONTENT")
    print("📊 Actual Relationships: HAS_DESCRIPTION, HAS_CHILD, HAS_CONTENT, HAS_THOUGHT")
    print()
    
    print("⚠️  Issues found in neo4j_service.py:")
    print("   1. get_all_topics() expects 'Topic' but database has 'TOPIC'")
    print("   2. get_all_quotes() expects 'Quote' but database doesn't have this label")
    print("   3. get_all_passages() expects 'Passage' but database doesn't have this label")
    print("   4. search_content() expects multiple labels that don't exist")
    print("   5. get_items_by_tag() expects 'Tag' nodes but database doesn't have this")
    print("   6. Many queries expect 'BELONGS_TO' and 'HAS_TAG' relationships that don't exist")
    print()
    
    print("🎯 Recommendations:")
    print("   1. Update get_all_topics() to use 'TOPIC' instead of 'Topic'")
    print("   2. Create Quote and Passage nodes if needed, or remove those functions")
    print("   3. Update search_content() to only search existing node types")
    print("   4. Update relationship queries to use actual relationships")
    print("   5. Consider if the current database structure meets the application needs")
    print()
    
    print("💡 The database appears to be a different structure than expected.")
    print("   It looks like a hierarchical thought/topic system rather than")
    print("   the multi-type content system the service expects.")

if __name__ == "__main__":
    try:
        results = test_service_functions()
        analyze_schema_mismatch()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        neo4j_service.close()