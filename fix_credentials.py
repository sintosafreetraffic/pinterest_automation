#!/usr/bin/env python3
"""
Fix for Google Sheets credentials in Render
Creates credentials.json from environment variable if it doesn't exist
"""

import os
import json
from pathlib import Path

def setup_google_credentials():
    """Setup Google credentials from environment variable"""
    credentials_file = Path("credentials.json")
    
    # If credentials.json doesn't exist, create it from environment variable
    if not credentials_file.exists():
        google_credentials = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if google_credentials:
            try:
                # Parse the JSON to validate it
                credentials_data = json.loads(google_credentials)
                # Write to file
                with open("credentials.json", "w") as f:
                    json.dump(credentials_data, f)
                print("✅ Created credentials.json from environment variable")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing GOOGLE_CREDENTIALS_JSON: {e}")
                return False
        else:
            print("❌ GOOGLE_CREDENTIALS_JSON environment variable not found")
            return False
    else:
        print("✅ credentials.json already exists")
        return True

if __name__ == "__main__":
    setup_google_credentials()
