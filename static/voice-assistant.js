/**
 * Voice Assistant UI Controller
 * Handles voice interaction, animations, state machine, and real-time feedback
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
        this.voiceState = 'waiting_for_trigger'; // waiting_for_trigger, active, inactive
        this.bookingContext = {}; // Store booking details
        // Silence detection / auto-execute
        this.silenceTimer = null;
        this.silenceTimeoutMs = 2000; // 2 seconds of silence triggers auto-submit
        this.lastCapturedText = '';
        this.lastProcessedText = '';
        this._suppressRecognition = false;
    }

    /**
     * Initialize voice assistant after login
     */
    async initializeVoiceAssistant() {
        try {
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
                this.voiceState = data.voice_state;
                
                // Show greeting UI
                this.displayMessage('assistant', data.greeting);
                
                // Trigger greeting speech
                await this.speak(data.speak_text);
                
                // Auto-start listening for trigger phrase
                setTimeout(() => {
                    this.startListening();
                }, 1500);
            }
        } catch (error) {
            console.error('Failed to initialize voice assistant:', error);
            this.showError('Voice assistant initialization failed');
        }
    }

    /**
     * Start listening for voice input
     */
    async startListening() {
        try {
            if (this.isListening) return;
            
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
            
            let transcript = '';

            // Keep a reference to recognition instance so we can restart if needed
            this._recognition = recognition;

            recognition.onstart = () => {
                console.log('🎤 Listening...');
                this.updateVoiceIndicator('listening');
            };
            
            recognition.onresult = async (event) => {
                // If recognition is suppressed (e.g., during TTS), ignore results
                if (this._suppressRecognition) return;

                // Build transcript from interim/final results
                transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }

                // Save last captured text (interim or final)
                this.lastCapturedText = transcript.trim();

                // Show interim/final to user (marking interim if needed)
                const isFinal = Array.from(event.results).slice(-1)[0].isFinal;
                if (this.voiceState === 'waiting_for_trigger') {
                    // Hide trigger phrase display for privacy - show no text, just listening indicator
                    // Don't update interim message to keep trigger phrase hidden
                } else {
                    this._updateInterimMessage(`"${this.lastCapturedText}${isFinal ? '' : ' (listening...)'}"`, isFinal);
                }

                // Reset silence timer each time we get new audio
                if (this.silenceTimer) {
                    clearTimeout(this.silenceTimer);
                    this.silenceTimer = null;
                }
                this.silenceTimer = setTimeout(() => this._onSilenceDetect(), this.silenceTimeoutMs);
            };
            
            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                if (event.error === 'no-speech') {
                    this.showError('No speech detected. Please try again.');
                } else {
                    this.showError(`Error: ${event.error}`);
                }
                this.isListening = false;
            };
            
            recognition.onend = () => {
                // Recognition ended unexpectedly (some browsers stop). Restart if assistant is still active.
                this.isListening = false;
                this.updateVoiceIndicator('idle');

                // If there is a pending captured phrase that wasn't processed, trigger it
                if (this.lastCapturedText && this.lastCapturedText !== this.lastProcessedText) {
                    // If silence timer wasn't fired (edge case), process immediately
                    if (this.silenceTimer) {
                        clearTimeout(this.silenceTimer);
                        this.silenceTimer = null;
                    }
                    this._onSilenceDetect();
                } else if (this.voiceState === 'active' || this.voiceState === 'waiting_for_trigger') {
                    // Try to restart listening after a short pause
                    setTimeout(() => this.startListening(), 300);
                }
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
     * Called when we detect user silence for configured timeout.
     * Auto-submits the last captured text if it wasn't already processed.
     */
    async _onSilenceDetect() {
        try {
            if (!this.lastCapturedText) return;
            if (this.lastCapturedText === this.lastProcessedText) return;

            // Remember processed text to avoid duplicates
            const toProcess = this.lastCapturedText;
            this.lastProcessedText = toProcess;

            // Clear timer
            if (this.silenceTimer) {
                clearTimeout(this.silenceTimer);
                this.silenceTimer = null;
            }

            // Process the command
            await this.processVoiceCommand(toProcess);

            // Continue listening if state requires it
            if (!this.isListening && (this.voiceState === 'active' || this.voiceState === 'waiting_for_trigger')) {
                setTimeout(() => this.startListening(), 300);
            }
        } catch (err) {
            console.error('Error in silence handler:', err);
        }
    }

    /**
     * Stop listening
     */
    stopListening() {
        this.isListening = false;
        this.updateVoiceIndicator('idle');
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
            
            // Update voice state from backend response
            if (data.state) {
                this.voiceState = data.state;
                // Convert state names for display
                if (data.state === 'trigger_detected') {
                    this.voiceState = 'active';
                } else if (data.state === 'trigger_not_detected') {
                    this.voiceState = 'waiting_for_trigger';
                }
            } else if (data.voice_state) {
                this.voiceState = data.voice_state;
            }
            
            if (data.success) {
                // Display assistant response
                if (data.message) {
                    this.displayMessage('assistant', data.message);
                }
                
                // Speak response using speak_text
                if (data.speak_text) {
                    // Stop recognition and suppress interim results while we speak
                    try {
                        this._suppressRecognition = true;
                        if (this._recognition) {
                            try { this._recognition.abort(); } catch (e) {}
                        }
                        // Clear any pending silence timers to avoid auto-submitting TTS
                        if (this.silenceTimer) { clearTimeout(this.silenceTimer); this.silenceTimer = null; }
                    } catch (e) {
                        console.warn('Failed to pause recognition before TTS', e);
                    }

                    await this.speak(data.speak_text);

                    // Re-enable recognition after speaking
                    this._suppressRecognition = false;
                    if (!this.isListening && (this.voiceState === 'active' || this.voiceState === 'waiting_for_trigger' || this.voiceState === 'booking_in_progress')) {
                        setTimeout(() => this.startListening(), 250);
                    }
                }
                
                // Handle state transitions
                if (data.state === 'trigger_detected') {
                    console.log('✅ Trigger phrase detected!');
                    this.updateVoiceIndicator('listening');
                } else if (data.state === 'trigger_not_detected') {
                    console.log('❌ Trigger phrase not detected. Waiting for retry...');
                    this.updateVoiceIndicator('listening');
                }
                
                // Handle specific command types
                if (data.command_type) {
                    this.handleCommandType(data.command_type, data.parameters, data);
                }
                
                // Store booking context if needed
                if (data.command_type === 'book_meeting' && data.parameters) {
                    this.bookingContext = data.parameters;
                }
            } else {
                // Handle error
                if (data.speak_text) {
                    this.displayMessage('assistant', data.speak_text);
                    
                    try {
                        this._suppressRecognition = true;
                        if (this._recognition) {
                            try { this._recognition.abort(); } catch (e) {}
                        }
                        if (this.silenceTimer) { clearTimeout(this.silenceTimer); this.silenceTimer = null; }
                    } catch (e) {}
                    
                    await this.speak(data.speak_text);
                    
                    this._suppressRecognition = false;
                    if (!this.isListening && (this.voiceState === 'active' || this.voiceState === 'waiting_for_trigger')) {
                        setTimeout(() => this.startListening(), 250);
                    }
                } else {
                    this.showError(data.error || 'Command processing failed');
                }
            }
        } catch (error) {
            console.error('Error processing command:', error);
            this.showError('Failed to process command');
        }
    }

    /**
     * Handle different command types
     */
    handleCommandType(commandType, parameters, fullResponse) {
        switch (commandType) {
            case 'book_meeting':
                console.log('📅 Booking meeting...');
                this.bookingContext = parameters || {};
                
                // If we have all info, auto-fill form
                if (parameters && parameters.title && parameters.date && parameters.time) {
                    const titleEl = document.getElementById('event-title');
                    const dateEl = document.getElementById('event-date');
                    const timeEl = document.getElementById('event-time');
                    
                    if (titleEl) titleEl.value = parameters.title;
                    if (dateEl) dateEl.value = parameters.date;
                    if (timeEl) timeEl.value = parameters.time;
                }
                break;
            
            case 'list_events':
                console.log('📅 Listing events...');
                if (fullResponse.events) {
                    this.displayCalendarEvents(fullResponse.events);
                }
                break;
            
            case 'set_reminder':
                console.log('⏰ Setting reminder...');
                if (parameters && parameters.title) {
                    const titleEl = document.getElementById('event-title');
                    if (titleEl) titleEl.value = parameters.title;
                }
                break;
            
            case 'unknown':
            default:
                console.log('❓ Unknown command type');
        }
    }

    /**
     * Display calendar events
     */
    displayCalendarEvents(events) {
        const transcript = document.getElementById('chat-history') || 
                          document.querySelector('.chat-history');
        
        if (!transcript) return;
        
        const eventsList = events.map(e => {
            const start = e.start?.dateTime || e.start?.date || 'Unknown time';
            return `• ${e.summary} at ${start}`;
        }).join('\n');
        
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message ai';
        messageEl.innerHTML = `<strong>Your Events:</strong><pre>${eventsList}</pre>`;
        messageEl.style.animation = 'slideInRight 0.2s ease-out';
        
        transcript.appendChild(messageEl);
        transcript.scrollTop = transcript.scrollHeight;
    }

    /**
     * Speak text using browser TTS
     */
    async speak(text) {
        return new Promise((resolve) => {
            try {
                this.isSpeaking = true;
                this.updateVoiceIndicator('speaking');
                
                if ('speechSynthesis' in window) {
                    // Cancel any ongoing speech
                    speechSynthesis.cancel();
                    
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.rate = 0.9;
                    utterance.pitch = 1.0;
                    utterance.volume = 0.9;
                    
                    utterance.onend = () => {
                        this.isSpeaking = false;
                        this.updateVoiceIndicator('idle');
                        resolve();
                    };
                    
                    utterance.onerror = (error) => {
                        console.error('Speech synthesis error:', error);
                        this.isSpeaking = false;
                        this.updateVoiceIndicator('idle');
                        resolve();
                    };
                    
                    speechSynthesis.speak(utterance);
                } else {
                    this.isSpeaking = false;
                    this.updateVoiceIndicator('idle');
                    resolve();
                }
            } catch (error) {
                console.error('Error speaking:', error);
                this.isSpeaking = false;
                this.updateVoiceIndicator('idle');
                resolve();
            }
        });
    }

    /**
     * Display message in transcript
     */
    displayMessage(speaker, text) {
        const transcript = document.getElementById('chat-history') || 
                          document.querySelector('.chat-history');
        
        if (transcript) {
            const messageEl = document.createElement('div');
            messageEl.className = `chat-message ${speaker === 'user' ? 'user' : speaker === 'error' ? 'error' : 'ai'}`;
            messageEl.textContent = text;
            messageEl.style.animation = 'slideInRight 0.2s ease-out';
            
            transcript.appendChild(messageEl);
            transcript.scrollTop = transcript.scrollHeight;
        }
        
        // Store in transcript
        this.transcript.push({ speaker, text, timestamp: new Date() });
    }

    /**
     * Update a single interim message instead of appending lots of small messages.
     * If isFinal is true, the interim will be converted to a regular user message.
     */
    _updateInterimMessage(text, isFinal) {
        const transcript = document.getElementById('chat-history') || document.querySelector('.chat-history');
        if (!transcript) return;

        let interim = document.querySelector('.chat-message.interim');
        if (!interim) {
            interim = document.createElement('div');
            interim.className = 'chat-message user interim';
            interim.style.opacity = '0.85';
            interim.style.fontStyle = 'italic';
            transcript.appendChild(interim);
        }

        interim.textContent = text;
        transcript.scrollTop = transcript.scrollHeight;

        if (isFinal) {
            interim.classList.remove('interim');
            interim.style.fontStyle = '';
            interim.style.opacity = '';
            // Add to transcript store
            this.transcript.push({ speaker: 'user', text, timestamp: new Date() });
            // remove the interim marker so new interim messages create a fresh element
        }
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

        // Hide/show chat panel during voice interactions
        this.toggleChatVisibility(state);
    }

    /**
     * Toggle chat panel visibility during voice interactions
     */
    toggleChatVisibility(state) {
        const chatPanel = document.getElementById('ai-chat-panel');
        if (chatPanel) {
            if (state === 'listening' || state === 'speaking') {
                chatPanel.classList.add('voice-active');
            } else {
                chatPanel.classList.remove('voice-active');
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
        // Use continuous + interim so we can detect silence and auto-submit
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        return recognition;
    }

    /**
     * End voice session
     */
    async endSession() {
        try {
            this.stopListening();
            
            // Save transcript to database
            await fetch('/api/voice/save-transcript', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    transcript: this.transcript,
                    notes: `Session completed. Total turns: ${this.turnNumber}`
                })
            });
            
            await fetch('/api/voice/end-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    notes: `Session completed. Total turns: ${this.turnNumber}`
                })
            });
            
            await this.speak('Voice session ended. Goodbye!');
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

    /**
     * Toggle voice mode
     */
    async toggleVoiceMode() {
        if (this.isListening) {
            this.stopListening();
        } else {
            await this.startListening();
        }
    }
}

// Initialize on page load
let voiceAssistant = null;

document.addEventListener('DOMContentLoaded', () => {
    voiceAssistant = new VoiceAssistantUI();
    
    // Only initialize if we're on the unified dashboard or AI chat page
    if (document.querySelector('.unified-dashboard') || document.querySelector('.ai-chat-container')) {
        // Initialize with slight delay to ensure DOM is ready
        setTimeout(() => {
            voiceAssistant.initializeVoiceAssistant();
        }, 500);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (voiceAssistant && voiceAssistant.voiceSessionId) {
        voiceAssistant.endSession();
    }
});

