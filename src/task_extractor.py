"""
Task Extraction from Conversations Module

Automatically detects tasks, reminders, and action items from natural language
conversations. Uses NLU + GPT to identify obligations, deadlines, and priorities.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
import re

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# ============================================================================
# Data Structures & Enums
# ============================================================================

class TaskType(Enum):
    """Type of extracted task."""
    REMINDER = "reminder"          # Time-based alert
    DEADLINE = "deadline"          # Due date task
    ACTION_ITEM = "action_item"   # Must-do task
    MEETING = "meeting"           # Scheduled meeting
    FOLLOW_UP = "follow_up"       # Action to follow up on
    DECISION = "decision"         # Decision to make
    QUESTION = "question"         # Question to answer
    LEARNING = "learning"         # Learning objective


class TaskPriority(Enum):
    """Task priority level."""
    CRITICAL = "critical"  # Must do immediately
    HIGH = "high"         # Important, soon
    MEDIUM = "medium"     # Normal priority
    LOW = "low"           # Can wait


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"           # Not yet started
    IN_PROGRESS = "in_progress"   # Currently working
    WAITING = "waiting"           # Blocked/waiting for something
    COMPLETED = "completed"       # Done
    CANCELLED = "cancelled"       # No longer needed


@dataclass
class TaskExtraction:
    """Extracted task from conversation."""
    task_id: str = ""
    task_type: TaskType = TaskType.ACTION_ITEM
    title: str = ""
    description: str = ""
    deadline: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    confidence: float = 0.0  # 0-1 confidence score
    source_text: str = ""  # Original text extracted from
    related_entities: List[str] = field(default_factory=list)  # People, places, projects
    reminder_before: Optional[int] = None  # Minutes before deadline
    extracted_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'type': self.task_type.value,
            'title': self.title,
            'description': self.description,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'priority': self.priority.value,
            'status': self.status.value,
            'confidence': self.confidence,
            'related_entities': self.related_entities,
            'reminder_before': self.reminder_before
        }


@dataclass
class ConversationContext:
    """Maintains context across multi-turn conversations."""
    conversation_id: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)  # [{'role': 'user'/'assistant', 'content': '...'}]
    extracted_tasks: List[TaskExtraction] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)  # Tracked entities
    pending_questions: List[str] = field(default_factory=list)  # Questions waiting for user input
    context_depth: int = 0  # How many turns of context to keep
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


# ============================================================================
# Task Extraction Engine
# ============================================================================

class TaskExtractor:
    """Extracts tasks and action items from natural language text."""
    
    # Task indicator keywords
    DEADLINE_KEYWORDS = [
        r'(?:by|before|until|due|deadline)\s+(.+?)(?:\.|,|$)',
        r'(?:by|before)\s+(?:the\s+)?(\w+day|tomorrow|next\s+\w+)',
        r'(?:deadline|due date)\s+(?:is\s+)?(.+?)(?:\.|,|$)',
    ]
    
    REMINDER_KEYWORDS = [
        r'(?:remind|remember|don\'t forget)\s+(?:me\s+)?(?:to\s+)?(.+?)(?:\.|,|$)',
        r'(?:i\s+)?(?:must|should|need|have\s+to)\s+(?:remember\s+)?(.+?)(?:\.|,|$)',
        r'(?:i\s+)?(?:might\s+)?(?:forget|miss)\s+(.+?)(?:\.|,|$)',
    ]
    
    ACTION_KEYWORDS = [
        r'(?:i\s+)?(?:must|should|need\s+to|have\s+to|ought\s+to)\s+(.+?)(?:\.|,|$)',
        r'(?:can\'t\s+)?forget.*?(?:to\s+)?(.+?)(?:\.|,|$)',
        r'(?:need\s+|want\s+)?(?:me\s+)?to\s+(.+?)(?:\.|,|$)',
    ]
    
    PRIORITY_KEYWORDS = {
        'critical': ['urgent', 'asap', 'critical', 'emergency', 'immediately', 'right now'],
        'high': ['important', 'soon', 'this week', 'quickly', 'must', 'should'],
        'medium': ['eventually', 'when you can', 'sometime'],
        'low': ['no rush', 'whenever', 'later', 'optional'],
    }
    
    def __init__(self, use_gpt: bool = False, confidence_threshold: float = 0.5):
        self.use_gpt = use_gpt and OPENAI_AVAILABLE
        self.confidence_threshold = confidence_threshold
        self.task_counter = 0
    
    def extract_tasks(self, text: str) -> List[TaskExtraction]:
        """
        Extract all tasks from given text.
        
        Args:
            text: Natural language input
            
        Returns:
            List of extracted TaskExtraction objects
        """
        tasks = []
        
        # Rule-based extraction
        tasks.extend(self._extract_deadlines(text))
        tasks.extend(self._extract_reminders(text))
        tasks.extend(self._extract_action_items(text))
        
        # GPT-based extraction if available
        if self.use_gpt:
            gpt_tasks = self._extract_with_gpt(text)
            tasks.extend(gpt_tasks)
        
        # Filter by confidence threshold
        tasks = [t for t in tasks if t.confidence >= self.confidence_threshold]
        
        # Assign unique IDs
        for task in tasks:
            self.task_counter += 1
            task.task_id = f"task_{self.task_counter}"
        
        return tasks
    
    def _extract_deadlines(self, text: str) -> List[TaskExtraction]:
        """Extract deadline-based tasks."""
        tasks = []
        
        for pattern in self.DEADLINE_KEYWORDS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                task_text = match.group(1) if match.groups() else match.group(0)
                
                # Parse deadline
                deadline = self._parse_deadline(match.group(0))
                
                if deadline:
                    priority = self._detect_priority(text)
                    task = TaskExtraction(
                        task_type=TaskType.DEADLINE,
                        title=task_text[:50],
                        description=f"Deadline task: {task_text}",
                        deadline=deadline,
                        priority=priority,
                        confidence=0.85,
                        source_text=text[:100],
                        reminder_before=1440 if priority == TaskPriority.HIGH else 480
                    )
                    tasks.append(task)
        
        return tasks
    
    def _extract_reminders(self, text: str) -> List[TaskExtraction]:
        """Extract reminder-based tasks."""
        tasks = []
        
        for pattern in self.REMINDER_KEYWORDS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                task_text = match.group(1) if match.groups() else match.group(0)
                
                priority = self._detect_priority(text)
                task = TaskExtraction(
                    task_type=TaskType.REMINDER,
                    title=task_text[:50],
                    description=f"Reminder: {task_text}",
                    priority=priority,
                    confidence=0.80,
                    source_text=text[:100],
                    reminder_before=60  # Remind 1 hour before
                )
                tasks.append(task)
        
        return tasks
    
    def _extract_action_items(self, text: str) -> List[TaskExtraction]:
        """Extract action-based tasks."""
        tasks = []
        
        for pattern in self.ACTION_KEYWORDS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                task_text = match.group(1) if match.groups() else match.group(0)
                
                priority = self._detect_priority(text)
                task = TaskExtraction(
                    task_type=TaskType.ACTION_ITEM,
                    title=task_text[:50],
                    description=f"Action item: {task_text}",
                    priority=priority,
                    confidence=0.75,
                    source_text=text[:100]
                )
                tasks.append(task)
        
        return tasks
    
    def _parse_deadline(self, text: str) -> Optional[datetime]:
        """Parse deadline from text."""
        text_lower = text.lower()
        now = datetime.now()
        
        # Relative dates
        if 'tomorrow' in text_lower:
            return now + timedelta(days=1)
        elif 'today' in text_lower:
            return now
        elif 'this week' in text_lower:
            return now + timedelta(days=7)
        elif 'next week' in text_lower:
            return now + timedelta(days=14)
        elif 'end of week' in text_lower or 'friday' in text_lower:
            days_until_friday = (4 - now.weekday()) % 7
            return now + timedelta(days=days_until_friday if days_until_friday > 0 else 7)
        elif 'next monday' in text_lower:
            days_until_monday = (7 - now.weekday()) % 7
            return now + timedelta(days=days_until_monday if days_until_monday > 0 else 7)
        elif 'thursday' in text_lower:
            days_until_thursday = (3 - now.weekday()) % 7
            return now + timedelta(days=days_until_thursday if days_until_thursday > 0 else 7)
        
        # Extract numbers
        match = re.search(r'in\s+(\d+)\s+(days?|weeks?|hours?)', text_lower)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            if 'day' in unit:
                return now + timedelta(days=value)
            elif 'week' in unit:
                return now + timedelta(weeks=value)
            elif 'hour' in unit:
                return now + timedelta(hours=value)
        
        return None
    
    def _detect_priority(self, text: str) -> TaskPriority:
        """Detect task priority from text."""
        text_lower = text.lower()
        
        for priority_level, keywords in self.PRIORITY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return TaskPriority[priority_level.upper()]
        
        return TaskPriority.MEDIUM
    
    def _extract_with_gpt(self, text: str) -> List[TaskExtraction]:
        """Extract tasks using GPT."""
        if not OPENAI_AVAILABLE:
            return []
        
        try:
            prompt = f"""Extract all tasks, reminders, deadlines, and action items from this text.
            
Text: "{text}"

For each task, provide:
- Type (reminder/deadline/action_item/meeting/follow_up)
- Title (short description)
- Deadline (if mentioned)
- Priority (critical/high/medium/low)

Format as JSON array: {{"tasks": [...]}}"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            import json
            data = json.loads(response['choices'][0]['message']['content'])
            tasks = []
            
            for task_data in data.get('tasks', []):
                task = TaskExtraction(
                    task_type=TaskType[task_data.get('type', 'ACTION_ITEM').upper()],
                    title=task_data.get('title', ''),
                    description=task_data.get('description', ''),
                    priority=TaskPriority[task_data.get('priority', 'MEDIUM').upper()],
                    confidence=0.90,
                    source_text=text[:100]
                )
                tasks.append(task)
            
            return tasks
        
        except Exception as e:
            print(f"[WARN] GPT extraction failed: {e}")
            return []
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities (people, projects, dates)."""
        entities = {
            'people': [],
            'projects': [],
            'dates': [],
            'locations': []
        }
        
        # Simple entity extraction
        # People (capitalized words)
        people_pattern = r'(?:with|to|from|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        entities['people'] = re.findall(people_pattern, text)
        
        # Dates (explicit mentions)
        entities['dates'] = self._extract_date_mentions(text)
        
        # Projects (quoted or capitalized sequences)
        project_pattern = r'"([^"]+)"|(?:project|task|initiative)\s+([A-Za-z0-9\s]+)'
        entities['projects'] = re.findall(project_pattern, text)
        
        return entities
    
    def _extract_date_mentions(self, text: str) -> List[str]:
        """Extract date mentions."""
        dates = []
        patterns = [
            r'\b(tomorrow|today|tonight)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
        ]
        
        for pattern in patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return dates


# ============================================================================
# Conversation Manager with Memory
# ============================================================================

class ConversationManager:
    """Manages multi-turn conversations with context and memory."""
    
    def __init__(self, max_context_turns: int = 5, use_gpt: bool = False):
        self.conversations: Dict[str, ConversationContext] = {}
        self.max_context_turns = max_context_turns
        self.use_gpt = use_gpt and OPENAI_AVAILABLE
        self.task_extractor = TaskExtractor(use_gpt=use_gpt)
    
    def start_conversation(self, conversation_id: str) -> ConversationContext:
        """Start new conversation context."""
        context = ConversationContext(
            conversation_id=conversation_id,
            context_depth=0
        )
        self.conversations[conversation_id] = context
        return context
    
    def add_message(self, conversation_id: str, role: str, content: str) -> ConversationContext:
        """Add message to conversation."""
        if conversation_id not in self.conversations:
            self.start_conversation(conversation_id)
        
        context = self.conversations[conversation_id]
        context.messages.append({'role': role, 'content': content})
        context.last_updated = datetime.now()
        context.context_depth += 1
        
        # Extract tasks from user message
        if role == 'user':
            tasks = self.task_extractor.extract_tasks(content)
            context.extracted_tasks.extend(tasks)
            
            # Extract entities
            entities = self.task_extractor.extract_entities(content)
            for entity_type, entity_list in entities.items():
                if entity_list:
                    context.entities[entity_type] = entity_list
        
        return context
    
    def get_context_summary(self, conversation_id: str) -> str:
        """Get summary of conversation context."""
        if conversation_id not in self.conversations:
            return ""
        
        context = self.conversations[conversation_id]
        
        summary = f"Conversation {conversation_id}:\n"
        summary += f"Turns: {context.context_depth}\n"
        
        if context.extracted_tasks:
            summary += f"Tasks extracted: {len(context.extracted_tasks)}\n"
            for task in context.extracted_tasks[-3:]:  # Last 3 tasks
                summary += f"  - {task.task_type.value}: {task.title}\n"
        
        if context.entities:
            summary += f"Entities: {context.entities}\n"
        
        if context.pending_questions:
            summary += f"Pending: {context.pending_questions}\n"
        
        return summary
    
    def get_context_for_gpt(self, conversation_id: str) -> str:
        """Get formatted context for GPT prompt."""
        if conversation_id not in self.conversations:
            return ""
        
        context = self.conversations[conversation_id]
        
        # Keep last N messages
        relevant_messages = context.messages[-self.max_context_turns:]
        
        context_text = "Conversation history:\n"
        for msg in relevant_messages:
            context_text += f"{msg['role'].upper()}: {msg['content']}\n"
        
        # Add extracted tasks
        if context.extracted_tasks:
            context_text += "\nExtracted tasks:\n"
            for task in context.extracted_tasks:
                context_text += f"- {task.task_type.value}: {task.title}\n"
        
        # Add entities
        if context.entities:
            context_text += f"\nTracked entities: {context.entities}\n"
        
        return context_text
    
    def generate_follow_up_question(self, conversation_id: str, 
                                   user_message: str) -> str:
        """Generate contextual follow-up question."""
        context = self.conversations.get(conversation_id)
        if not context:
            return ""
        
        if not self.use_gpt:
            return self._generate_rule_based_question(context, user_message)
        
        return self._generate_gpt_question(context, user_message)
    
    def _generate_rule_based_question(self, context: ConversationContext, 
                                     user_message: str) -> str:
        """Generate follow-up using rules."""
        # Check for incomplete tasks
        incomplete_keywords = {
            'when': ['schedule', 'meeting', 'event', 'appointment', 'session'],
            'where': ['go', 'travel', 'visit', 'meet'],
            'who': ['call', 'contact', 'email', 'message'],
            'how': ['method', 'approach', 'way', 'process'],
            'duration': ['session', 'meeting', 'call', 'class', 'lesson']
        }
        
        for question_type, keywords in incomplete_keywords.items():
            if any(kw in user_message.lower() for kw in keywords):
                questions = {
                    'when': "When would you like to schedule this?",
                    'where': "Where is this taking place?",
                    'who': "Who do you need to contact?",
                    'how': "How do you want to approach this?",
                    'duration': "How long should this take?"
                }
                return questions.get(question_type, "")
        
        return ""
    
    def _generate_gpt_question(self, context: ConversationContext, 
                              user_message: str) -> str:
        """Generate follow-up using GPT."""
        if not OPENAI_AVAILABLE:
            return ""
        
        try:
            context_text = self.get_context_for_gpt(context.conversation_id)
            
            prompt = f"""{context_text}

Based on this conversation, what clarifying question should the assistant ask next?
Respond with ONLY the question, no explanation."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            return response['choices'][0]['message']['content'].strip()
        
        except Exception as e:
            print(f"[WARN] GPT question generation failed: {e}")
            return ""
    
    def clear_context(self, conversation_id: str):
        """Clear conversation context."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    def get_all_extracted_tasks(self, conversation_id: str) -> List[TaskExtraction]:
        """Get all tasks extracted from conversation."""
        if conversation_id not in self.conversations:
            return []
        return self.conversations[conversation_id].extracted_tasks


# ============================================================================
# Integration Helper Functions
# ============================================================================

def quick_task_extraction(text: str) -> List[TaskExtraction]:
    """Quick task extraction without GPT."""
    extractor = TaskExtractor(use_gpt=False)
    return extractor.extract_tasks(text)


def quick_conversation_turn(conversation_id: str, user_message: str,
                           assistant_response: str = None) -> Dict[str, Any]:
    """Quick helper for a conversation turn."""
    manager = ConversationManager(use_gpt=False)
    
    # Initialize if needed
    if conversation_id not in manager.conversations:
        manager.start_conversation(conversation_id)
    
    # Add user message
    manager.add_message(conversation_id, 'user', user_message)
    
    # Get context
    context = manager.conversations[conversation_id]
    
    # Generate follow-up question
    follow_up = manager.generate_follow_up_question(conversation_id, user_message)
    
    # Add assistant response if provided
    if assistant_response:
        manager.add_message(conversation_id, 'assistant', assistant_response)
    
    return {
        'conversation_id': conversation_id,
        'user_message': user_message,
        'extracted_tasks': [t.to_dict() for t in context.extracted_tasks],
        'follow_up_question': follow_up,
        'context_summary': manager.get_context_summary(conversation_id),
        'entities': context.entities
    }
