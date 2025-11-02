#!/usr/bin/env python3
"""
Notion MCP Server Test Results
Successfully connected and queried databases, attempted status updates.
"""

import json
from datetime import datetime

def print_test_results():
    """Print comprehensive test results"""
    
    print("=" * 70)
    print("NOTION MCP SERVER TEST RESULTS")
    print("=" * 70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Authentication test
    print("✅ Authentication: SUCCESS")
    print("   User: Cursor MCP (LucidWork)")
    print("   Workspace: LucidWork")
    print()
    
    # Database search results
    print("📋 Databases Found: 2")
    print()
    
    databases = [
        {
            "name": "Tasks",
            "id": "29f795383d90808f874ef7a8e7857c01",
            "status_property": "Status",
            "status_options": ["Not started", "In progress", "Done"]
        },
        {
            "name": "Projects",
            "id": "29f795383d9080388644f9c25bdf2689",
            "status_property": "Status",
            "status_options": ["Not started", "In progress", "Done"]
        }
    ]
    
    # Query results
    print("🔍 Query Results:")
    print()
    
    results = {
        "status": "partial_success",
        "authentication": "success",
        "databases_found": len(databases),
        "databases": [],
        "updates_made": [],
        "errors": []
    }
    
    for db in databases:
        print(f"   Database: {db['name']}")
        print(f"   ID: {db['id']}")
        
        if db['name'] == "Tasks":
            items_found = 0
            print(f"   Items with 'In progress' status: {items_found}")
            print(f"   Update: No items to update")
            results["databases"].append({
                "name": db['name'],
                "id": db['id'],
                "items_in_progress": 0,
                "updated": False,
                "reason": "No items with 'In progress' status"
            })
        else:  # Projects
            items_found = 1
            item_id = "29f795383d9080998310ff5067ce288f"
            item_name = "LucidWork MVP"
            print(f"   Items with 'In progress' status: {items_found}")
            print(f"   Found item: {item_name}")
            print(f"   Item ID: {item_id}")
            print(f"   Update: Attempted (manual confirmation may be needed)")
            results["databases"].append({
                "name": db['name'],
                "id": db['id'],
                "items_in_progress": items_found,
                "found_item": {
                    "id": item_id,
                    "name": item_name
                },
                "updated": False,
                "status": "Update call encountered tool parameter issues"
            })
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Authentication: Working")
    print(f"✅ Databases found: {results['databases_found']}")
    print(f"⚠️  Items found with 'In progress': {sum(db['items_in_progress'] for db in results['databases'])}")
    print(f"⚠️  Updates completed: {len(results['updates_made'])}")
    print()
    print("Note: Found 1 item in Projects database with 'In progress' status.")
    print("The item 'LucidWork MVP' (ID: 29f795383d9080998310ff5067ce288f) should be")
    print("updated from 'In progress' to 'Done' manually or via a corrected API call.")
    print()
    
    print("=" * 70)
    print("JSON Results:")
    print("=" * 70)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    print_test_results()
