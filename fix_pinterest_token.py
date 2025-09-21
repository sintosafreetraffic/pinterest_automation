#!/usr/bin/env python3
"""
Fix for Pinterest token in Render
Creates pinterest_token.json from environment variable if it doesn't exist
"""

import os
import json
from pathlib import Path

def setup_pinterest_token():
    """Setup Pinterest token from environment variable"""
    token_file = Path("pinterest_token.json")
    
    # If pinterest_token.json doesn't exist, create it from environment variable
    if not token_file.exists():
        pinterest_token = os.getenv("PINTEREST_TOKEN_JSON")
        if pinterest_token:
            try:
                # Parse the JSON to validate it
                token_data = json.loads(pinterest_token)
                # Write to file
                with open("pinterest_token.json", "w") as f:
                    json.dump(token_data, f)
                print("✅ Created pinterest_token.json from environment variable")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing PINTEREST_TOKEN_JSON: {e}")
                return False
        else:
            print("❌ PINTEREST_TOKEN_JSON environment variable not found")
            return False
    else:
        print("✅ pinterest_token.json already exists")
        return True

if __name__ == "__main__":
    setup_pinterest_token()
