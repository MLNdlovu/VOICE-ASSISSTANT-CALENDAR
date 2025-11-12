"""
ChatGPT Integration Module for Voice Assistant Calendar

This module provides AI-powered conversational abilities using OpenAI's GPT models.
It enables natural language understanding and intelligent responses for calendar assistance.

Features:
- Conversational AI responses
- Calendar assistance and advice
- Smart scheduling suggestions
- Natural language understanding
- Context-aware responses
"""

import os
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import json

try:
    from openai import OpenAI
    CHATGPT_AVAILABLE = True
except ImportError:
    CHATGPT_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class CalendarChatbot:
    """
    AI-powered chatbot for the Voice Assistant Calendar.
    
    Provides conversational assistance using OpenAI's GPT models.
    Understands calendar context and provides intelligent scheduling advice.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the ChatGPT chatbot.
        
        Parameters:
        - api_key: OpenAI API key. If None, reads from OPENAI_API_KEY environment variable
        - model: Model to use. Default: "gpt-3.5-turbo" (can also use "gpt-4")
        
        Raises:
        - ValueError: If API key is not provided and not in environment
        """
        # Load environment variables if available
        if DOTENV_AVAILABLE:
            load_dotenv()
        
        # Get API key
        if api_key is None:
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. "
                "Please set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        
        if not CHATGPT_AVAILABLE:
            raise ImportError(
                "OpenAI library not installed. "
                "Install with: pip install openai"
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10  # Keep last 10 messages for context
        
        print(f"[INFO] ChatGPT chatbot initialized with model: {model}")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for calendar assistance."""
        return """You are an intelligent calendar assistant AI integrated with a Voice Assistant Calendar system.

Your responsibilities:
1. Help users manage their calendar efficiently
2. Suggest optimal time slots for meetings
3. Provide scheduling advice and best practices
4. Answer questions about calendar management
5. Help resolve scheduling conflicts
6. Suggest meeting durations and time blocks

Calendar Context:
- The system uses Google Calendar
- Users can book slots with email, date, time, and description
- Code Clinics are available for booking
- Users can view, book, and cancel events

Guidelines:
- Be concise and helpful
- Provide practical scheduling advice
- Suggest best times for different types of meetings
- Help users optimize their calendar
- Ask clarifying questions when needed
- Be friendly and professional
- When users mention dates, help them find optimal times
- Suggest buffer times between meetings

Remember: You're helping a student/user manage their academic or professional calendar."""
    
    def chat(self, user_message: str, calendar_context: Optional[Dict] = None) -> str:
        """
        Send a message to ChatGPT and get a response.
        
        Parameters:
        - user_message: The user's message
        - calendar_context: Optional calendar information (upcoming events, free slots, etc.)
        
        Returns:
        - The AI response as a string
        """
        # Add calendar context to the message if provided
        enhanced_message = user_message
        if calendar_context:
            context_info = self._format_calendar_context(calendar_context)
            enhanced_message = f"{user_message}\n\n[Calendar Context]\n{context_info}"
        
        # Add message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": enhanced_message
        })
        
        # Keep conversation history manageable
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()}
                ] + self.conversation_history,
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract response
            ai_response = response.choices[0].message.content
            
            # Add AI response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            return ai_response
        
        except Exception as e:
            error_msg = f"Error communicating with ChatGPT: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def suggest_meeting_time(self, meeting_type: str, duration_minutes: int = 30) -> str:
        """
        Get AI suggestions for optimal meeting times.
        
        Parameters:
        - meeting_type: Type of meeting (e.g., "code clinic", "study group", "consultation")
        - duration_minutes: How long the meeting should be
        
        Returns:
        - AI suggestions for meeting time
        """
        prompt = f"""I need to schedule a {meeting_type} that will take {duration_minutes} minutes. 
What are the best times and days to schedule this kind of meeting? 
Please provide specific recommendations."""
        
        return self.chat(prompt)
    
    def answer_calendar_question(self, question: str) -> str:
        """
        Answer a general calendar or scheduling question.
        
        Parameters:
        - question: The user's question about calendar management
        
        Returns:
        - AI's answer
        """
        return self.chat(question)
    
    def help_resolve_conflict(self, conflict_description: str) -> str:
        """
        Get help resolving a scheduling conflict.
        
        Parameters:
        - conflict_description: Description of the scheduling conflict
        
        Returns:
        - AI suggestions for resolving the conflict
        """
        prompt = f"""I have a scheduling conflict: {conflict_description}
How can I best resolve this conflict? What options do I have?"""
        
        return self.chat(prompt)
    
    def analyze_schedule(self, events_list: List[Dict]) -> str:
        """
        Get AI analysis of the user's schedule.
        
        Parameters:
        - events_list: List of events with details
        
        Returns:
        - AI analysis of the schedule
        """
        events_summary = "\n".join([
            f"- {e.get('summary', 'Untitled')}: {e.get('start', {}).get('dateTime', e.get('start', {}).get('date', 'N/A'))}"
            for e in events_list[:10]  # Limit to 10 events
        ])
        
        prompt = f"""Here are my upcoming events:
{events_summary}

Can you analyze my schedule and provide insights? 
- Am I overbooked?
- Do I have good breaks?
- Any suggestions for better time management?"""
        
        return self.chat(prompt)
    
    def _format_calendar_context(self, context: Dict) -> str:
        """Format calendar context information for the AI."""
        formatted = []
        
        if 'upcoming_events' in context:
            formatted.append(f"Upcoming events: {len(context['upcoming_events'])} events")
        
        if 'free_slots' in context:
            formatted.append(f"Available slots: {context['free_slots']}")
        
        if 'current_time' in context:
            formatted.append(f"Current time: {context['current_time']}")
        
        if 'total_events_today' in context:
            formatted.append(f"Events today: {context['total_events_today']}")
        
        return "\n".join(formatted)
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        print("[INFO] Conversation history cleared")
    
    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        return {
            "model": self.model,
            "conversation_history_length": len(self.conversation_history),
            "max_history": self.max_history,
            "is_available": CHATGPT_AVAILABLE
        }


def is_chatgpt_available() -> bool:
    """Check if ChatGPT is available and configured."""
    if not CHATGPT_AVAILABLE:
        return False
    
    api_key = os.getenv('OPENAI_API_KEY')
    return bool(api_key)


def initialize_chatbot(api_key: Optional[str] = None, model: str = "gpt-3.5-turbo") -> Optional[CalendarChatbot]:
    """
    Safely initialize the chatbot.
    
    Parameters:
    - api_key: Optional OpenAI API key
    - model: Model to use
    
    Returns:
    - CalendarChatbot instance or None if not available
    """
    if not CHATGPT_AVAILABLE:
        print("[WARN] OpenAI not installed. Install with: pip install openai")
        return None
    
    try:
        return CalendarChatbot(api_key=api_key, model=model)
    except ValueError as e:
        print(f"[WARN] ChatGPT initialization failed: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error initializing ChatGPT: {e}")
        return None


# Example usage for testing
if __name__ == "__main__":
    print("Testing ChatGPT Integration...\n")
    
    # Check if API key is available
    if not is_chatgpt_available():
        print("❌ ChatGPT not available. Please set OPENAI_API_KEY environment variable.")
        print("   You can add it to a .env file or set it as an environment variable.")
        exit(1)
    
    # Initialize chatbot
    try:
        bot = CalendarChatbot(model="gpt-3.5-turbo")
        print("✅ ChatGPT chatbot initialized successfully!\n")
        
        # Test basic chat
        print("Testing basic conversation...")
        response = bot.answer_calendar_question("What are the best times to schedule meetings?")
        print(f"\n[AI] {response}\n")
        
        # Test meeting suggestions
        print("Testing meeting suggestions...")
        response = bot.suggest_meeting_time("code clinic session", 60)
        print(f"\n[AI] {response}\n")
        
        print("✅ ChatGPT integration working correctly!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
