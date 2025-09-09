#!/usr/bin/env python3
"""
Generate OpenAPI schema for GPTrans API
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backend.main import app

def generate_openapi_schema():
    """Generate and save OpenAPI schema."""
    
    schema = app.openapi()
    
    # Save to file
    output_path = Path(__file__).parent.parent / "docs" / "openapi.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print(f"OpenAPI schema saved to: {output_path}")
    
    # Print summary
    paths = schema.get('paths', {})
    print(f"\nAPI Summary:")
    print(f"- Title: {schema.get('info', {}).get('title', 'Unknown')}")
    print(f"- Version: {schema.get('info', {}).get('version', 'Unknown')}")
    print(f"- Endpoints: {len(paths)}")
    
    # List endpoints
    for path, methods in paths.items():
        for method, details in methods.items():
            summary = details.get('summary', 'No summary')
            print(f"  {method.upper()} {path} - {summary}")

if __name__ == "__main__":
    generate_openapi_schema()