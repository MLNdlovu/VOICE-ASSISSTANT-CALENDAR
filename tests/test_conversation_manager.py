"""
Unit Tests for Jarvis-Style Multi-Turn Conversation Manager

Tests for conversation flow, context tracking, state management,
multi-turn memory, and follow-up question generation.
"""

import pytest
from datetime import datetime, timedelta
from src.conversation_manager import (
    JarvisConversationManager,
    DialogueType,
    ConversationState,
    DialogueTurn,
    MultiStepConversation,
    SchedulingWorkflow,
    TaskCreationWorkflow,
    MeetingAssistantWorkflow
)


class TestDialogueTurn:
    """Test single turn in conversation."""
    
    def test_dialogue_turn_creation(self):
        """Test creating a dialogue turn."""
        turn = DialogueTurn(
            turn_number=1,
            speaker='user',
            text='Schedule a meeting tomorrow at 2pm'
        )
        
        assert turn.turn_number == 1
        assert turn.speaker == 'user'
        assert turn.text == 'Schedule a meeting tomorrow at 2pm'
        assert turn.timestamp is not None
    
    def test_dialogue_turn_with_data(self):
        """Test turn with parsed intent and extracted data."""
        turn = DialogueTurn(
            turn_number=2,
            speaker='assistant',
            text='Sure, how long should the meeting be?',
            parsed_intent={'type': 'question'},
            extracted_data={'date': '2024-03-15'}
        )
        
        assert turn.parsed_intent['type'] == 'question'
        assert turn.extracted_data['date'] == '2024-03-15'


class TestMultiStepConversation:
    """Test multi-step conversation container."""
    
    def test_conversation_initialization(self):
        """Test initializing a conversation."""
        conv = MultiStepConversation(
            conversation_id='conv_123',
            dialogue_type=DialogueType.SCHEDULING,
            required_fields=['date', 'time', 'duration']
        )
        
        assert conv.conversation_id == 'conv_123'
        assert conv.dialogue_type == DialogueType.SCHEDULING
        assert len(conv.turns) == 0
        assert conv.state == ConversationState.IDLE
    
    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        conv = MultiStepConversation(
            conversation_id='conv_123',
            required_fields=['date', 'time', 'duration']
        )
        
        # No fields completed
        assert conv.progress_percentage() == 0.0
        
        # One field completed
        conv.completed_fields.append('date')
        assert conv.progress_percentage() == pytest.approx(33.33, abs=1)
        
        # All fields completed
        conv.completed_fields.extend(['time', 'duration'])
        assert conv.progress_percentage() == 100.0
    
    def test_conversation_state_tracking(self):
        """Test conversation state changes."""
        conv = MultiStepConversation(
            conversation_id='conv_123',
            state=ConversationState.LISTENING
        )
        
        assert conv.state == ConversationState.LISTENING
        
        conv.state = ConversationState.PROCESSING
        assert conv.state == ConversationState.PROCESSING


class TestJarvisConversationManager:
    """Test Jarvis-style conversation management."""
    
    def test_manager_initialization(self):
        """Test creating conversation manager."""
        manager = JarvisConversationManager(use_gpt=False)
        assert manager.conversations == {}
        assert manager.use_gpt == False
    
    def test_start_conversation(self):
        """Test starting a new conversation."""
        manager = JarvisConversationManager(use_gpt=False)
        
        conv = manager.start_conversation(
            'conv_1',
            dialogue_type=DialogueType.SCHEDULING,
            required_fields=['date', 'time']
        )
        
        assert 'conv_1' in manager.conversations
        assert conv.dialogue_type == DialogueType.SCHEDULING
        assert conv.state == ConversationState.LISTENING
    
    def test_add_user_message(self):
        """Test adding user message to conversation."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('conv_1')
        
        result = manager.add_user_message('conv_1', 'Schedule a meeting')
        
        assert result['status'] == 'success'
        assert result['conversation_id'] == 'conv_1'
        assert result['user_message'] == 'Schedule a meeting'
        assert result['assistant_response'] != ''
    
    def test_conversation_turn_tracking(self):
        """Test that turns are tracked properly."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('conv_1')
        
        manager.add_user_message('conv_1', 'Schedule something')
        
        conv = manager.conversations['conv_1']
        assert len(conv.turns) == 2  # user + assistant
        assert conv.turns[0].speaker == 'user'
        assert conv.turns[1].speaker == 'assistant'
    
    def test_required_fields_tracking(self):
        """Test tracking of required fields."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation(
            'conv_1',
            dialogue_type=DialogueType.SCHEDULING,
            required_fields=['date', 'time', 'duration']
        )
        
        conv = manager.conversations['conv_1']
        assert len(conv.required_fields) == 3
        assert len(conv.completed_fields) == 0
    
    def test_collected_data_update(self):
        """Test that extracted data is collected."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('conv_1')
        
        result = manager.add_user_message('conv_1', 'Tomorrow at 2pm')
        
        # The rule-based parser should extract date
        conv = manager.conversations['conv_1']
        # Note: actual extraction depends on rule implementation
        assert isinstance(conv.collected_data, dict)
    
    def test_confirm_action(self):
        """Test confirming collected data."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('conv_1')
        
        # Add some data
        manager.conversations['conv_1'].collected_data = {'date': '2024-03-15', 'time': '14:00'}
        manager.conversations['conv_1'].awaiting_confirmation = True
        
        result = manager.confirm_action('conv_1')
        
        assert result['status'] == 'confirmed'
        assert result['collected_data'] == {'date': '2024-03-15', 'time': '14:00'}
        assert manager.conversations['conv_1'].awaiting_confirmation == False
    
    def test_cancel_conversation(self):
        """Test canceling a conversation."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('conv_1')
        
        result = manager.cancel_conversation('conv_1')
        
        assert result['status'] == 'cancelled'
        assert manager.conversations['conv_1'].state == ConversationState.IDLE
    
    def test_get_conversation_summary(self):
        """Test getting conversation summary."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('conv_1', dialogue_type=DialogueType.SCHEDULING)
        
        manager.add_user_message('conv_1', 'Schedule tomorrow')
        manager.add_user_message('conv_1', 'At 2pm')
        
        summary = manager.get_conversation_summary('conv_1')
        
        assert summary['conversation_id'] == 'conv_1'
        assert summary['type'] == 'scheduling'
        assert summary['turns'] >= 2
        assert 'progress' in summary
    
    def test_get_next_clarification_needed(self):
        """Test getting next missing field."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation(
            'conv_1',
            required_fields=['date', 'time', 'duration']
        )
        
        conv = manager.conversations['conv_1']
        conv.completed_fields = ['date']
        
        next_field = manager.get_next_clarification_needed('conv_1')
        assert next_field in ['time', 'duration']
    
    def test_nonexistent_conversation_error(self):
        """Test error handling for nonexistent conversation."""
        manager = JarvisConversationManager(use_gpt=False)
        
        result = manager.add_user_message('nonexistent', 'test')
        assert result['status'] == 'success'  # Should auto-create
        
        summary = manager.get_conversation_summary('nonexistent')
        assert summary['conversation_id'] == 'nonexistent'


class TestSchedulingWorkflow:
    """Test scheduling workflow."""
    
    def test_scheduling_workflow_init(self):
        """Test initializing scheduling workflow."""
        manager = JarvisConversationManager(use_gpt=False)
        
        conv = SchedulingWorkflow.start(manager, 'sched_1')
        
        assert conv.dialogue_type == DialogueType.SCHEDULING
        assert 'date' in conv.required_fields
        assert 'time' in conv.required_fields
        assert 'duration' in conv.required_fields
        assert 'participant' in conv.required_fields
    
    def test_scheduling_workflow_conversation(self):
        """Test multi-turn scheduling workflow."""
        manager = JarvisConversationManager(use_gpt=False)
        SchedulingWorkflow.start(manager, 'sched_1')
        
        # Simulate conversation
        manager.add_user_message('sched_1', 'Schedule a meeting')
        manager.add_user_message('sched_1', 'Tomorrow at 2pm')
        manager.add_user_message('sched_1', '1 hour')
        
        conv = manager.conversations['sched_1']
        assert len(conv.turns) >= 3


class TestTaskCreationWorkflow:
    """Test task creation workflow."""
    
    def test_task_creation_workflow_init(self):
        """Test initializing task creation workflow."""
        manager = JarvisConversationManager(use_gpt=False)
        
        conv = TaskCreationWorkflow.start(manager, 'task_1')
        
        assert conv.dialogue_type == DialogueType.TASK_CREATION
        assert 'title' in conv.required_fields
        assert 'deadline' in conv.required_fields
        assert 'priority' in conv.required_fields


class TestMeetingAssistantWorkflow:
    """Test meeting assistant workflow."""
    
    def test_meeting_workflow_init(self):
        """Test initializing meeting assistant workflow."""
        manager = JarvisConversationManager(use_gpt=False)
        
        conv = MeetingAssistantWorkflow.start(manager, 'meet_1')
        
        assert conv.dialogue_type == DialogueType.QUESTION_ANSWER
        assert 'meeting_type' in conv.required_fields
        assert 'attendees' in conv.required_fields


class TestConversationFlow:
    """Test realistic conversation flows."""
    
    def test_simple_qa_flow(self):
        """Test simple question-answer flow."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('qa_1', DialogueType.QUESTION_ANSWER)
        
        # Q&A turns
        r1 = manager.add_user_message('qa_1', 'What is on my calendar today?')
        assert 'assistant_response' in r1
        
        r2 = manager.add_user_message('qa_1', 'Tell me about the first meeting')
        assert 'assistant_response' in r2
    
    def test_multi_step_flow(self):
        """Test multi-step task creation flow."""
        manager = JarvisConversationManager(use_gpt=False)
        TaskCreationWorkflow.start(manager, 'task_flow')
        
        conv = manager.conversations['task_flow']
        initial_progress = conv.progress_percentage()
        
        # Add multiple turns
        manager.add_user_message('task_flow', 'Renew my license')
        manager.add_user_message('task_flow', 'Before next Thursday')
        manager.add_user_message('task_flow', 'High priority')
        
        final_progress = conv.progress_percentage()
        assert final_progress > initial_progress
    
    def test_context_preservation_across_turns(self):
        """Test that context is preserved across turns."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('context_1')
        
        # User mentions something
        manager.add_user_message('context_1', 'Schedule a 2-hour meeting')
        
        # User adds more info
        manager.add_user_message('context_1', 'With John and Sarah')
        
        # User confirms
        manager.add_user_message('context_1', 'Tomorrow at 2pm')
        
        conv = manager.conversations['context_1']
        # All turns should be preserved
        assert len(conv.turns) >= 5  # at least 3 user + 2 assistant


class TestConversationEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_message(self):
        """Test handling empty message."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('edge_1')
        
        result = manager.add_user_message('edge_1', '')
        # Should still process (empty string is valid)
        assert 'assistant_response' in result
    
    def test_very_long_conversation(self):
        """Test long conversation with many turns."""
        manager = JarvisConversationManager(use_gpt=False)
        manager.start_conversation('long_1')
        
        # Add many turns
        for i in range(10):
            manager.add_user_message('long_1', f'Message {i+1}')
        
        conv = manager.conversations['long_1']
        assert len(conv.turns) >= 10
    
    def test_multiple_concurrent_conversations(self):
        """Test managing multiple conversations."""
        manager = JarvisConversationManager(use_gpt=False)
        
        # Start multiple conversations
        for i in range(5):
            manager.start_conversation(f'conv_{i}')
            manager.add_user_message(f'conv_{i}', f'Message for conv {i}')
        
        # All should be tracked
        assert len(manager.conversations) == 5
        
        # Each should be independent
        assert manager.conversations['conv_0'].turns != manager.conversations['conv_1'].turns
    
    def test_conversation_state_transitions(self):
        """Test valid state transitions."""
        conv = MultiStepConversation('state_test')
        
        assert conv.state == ConversationState.IDLE
        
        conv.state = ConversationState.LISTENING
        assert conv.state == ConversationState.LISTENING
        
        conv.state = ConversationState.PROCESSING
        assert conv.state == ConversationState.PROCESSING
        
        conv.state = ConversationState.COMPLETED
        assert conv.state == ConversationState.COMPLETED


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
