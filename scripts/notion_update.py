#!/usr/bin/env python3
"""
CLI script for updating Notion database items.

Usage:
    python scripts/notion_update.py <database_type> <item_name> <status>
    python scripts/notion_update.py tasks "Create route stubs" "Done"
    python scripts/notion_update.py projects "Hub Queue" "In progress"

Examples:
    # Update a task to Done
    python scripts/notion_update.py tasks "Task name" "Done"
    
    # Update a project to In progress
    python scripts/notion_update.py projects "Project name" "In progress"
    
    # List items with specific status
    python scripts/notion_update.py tasks --list "In progress"
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.notion_helper import (
    update_item_status,
    get_items_by_status,
    get_database_id,
    DATABASES,
)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "--list" or (len(sys.argv) >= 3 and sys.argv[2] == "--list"):
        # List items with status
        if len(sys.argv) < 4:
            print("Usage: python scripts/notion_update.py <tasks|projects> --list <status>")
            sys.exit(1)
        
        db_type = sys.argv[1] if command != "--list" else sys.argv[2]
        status = sys.argv[3] if command != "--list" else sys.argv[2]
        
        if db_type not in DATABASES:
            print(f"Error: Database type must be 'tasks' or 'projects', got '{db_type}'")
            sys.exit(1)
        
        print(f"Finding {db_type} with status '{status}'...")
        items = get_items_by_status(db_type, status)
        
        if not items:
            print(f"No items found with status '{status}'")
            sys.exit(0)
        
        print(f"\nFound {len(items)} items:\n")
        for item in items:
            name = item["properties"].get("Name", {}).get("title", [])
            name_text = name[0]["plain_text"] if name else "Untitled"
            page_id = item["id"]
            print(f"  - {name_text} (ID: {page_id})")
        
        sys.exit(0)
    
    # Update item status
    if len(sys.argv) < 4:
        print("Usage: python scripts/notion_update.py <tasks|projects> <item_name> <status>")
        print("\nStatus values:")
        print("  Tasks: 'Not started', 'In progress', 'Done'")
        print("  Projects: 'Not started', 'In progress', 'Done'")
        sys.exit(1)
    
    db_type = sys.argv[1]
    item_name = sys.argv[2]
    status = sys.argv[3]
    
    if db_type not in DATABASES:
        print(f"Error: Database type must be 'tasks' or 'projects', got '{db_type}'")
        sys.exit(1)
    
    try:
        print(f"Searching for '{item_name}' in {db_type} database...")
        result = update_item_status(db_type, item_name, status)
        
        # Extract updated info
        name = result["properties"].get("Name", {}).get("title", [])
        name_text = name[0]["plain_text"] if name else "Untitled"
        updated_status = result["properties"].get("Status", {}).get("status", {})
        status_name = updated_status.get("name", "Unknown")
        
        print(f"✅ Successfully updated '{name_text}' to status: {status_name}")
        print(f"   Page ID: {result['id']}")
        print(f"   URL: {result.get('url', 'N/A')}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

