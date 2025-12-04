"""
AI Response Generator - Natural Language Output

This module is responsible for:
1. Taking the executed command result
2. Using AI to generate friendly, natural responses
3. Creating responses that sound human-like and contextual

After an action is performed, we don't just say "done" - 
we use AI to create natural language like:
"Your doctor appointment has been added for December 15 at 2 PM."
"I've cancelled your meeting with Sipho."
"You have 3 meetings today: one at 9 AM, one at 2 PM, and one at 5 PM."
"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any, List

try:
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

# Initialize async OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def generate_response(
    intent: str,
    parameters: Dict[str, Any],
    result: Dict[str, Any],
    success: bool = True
) -> str:
    """
    ========================================
    GENERATE NATURAL AI RESPONSE
    ========================================
    
    Takes the executed command and generates a human-sounding response.
    
    Args:
        intent (str): The intent that was executed ("create_event", "delete_event", etc.)
        parameters (Dict): Parameters extracted by AI (title, date, time, etc.)
        result (Dict): Result from executing the command (success status, created IDs, etc.)
        success (bool): Whether the command succeeded
    
    Returns:
        str: Natural language response to speak to the user
    """
    
    if not client:
        logger.error("OpenAI client not initialized.")
        return "I'm not able to respond right now. Please check your API key."
    
    # Build a prompt for the AI to generate a response
    prompt = _build_response_prompt(intent, parameters, result, success)
    
    try:
        logger.info(f"🤖 Generating response for intent: {intent}")
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a friendly voice assistant. Generate a short, natural response (1-2 sentences max) 
                    to confirm an action was completed. Be conversational and warm."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,  # Slightly higher for natural variation
            max_tokens=100
        )
        
        response_text = response.choices[0].message.content.strip()
        logger.info(f"✅ Generated response: {response_text}")
        
        return response_text
    
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return _fallback_response(intent, parameters, success)


def _build_response_prompt(
    intent: str,
    parameters: Dict[str, Any],
    result: Dict[str, Any],
    success: bool
) -> str:
    """
    Build a prompt for the AI to generate a response.
    
    Args:
        intent: The intent executed
        parameters: Extracted parameters
        result: Execution result
        success: Whether it succeeded
    
    Returns:
        str: Prompt for AI
    """
    
    if not success:
        return f"""Generate a brief, apologetic response explaining that we couldn't complete the {intent} action.
        Error: {result.get('error', 'Unknown error')}"""
    
    if intent == "create_event":
        title = parameters.get("title", "event")
        date = parameters.get("date", "the scheduled date")
        time = parameters.get("time", "the scheduled time")
        return f"""Confirm that I've successfully created an event titled "{title}" on {date} at {time}. 
        Be friendly and brief (one sentence)."""
    
    elif intent == "delete_event":
        title = parameters.get("event_title", "the event")
        return f"""Confirm that I've successfully deleted the event "{title}". Be friendly and brief (one sentence)."""
    
    elif intent == "show_events":
        date_range = parameters.get("date_range", "the requested time")
        event_count = result.get("event_count", 0)
        
        if event_count == 0:
            return f"""Tell the user in a friendly way that they have no events scheduled for {date_range}."""
        else:
            return f"""Summarize that the user has {event_count} events scheduled for {date_range}. Be brief (one sentence)."""
    
    else:
        return f"""Generate a brief, friendly response confirming the action was completed."""


def _fallback_response(intent: str, parameters: Dict[str, Any], success: bool) -> str:
    """
    Fallback responses when AI fails.
    
    Args:
        intent: The intent
        parameters: Extracted parameters
        success: Whether it succeeded
    
    Returns:
        str: Fallback response
    """
    
    if not success:
        return "Sorry, something went wrong. Please try again."
    
    if intent == "create_event":
        title = parameters.get("title", "event")
        date = parameters.get("date", "")
        time = parameters.get("time", "")
        return f"Added {title} to your calendar on {date} at {time}."
    
    elif intent == "delete_event":
        title = parameters.get("event_title", "event")
        return f"Deleted {title} from your calendar."
    
    elif intent == "show_events":
        return "Here's what's on your calendar."
    
    else:
        return "Done!"


def generate_response_sync(
    intent: str,
    parameters: Dict[str, Any],
    result: Dict[str, Any],
    success: bool = True
) -> str:
    """
    Synchronous wrapper for generate_response().
    
    Args:
        intent: The intent
        parameters: Extracted parameters
        result: Execution result
        success: Whether it succeeded
    
    Returns:
        str: Natural language response
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, generate_response(intent, parameters, result, success))
                return future.result()
        else:
            return asyncio.run(generate_response(intent, parameters, result, success))
    except RuntimeError:
        return asyncio.run(generate_response(intent, parameters, result, success))


# Example usage
if __name__ == "__main__":
    import sys
    
    # Example: python ai_response.py create_event "{\"title\": \"Meeting\", \"date\": \"2025-12-01\", \"time\": \"14:00\"}" "{\"success\": true}"
    
    if len(sys.argv) >= 2:
        intent = sys.argv[1]
        parameters = json.loads(sys.argv[2] if len(sys.argv) > 2 else "{}")
        result = json.loads(sys.argv[3] if len(sys.argv) > 3 else "{}")
        
        response = asyncio.run(generate_response(intent, parameters, result))
        print(response)
    else:
        print("Usage: python ai_response.py <intent> '<parameters_json>' '<result_json>'")
        print("Example: python ai_response.py create_event '{\"title\": \"Meeting\"}' '{\"success\": true}'")
