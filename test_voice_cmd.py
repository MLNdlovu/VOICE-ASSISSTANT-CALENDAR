#!/usr/bin/env python
"""
Test script for /api/voice_cmd endpoint
"""

import json
import requests
import sys

BASE_URL = "http://localhost:5000"

def test_voice_cmd():
    """Test the voice command endpoint"""
    
    tests = [
        {
            "name": "Book a meeting",
            "payload": {
                "transcript": "book a meeting tomorrow at 2 PM called budget review",
                "user_id": "test_user"
            }
        },
        {
            "name": "Get events",
            "payload": {
                "transcript": "what's on my calendar today",
                "user_id": "test_user"
            }
        },
        {
            "name": "General question",
            "payload": {
                "transcript": "hello how are you",
                "user_id": "test_user"
            }
        },
        {
            "name": "Empty transcript",
            "payload": {
                "transcript": "",
                "user_id": "test_user"
            }
        }
    ]
    
    for test in tests:
        print(f"\n{'='*60}")
        print(f"Testing: {test['name']}")
        print(f"{'='*60}")
        print(f"Request: {json.dumps(test['payload'], indent=2)}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/voice_cmd",
                json=test['payload'],
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to server. Is it running on localhost:5000?")
            return False
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_voice_cmd()
    sys.exit(0 if success else 1)
