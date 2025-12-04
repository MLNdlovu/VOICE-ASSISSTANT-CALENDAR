"""
AI Intent Handler - The Core AI Brain

This module is responsible for:
1. Taking raw user voice transcripts
2. Sending them to OpenAI GPT for interpretation
3. Parsing the structured JSON response
4. Extracting intent and parameters

The AI model understands natural language and decides what the user meant,
replacing all old regex/pattern matching logic.
"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    raise ImportError("Please install openai: pip install openai")

import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# AI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set. AI intent handler will not work.")

# Initialize async OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def interpret(text: str) -> Dict[str, Any]:
    """
    ========================================
    MAIN AI ENTRY POINT - INTERPRET USER TEXT
    ========================================
    
    This is where the magic happens:
    1. Send raw user voice text to OpenAI
    2. AI reads the system prompt (ai_prompts/system_prompt.txt)
    3. AI decides the intent (create_event, delete_event, show_events, etc.)
    4. AI extracts parameters (date, time, title, person name, etc.)
    5. Returns structured JSON
    
    Args:
        text (str): Raw user voice transcript
    
    Returns:
        Dict with:
        {
            "success": bool,
            "intent": str,  # "create_event", "delete_event", "show_events", "unknown"
            "parameters": {},  # intent-specific parameters
            "confidence": float,  # 0.0 to 1.0
            "raw_response": str  # for debugging
        }
    """
    
    if not client:
        logger.error("OpenAI client not initialized. Check OPENAI_API_KEY.")
        return {
            "success": False,
            "intent": "error",
            "parameters": {},
            "confidence": 0.0,
            "raw_response": "OpenAI API key not configured."
        }
    
    if not text or not text.strip():
        return {
            "success": False,
            "intent": "empty_input",
            "parameters": {},
            "confidence": 0.0,
            "raw_response": "No text provided."
        }
    
    try:
        # Load system prompt from file
        system_prompt = _load_system_prompt()
        
        logger.info(f"🤖 AI Interpreting: '{text}'")
        
        # Call OpenAI with async
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3,  # Low temperature for consistent JSON
            max_tokens=500,
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        # Extract response text
        response_text = response.choices[0].message.content
        logger.debug(f"🤖 AI Raw Response: {response_text}")
        
        # Parse JSON
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response_text}")
            return {
                "success": False,
                "intent": "json_parse_error",
                "parameters": {},
                "confidence": 0.0,
                "raw_response": response_text
            }
        
        # Validate required fields
        if "intent" not in parsed:
            parsed["intent"] = "unknown"
        
        if "parameters" not in parsed:
            parsed["parameters"] = {}
        
        parsed["success"] = parsed.get("intent") != "unknown"
        parsed["confidence"] = parsed.get("confidence", 0.8)
        parsed["raw_response"] = response_text
        
        logger.info(f"✅ Intent: {parsed['intent']} | Confidence: {parsed['confidence']}")
        
        return parsed
    
    except Exception as e:
        logger.error(f"AI interpretation error: {str(e)}")
        return {
            "success": False,
            "intent": "error",
            "parameters": {},
            "confidence": 0.0,
            "raw_response": str(e)
        }


def _load_system_prompt() -> str:
    """
    Load AI system prompt from file.
    This tells the AI exactly how to interpret commands.
    
    Returns:
        str: System prompt content
    """
    prompt_file = "ai_prompts/system_prompt.txt"
    
    try:
        with open(prompt_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning(f"System prompt file not found: {prompt_file}")
        # Fallback prompt
        return """You are the AI command interpreter for a voice assistant calendar app.
Your job is to extract intent and parameters from natural voice commands.

You MUST respond with ONLY valid JSON. No other text.

Possible intents: "create_event", "delete_event", "show_events", "unknown"

For "create_event":
- Extract: title (event name), date (YYYY-MM-DD), time (HH:MM)
- Example: "book meeting tomorrow at 2pm" → {"intent": "create_event", "parameters": {"title": "meeting", "date": "2025-12-01", "time": "14:00"}}

For "delete_event":
- Extract: event_title or event_id
- Example: "delete my meeting" → {"intent": "delete_event", "parameters": {"event_title": "meeting"}}

For "show_events":
- Extract: date_range (optional: today, tomorrow, this week, this month)
- Example: "what's on my calendar today" → {"intent": "show_events", "parameters": {"date_range": "today"}}

For "unknown":
- When you can't determine the intent
- Example: "what's the weather" → {"intent": "unknown", "parameters": {}}

Always respond with valid JSON only."""


async def interpret_batch(texts: list) -> list:
    """
    Process multiple texts at once (async batch processing).
    
    Args:
        texts (list): List of strings to interpret
    
    Returns:
        list: List of interpretation results
    """
    tasks = [interpret(text) for text in texts]
    return await asyncio.gather(*tasks)


def interpret_sync(text: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for interpret() - useful if you can't use async.
    
    Args:
        text (str): Raw user voice transcript
    
    Returns:
        Dict: Interpretation result
    """
    try:
        # Run async function in event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, use run_in_executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, interpret(text))
                return future.result()
        else:
            return asyncio.run(interpret(text))
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(interpret(text))


# Example usage (for testing)
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        user_text = " ".join(sys.argv[1:])
        result = asyncio.run(interpret(user_text))
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python ai_intent_handler.py '<your voice command>'")
        print("Example: python ai_intent_handler.py 'book a meeting tomorrow at 2pm'")
