/**
 * Voice Assistant UI Controller
 * Handles voice interaction, animations, and real-time feedback
 */

class VoiceAssistantUI {
    constructor() {
        this.isListening = false;
        this.isSpeaking = false;
        this.currentTrigger = 'XX00';
        this.currentUserName = 'User';
        this.voiceSessionId = null;
        this.turnNumber = 1;
        this.transcript = [];
    }

    /**
     * Initialize voice assistant after login
     */
    async initializeVoiceAssistant() {
        try {
            // Show greeting UI
            this.showGreetingMessage();
            
            // Start voice session
            const response = await fetch('/api/voice/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            if (data.success) {
                this.voiceSessionId = data.session_id;
                this.currentTrigger = data.user_trigger;
                this.currentUserName = data.user_name;
                
                // Trigger greeting speech
                this.speakGreeting();
            }
        } catch (error) {
            console.error('Failed to initialize voice assistant:', error);
            this.showError('Voice assistant initialization failed');
        }
    }

    /**
     * Show greeting message in UI
     */
    showGreetingMessage() {
        const greeting = `Hello ${this.currentUserName}! Welcome back. Say your trigger word "${this.currentTrigger}" to activate voice commands.`;
        this.displayMessage('assistant', greeting);
    }

    /**
     * Speak greeting using Web Speech API or TTS
     */
    async speakGreeting() {
        const message = `Hello, what can I do for you today?`;
        
        try {
            // Use Web Speech API if available
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(message);
                utterance.rate = 0.9;
                utterance.pitch = 1.0;
                utterance.volume = 0.9;
                
                speechSynthesis.cancel();
                speechSynthesis.speak(utterance);
            }
        } catch (error) {
            console.error('Speech synthesis error:', error);
        }
    }

    /**
     * Start listening for voice input
     */
    async startListening() {
        try {
            this.isListening = true;
            this.updateVoiceIndicator('listening');
            
            // Use Web Speech API
            const recognition = this.getRecognition();
            if (!recognition) {
                this.showError('Speech recognition not supported in your browser');
                this.isListening = false;
                this.updateVoiceIndicator('idle');
                return;
            }
            
            recognition.onstart = () => {
                console.log('🎤 Listening...');
            };
            
            recognition.onresult = (event) => {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcriptSegment = event.results[i][0].transcript;
                    transcript += transcriptSegment;
                }
                
                this.displayMessage('user', transcript);
                this.processVoiceCommand(transcript);
            };
            
            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.showError(`Error: ${event.error}`);
            };
            
            recognition.onend = () => {
                this.isListening = false;
                this.updateVoiceIndicator('idle');
            };
            
            recognition.start();
        } catch (error) {
            console.error('Error starting voice input:', error);
            this.showError('Could not start voice recording');
            this.isListening = false;
            this.updateVoiceIndicator('idle');
        }
    }

    /**
     * Process voice command through backend
     */
    async processVoiceCommand(text) {
        try {
            const response = await fetch('/api/voice/process-command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    turn_number: this.turnNumber++
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // Display assistant response
                this.displayMessage('assistant', data.message);
                
                // Speak response
                this.speak(data.message);
                
                // Handle specific command types
                this.handleCommandType(data.command_type, data.parameters);
            } else {
                this.showError(data.error || 'Command processing failed');
            }
        } catch (error) {
            console.error('Error processing command:', error);
            this.showError('Failed to process command');
        }
    }

    /**
     * Handle different command types
     */
    handleCommandType(commandType, parameters) {
        switch (commandType) {
            case 'book_meeting':
                if (parameters.title && parameters.date && parameters.time) {
                    // Auto-fill booking form
                    document.getElementById('event-title').value = parameters.title;
                    document.getElementById('event-date').value = parameters.date;
                    document.getElementById('event-time').value = parameters.time;
                    document.getElementById('event-type').value = 'book';
                }
                break;
            
            case 'list_events':
                this.loadCalendarEvents(parameters.filter);
                break;
            
            case 'set_reminder':
                document.getElementById('event-type').value = 'remind';
                if (parameters.title) {
                    document.getElementById('event-title').value = parameters.title;
                }
                break;
        }
    }

    /**
     * Load calendar events to display
     */
    async loadCalendarEvents(filter = null) {
        try {
            const queryString = filter ? `?filter=${filter}` : '';
            const response = await fetch(`/api/events${queryString}`);
            const data = await response.json();
            
            if (data.success && data.events) {
                let summary = `You have ${data.events.length} events`;
                if (filter) {
                    summary += ` ${filter}`;
                }
                summary += ': ' + data.events.map(e => e.summary).join(', ');
                
                this.displayMessage('assistant', summary);
                this.speak(summary);
            }
        } catch (error) {
            console.error('Error loading events:', error);
        }
    }

    /**
     * Speak text using browser TTS
     */
    async speak(text) {
        try {
            this.isSpeaking = true;
            this.updateVoiceIndicator('speaking');
            
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 0.9;
                utterance.onend = () => {
                    this.isSpeaking = false;
                    this.updateVoiceIndicator('idle');
                };
                
                speechSynthesis.cancel();
                speechSynthesis.speak(utterance);
            }
        } catch (error) {
            console.error('Speech error:', error);
            this.isSpeaking = false;
            this.updateVoiceIndicator('idle');
        }
    }

    /**
     * Display message in transcript
     */
    displayMessage(speaker, text) {
        const transcript = document.getElementById('chat-history') || 
                          document.querySelector('.chat-history');
        
        if (transcript) {
            const messageEl = document.createElement('div');
            messageEl.className = `chat-message ${speaker === 'user' ? 'user' : 'ai'}`;
            messageEl.textContent = text;
            messageEl.style.animation = 'slideInRight 0.2s ease-out';
            
            transcript.appendChild(messageEl);
            transcript.scrollTop = transcript.scrollHeight;
        }
        
        // Store in transcript
        this.transcript.push({ speaker, text, timestamp: new Date() });
    }

    /**
     * Update voice indicator animation state
     */
    updateVoiceIndicator(state) {
        const indicator = document.querySelector('.voice-indicator');
        if (indicator) {
            indicator.classList.remove('listening', 'speaking', 'idle');
            indicator.classList.add(state);
        }
        
        const status = document.querySelector('.voice-status');
        if (status) {
            status.classList.remove('speaking', 'error');
            if (state === 'listening') {
                status.textContent = '🎤 Listening...';
                status.style.color = '#42a5f5';
            } else if (state === 'speaking') {
                status.classList.add('speaking');
                status.textContent = '🔊 Speaking...';
            } else {
                status.textContent = '⭕ Ready';
            }
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        this.displayMessage('error', message);
        
        const status = document.querySelector('.voice-status');
        if (status) {
            status.classList.add('error');
            status.textContent = `⚠️ ${message}`;
        }
    }

    /**
     * Get speech recognition instance
     */
    getRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            return null;
        }
        
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        return recognition;
    }

    /**
     * End voice session
     */
    async endSession() {
        try {
            await fetch('/api/voice/end-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    notes: `Session completed. Total turns: ${this.turnNumber}`
                })
            });
            
            this.speak('Voice session ended. Goodbye!');
        } catch (error) {
            console.error('Error ending session:', error);
        }
    }

    /**
     * Get session statistics
     */
    async getStatistics() {
        try {
            const response = await fetch('/api/voice/stats?days=7');
            const data = await response.json();
            return data.statistics;
        } catch (error) {
            console.error('Error fetching statistics:', error);
            return null;
        }
    }
}

// Initialize on page load
let voiceAssistant = null;

document.addEventListener('DOMContentLoaded', () => {
    voiceAssistant = new VoiceAssistantUI();
    
    // Only initialize if we're on the unified dashboard
    if (document.querySelector('.unified-dashboard')) {
        // Initialize with slight delay to ensure DOM is ready
        setTimeout(() => {
            voiceAssistant.initializeVoiceAssistant();
        }, 500);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (voiceAssistant) {
        voiceAssistant.endSession();
    }
});
