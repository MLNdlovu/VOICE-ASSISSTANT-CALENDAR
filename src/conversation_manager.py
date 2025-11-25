"""
Multi-Step Voice Conversation Handler (Jarvis-style)

Manages chain-of-thought conversations with memory, context tracking,
and intelligent follow-up questions. Enables natural multi-turn interactions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Callable
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# ============================================================================
# Data Structures & Enums
# ============================================================================

class ConversationState(Enum):
    """State of a conversation."""
    IDLE = "idle"                     # Not in conversation
    LISTENING = "listening"           # Waiting for user input
    PROCESSING = "processing"         # Analyzing input
    GENERATING_RESPONSE = "generating" # Creating response
    WAITING_FOR_CONFIRMATION = "waiting_confirmation"
    TASK_IN_PROGRESS = "task_in_progress"
    COMPLETED = "completed"


class DialogueType(Enum):
    """Type of dialogue/interaction."""
    QUESTION_ANSWER = "qa"             # Simple Q&A
    TASK_CREATION = "task_creation"   # Multi-step task setup
    SCHEDULING = "scheduling"         # Meeting/event scheduling
    CLARIFICATION = "clarification"   # Asking for clarification
    CONFIRMATION = "confirmation"     # Confirming action
    INFORMATION = "information"       # Providing information


@dataclass
class DialogueTurn:
    """Single turn in a conversation."""
    turn_number: int
    speaker: str  # 'user' or 'assistant'
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    parsed_intent: Optional[Dict] = None
    extracted_data: Optional[Dict] = None


@dataclass
class MultiStepConversation:
    """Multi-turn conversation with full context."""
    conversation_id: str
    dialogue_type: DialogueType = DialogueType.QUESTION_ANSWER
    state: ConversationState = ConversationState.IDLE
    turns: List[DialogueTurn] = field(default_factory=list)
    
    # Context tracking
    current_topic: str = ""
    subtopic_stack: List[str] = field(default_factory=list)
    
    # Data collection
    collected_data: Dict[str, Any] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    completed_fields: List[str] = field(default_factory=list)
    
    # State tracking
    pending_clarifications: List[str] = field(default_factory=list)
    awaiting_confirmation: bool = False
    confirmation_action: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def progress_percentage(self) -> float:
        """Calculate conversation progress (0-100)."""
        if not self.required_fields:
            return 100.0
        return (len(self.completed_fields) / len(self.required_fields)) * 100


# ============================================================================
# Jarvis-Style Conversation Manager
# ============================================================================

class JarvisConversationManager:
    """
    Multi-step conversation manager inspired by Jarvis (Iron Man's AI).
    
    Features:
    - Chain-of-thought conversations with memory
    - Intelligent follow-up questions
    - Context-aware clarifications
    - Multi-step task workflows
    - Natural dialogue flow
    """
    
    def __init__(self, use_gpt: bool = True):
        self.conversations: Dict[str, MultiStepConversation] = {}
        self.use_gpt = use_gpt and OPENAI_AVAILABLE
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for GPT."""
        return """You are Jarvis, an intelligent voice assistant inspired by Iron Man's AI.
        
Your capabilities:
- Engage in natural, multi-turn conversations
- Remember context from previous messages
- Ask clarifying questions when needed
- Guide users through multi-step processes
- Summarize extracted information
- Confirm actions before executing
- Use friendly, professional tone

When responding:
1. Reference previous context naturally
2. Ask ONE focused clarifying question if needed
3. Confirm understanding of the user's intent
4. Provide next logical step
5. Be proactive but respect user autonomy

Format responses naturally - conversational, not robotic."""
    
    def start_conversation(self, conversation_id: str, 
                          dialogue_type: DialogueType = DialogueType.QUESTION_ANSWER,
                          required_fields: Optional[List[str]] = None) -> MultiStepConversation:
        """Start new multi-step conversation."""
        conv = MultiStepConversation(
            conversation_id=conversation_id,
            dialogue_type=dialogue_type,
            state=ConversationState.LISTENING,
            required_fields=required_fields or []
        )
        self.conversations[conversation_id] = conv
        return conv
    
    def add_user_message(self, conversation_id: str, user_text: str) -> Dict[str, Any]:
        """Process user message and generate response."""
        if conversation_id not in self.conversations:
            self.start_conversation(conversation_id)
        
        conv = self.conversations[conversation_id]
        
        # Add user turn
        turn_number = len(conv.turns) + 1
        user_turn = DialogueTurn(
            turn_number=turn_number,
            speaker='user',
            text=user_text
        )
        conv.turns.append(user_turn)
        
        # Update state
        conv.state = ConversationState.PROCESSING
        conv.updated_at = datetime.now()
        
        # Extract intent and data
        intent_data = self._parse_user_intent(conv, user_text)
        user_turn.parsed_intent = intent_data.get('intent')
        user_turn.extracted_data = intent_data.get('data')
        
        # Update collected data
        if user_turn.extracted_data:
            conv.collected_data.update(user_turn.extracted_data)
            # Mark fields as completed
            for field in user_turn.extracted_data.keys():
                if field in conv.required_fields and field not in conv.completed_fields:
                    conv.completed_fields.append(field)
        
        # Generate assistant response
        response = self._generate_response(conv, user_text)
        
        # Add assistant turn
        assistant_turn = DialogueTurn(
            turn_number=turn_number + 1,
            speaker='assistant',
            text=response
        )
        conv.turns.append(assistant_turn)
        
        # Determine next state
        conv.state = self._determine_next_state(conv)
        
        return {
            'conversation_id': conversation_id,
            'turn_number': turn_number,
            'user_message': user_text,
            'assistant_response': response,
            'progress': conv.progress_percentage(),
            'state': conv.state.value,
            'collected_data': conv.collected_data,
            'pending_clarifications': conv.pending_clarifications
        }
    
    def _parse_user_intent(self, conv: MultiStepConversation, 
                          user_text: str) -> Dict[str, Any]:
        """Parse user intent and extract data."""
        
        if not self.use_gpt:
            return self._parse_intent_rules(conv, user_text)
        
        return self._parse_intent_gpt(conv, user_text)
    
    def _parse_intent_rules(self, conv: MultiStepConversation, 
                           user_text: str) -> Dict[str, Any]:
        """Rule-based intent parsing."""
        import re
        
        intent = {'type': 'general', 'confidence': 0.5}
        data = {}
        
        # Detect affirmation/negation
        if re.search(r'\b(yes|yeah|yep|sure|okay|ok|alright)\b', user_text, re.I):
            intent['type'] = 'affirmation'
        elif re.search(r'\b(no|nope|nah|never|negative)\b', user_text, re.I):
            intent['type'] = 'negation'
        
        # Extract time if scheduling
        if conv.dialogue_type == DialogueType.SCHEDULING:
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', user_text, re.I)
            if time_match:
                data['time'] = time_match.group(0)
                intent['type'] = 'time_specification'
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(hour|hr|minute|min)', user_text, re.I)
        if duration_match:
            data['duration'] = duration_match.group(0)
        
        # Extract dates
        date_keywords = {
            'today': 'today',
            'tomorrow': 'tomorrow',
            'tonight': 'tonight',
            'monday': 'monday',
            'tuesday': 'tuesday',
            'wednesday': 'wednesday',
            'thursday': 'thursday',
            'friday': 'friday',
            'weekend': 'weekend'
        }
        
        for keyword, value in date_keywords.items():
            if keyword in user_text.lower():
                data['date'] = value
                intent['type'] = 'date_specification'
                break
        
        return {'intent': intent, 'data': data}
    
    def _parse_intent_gpt(self, conv: MultiStepConversation, 
                         user_text: str) -> Dict[str, Any]:
        """GPT-based intent parsing."""
        if not OPENAI_AVAILABLE:
            return self._parse_intent_rules(conv, user_text)
        
        try:
            context = self._get_conversation_context(conv)
            
            prompt = f"""Conversation context:
{context}

Latest user message: "{user_text}"

Dialogue type: {conv.dialogue_type.value}
Required fields: {conv.required_fields}
Completed fields: {conv.completed_fields}

Parse the user's intent and extract any relevant data.
Respond with JSON:
{{
    "intent": {{
        "type": "affirmation|negation|question|specification|other",
        "confidence": 0.0-1.0,
        "description": "brief description"
    }},
    "extracted_data": {{
        "field_name": "value"
    }},
    "clarification_needed": "field_name or null"
}}"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            result = json.loads(response['choices'][0]['message']['content'])
            return {
                'intent': result.get('intent'),
                'data': result.get('extracted_data', {})
            }
        
        except Exception as e:
            print(f"[WARN] GPT parsing failed: {e}")
            return self._parse_intent_rules(conv, user_text)
    
    def _generate_response(self, conv: MultiStepConversation, 
                          user_text: str) -> str:
        """Generate contextual response."""
        
        if not self.use_gpt:
            return self._generate_response_rules(conv, user_text)
        
        return self._generate_response_gpt(conv, user_text)
    
    def _generate_response_rules(self, conv: MultiStepConversation, 
                                user_text: str) -> str:
        """Rule-based response generation."""
        import re
        
        # Check missing fields
        missing_fields = [f for f in conv.required_fields if f not in conv.completed_fields]
        
        if missing_fields:
            next_field = missing_fields[0]
            questions = {
                'time': "When would you like to schedule this?",
                'duration': "How long should this take?",
                'date': "What day works for you?",
                'recipient': "Who should I send this to?",
                'subject': "What's this about?",
                'priority': "How urgent is this?",
                'location': "Where will this be?"
            }
            return questions.get(next_field, f"Tell me about the {next_field}.")
        
        # If all fields collected, confirm
        if conv.collected_data:
            collected_summary = ", ".join([f"{k}: {v}" for k, v in conv.collected_data.items()])
            return f"Perfect. So to confirm: {collected_summary}. Sound good?"
        
        # Generic response
        return "Got it. Anything else?"
    
    def _generate_response_gpt(self, conv: MultiStepConversation, 
                              user_text: str) -> str:
        """GPT-based response generation."""
        if not OPENAI_AVAILABLE:
            return self._generate_response_rules(conv, user_text)
        
        try:
            context = self._get_conversation_context(conv)
            
            prompt = f"""{self.system_prompt}

{context}

Required fields: {conv.required_fields}
Completed fields: {conv.completed_fields}
Collected data: {conv.collected_data}

Generate a natural follow-up response to continue the conversation.
Be concise (1-2 sentences). If more information is needed, ask ONE focused question.
If all info is collected, confirm the details."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )
            
            return response['choices'][0]['message']['content'].strip()
        
        except Exception as e:
            print(f"[WARN] GPT response generation failed: {e}")
            return self._generate_response_rules(conv, user_text)
    
    def _get_conversation_context(self, conv: MultiStepConversation) -> str:
        """Get formatted conversation context for GPT."""
        context = f"Dialogue type: {conv.dialogue_type.value}\n"
        context += f"Progress: {conv.progress_percentage():.0f}% complete\n\n"
        context += "Recent turns:\n"
        
        # Include last 3 turns
        for turn in conv.turns[-6:]:
            context += f"{turn.speaker.upper()}: {turn.text}\n"
        
        return context
    
    def _determine_next_state(self, conv: MultiStepConversation) -> ConversationState:
        """Determine conversation state after processing."""
        # Check if all required fields are collected
        missing_fields = [f for f in conv.required_fields if f not in conv.completed_fields]
        
        if not missing_fields and conv.collected_data:
            return ConversationState.WAITING_FOR_CONFIRMATION
        
        if missing_fields:
            return ConversationState.LISTENING
        
        return ConversationState.COMPLETED
    
    def confirm_action(self, conversation_id: str) -> Dict[str, Any]:
        """Confirm collected data and prepare for action."""
        if conversation_id not in self.conversations:
            return {'status': 'error', 'message': 'Conversation not found'}
        
        conv = self.conversations[conversation_id]
        conv.awaiting_confirmation = False
        conv.state = ConversationState.TASK_IN_PROGRESS
        
        return {
            'status': 'confirmed',
            'conversation_id': conversation_id,
            'collected_data': conv.collected_data,
            'dialogue_type': conv.dialogue_type.value
        }
    
    def cancel_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Cancel conversation and clean up."""
        if conversation_id in self.conversations:
            conv = self.conversations[conversation_id]
            conv.state = ConversationState.IDLE
            return {
                'status': 'cancelled',
                'conversation_id': conversation_id,
                'collected_data': conv.collected_data
            }
        return {'status': 'error', 'message': 'Conversation not found'}
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get summary of conversation."""
        if conversation_id not in self.conversations:
            return {}
        
        conv = self.conversations[conversation_id]
        
        return {
            'conversation_id': conversation_id,
            'type': conv.dialogue_type.value,
            'state': conv.state.value,
            'turns': len(conv.turns),
            'progress': conv.progress_percentage(),
            'collected_data': conv.collected_data,
            'required_fields': conv.required_fields,
            'completed_fields': conv.completed_fields,
            'created_at': conv.created_at.isoformat(),
            'last_turn': conv.turns[-1].text if conv.turns else None
        }
    
    def get_next_clarification_needed(self, conversation_id: str) -> Optional[str]:
        """Get next field that needs clarification."""
        if conversation_id not in self.conversations:
            return None
        
        conv = self.conversations[conversation_id]
        missing_fields = [f for f in conv.required_fields if f not in conv.completed_fields]
        
        return missing_fields[0] if missing_fields else None


# ============================================================================
# Example Conversation Workflows
# ============================================================================

class SchedulingWorkflow:
    """Multi-step workflow for scheduling meetings."""
    
    REQUIRED_FIELDS = ['date', 'time', 'duration', 'participant']
    
    @staticmethod
    def start(manager: JarvisConversationManager, 
              conversation_id: str) -> MultiStepConversation:
        """Start scheduling workflow."""
        return manager.start_conversation(
            conversation_id,
            dialogue_type=DialogueType.SCHEDULING,
            required_fields=SchedulingWorkflow.REQUIRED_FIELDS
        )


class TaskCreationWorkflow:
    """Multi-step workflow for creating tasks."""
    
    REQUIRED_FIELDS = ['title', 'deadline', 'priority']
    
    @staticmethod
    def start(manager: JarvisConversationManager, 
              conversation_id: str) -> MultiStepConversation:
        """Start task creation workflow."""
        return manager.start_conversation(
            conversation_id,
            dialogue_type=DialogueType.TASK_CREATION,
            required_fields=TaskCreationWorkflow.REQUIRED_FIELDS
        )


class MeetingAssistantWorkflow:
    """Multi-step workflow for assisting with meetings."""
    
    REQUIRED_FIELDS = ['meeting_type', 'attendees', 'duration', 'topic']
    
    @staticmethod
    def start(manager: JarvisConversationManager, 
              conversation_id: str) -> MultiStepConversation:
        """Start meeting assistant workflow."""
        return manager.start_conversation(
            conversation_id,
            dialogue_type=DialogueType.QUESTION_ANSWER,
            required_fields=MeetingAssistantWorkflow.REQUIRED_FIELDS
        )


# ============================================================================
# Quick Helper Functions
# ============================================================================

def create_jarvis_manager(use_gpt: bool = True) -> JarvisConversationManager:
    """Quick factory to create conversation manager."""
    return JarvisConversationManager(use_gpt=use_gpt)


def quick_scheduling_conversation(conversation_id: str, 
                                  user_messages: List[str]) -> Dict[str, Any]:
    """Quick example of multi-turn scheduling conversation."""
    manager = JarvisConversationManager(use_gpt=False)
    
    # Start scheduling workflow
    SchedulingWorkflow.start(manager, conversation_id)
    
    # Process each message
    results = []
    for msg in user_messages:
        result = manager.add_user_message(conversation_id, msg)
        results.append(result)
    
    # Get final summary
    summary = manager.get_conversation_summary(conversation_id)
    
    return {
        'turns': results,
        'summary': summary
    }
