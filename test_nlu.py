#!/usr/bin/env python
"""Quick test of NL parser"""

import sys
sys.path.insert(0, 'src')

from nlu_parser import EventDetailExtractor

# Test the parser
extractor = EventDetailExtractor()

test_inputs = [
    "book Friday 2PM movie date with John",
    "movie date with John Friday 2PM",
    "2PM Friday meeting with Sarah and Mike",
    "book meeting tomorrow at 3",
    "schedule dentist appointment on 12/25 at 10am",
]

for test_input in test_inputs:
    print(f"\n{'='*60}")
    print(f"Input: {test_input}")
    result = extractor.extract_all(test_input)
    print(f"Date: {result['date']}")
    print(f"Time: {result['time']}")
    print(f"Title: {result['title']}")
    print(f"Attendees: {result['attendees']}")
    print(f"Missing: {result['missing_keys']}")
