/**
 * Voice Interface Controller
 * Handles voice input, trigger detection, command processing, and TTS
 */

class VoiceInterface {
    constructor() {
        // State machine
        this.state = 'IDLE'; // IDLE, TRIGGER_DETECTED, CAPTURING, PROCESSING, RESPONDING, NEEDS_INFO
        
        // Voice recognition setup
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
        // Session data
        this.sessionId = this.generateSessionId();
        this.triggerPhrase = null;
        this.lastTranscript = '';
        this.isProcessing = false;
        this.silenceTimer = null;
        this.lastResultTime = 0;
        this.silenceTimeoutMs = 2000;
        
        // TTS settings
        this.enableTTS = true;
        this.speechRate = 0.9;
        this.speechPitch = 1.0;
        this.isSpeaking = false;
        
        // UI elements
        this.micButton = document.getElementById('micButton');
        this.micStatus = document.getElementById('micStatus');
        this.assistantBubble = document.getElementById('assistantBubble');
        this.bubbleContent = document.getElementById('bubbleContent');
        this.processingIndicator = document.getElementById('processingIndicator');
        this.eventsDisplay = document.getElementById('eventsDisplay');
        this.eventsList = document.getElementById('eventsList');
        
        // Modal elements
        this.settingsModal = document.getElementById('settingsModal');
        this.triggerSetupModal = document.getElementById('triggerSetupModal');
        this.changeTriggerModal = document.getElementById('changeTriggerModal');
        
        // Settings
        this.alwaysOnToggle = document.getElementById('alwaysOnToggle');
        this.enableTTSCheckbox = document.getElementById('enableTTS');
        this.speechRateInput = document.getElementById('speechRate');
        this.speechPitchInput = document.getElementById('speechPitch');
        
        // Audio elements
        this.activationSound = document.getElementById('activationSound');
        this.readySound = document.getElementById('readySound');
        this.errorSound = document.getElementById('errorSound');
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadTriggerStatus();
        this.setupSpeechRecognition();
        this.loadSettings();
    }

    /**
     * Setup event listeners for all UI elements
     */
    setupEventListeners() {
        // Mic button
        this.micButton.addEventListener('click', () => this.toggleMicrophone());

        // Settings modal
        document.getElementById('settingsBtn').addEventListener('click', () => this.openSettingsModal());
        document.getElementById('closeSettingsBtn').addEventListener('click', () => this.closeModal('settingsModal'));
        
        // Trigger management
        document.getElementById('changeTriggerBtn').addEventListener('click', () => this.openChangeTriggerModal());
        document.getElementById('saveTriggerBtn').addEventListener('click', () => this.saveTrigger());
        document.getElementById('skipTriggerBtn').addEventListener('click', () => this.closeModal('triggerSetupModal'));
        document.getElementById('confirmNewTriggerBtn').addEventListener('click', () => this.confirmNewTrigger());
        document.getElementById('cancelNewTriggerBtn').addEventListener('click', () => this.closeModal('changeTriggerModal'));
        document.getElementById('closeTriggerModalBtn').addEventListener('click', () => this.closeModal('changeTriggerModal'));

        // Settings controls
        this.alwaysOnToggle.addEventListener('change', (e) => this.setAlwaysOn(e.target.checked));
        this.enableTTSCheckbox.addEventListener('change', (e) => this.setTTS(e.target.checked));
        this.speechRateInput.addEventListener('input', (e) => this.setSpeechRate(parseFloat(e.target.value)));
        this.speechPitchInput.addEventListener('input', (e) => this.setSpeechPitch(parseFloat(e.target.value)));

        // Close modals on background click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.closeModal(modal.id);
            });
        });
    }

    /**
     * Setup speech recognition callbacks
     */
    setupSpeechRecognition() {
        this.recognition.onstart = () => {
            console.log('Speech recognition started');
        };

        this.recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const isFinal = event.results[i].isFinal;
                transcript += event.results[i][0].transcript;

                if (isFinal) {
                    this.lastResultTime = Date.now();
                    this.onTranscriptReceived(transcript, true);
                } else {
                    this.onTranscriptReceived(transcript, false);
                }
            }

            // Reset silence timer
            this.resetSilenceTimer();
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.onSpeechError(event.error);
        };

        this.recognition.onend = () => {
            console.log('Speech recognition ended');
        };
    }

    /**
     * Handle transcript received from speech recognition
     */
    onTranscriptReceived(transcript, isFinal) {
        this.lastTranscript = transcript.toLowerCase().trim();

        if (!isFinal) {
            // Interim result - update UI
            this.updateMicStatus(`Hearing: "${transcript}"`);
        } else {
            // Final result - process
            if (this.state === 'IDLE') {
                // Check if it's the trigger phrase
                if (this.fuzzyMatchTrigger(this.lastTranscript)) {
                    this.triggerDetected();
                }
            } else if (this.state === 'CAPTURING') {
                // Process the command
                this.processCommand(this.lastTranscript);
            } else if (this.state === 'NEEDS_INFO') {
                // Continue with follow-up answer
                this.processCommand(this.lastTranscript);
            }
        }
    }

    /**
     * Fuzzy match the trigger phrase (70-80% similarity)
     */
    fuzzyMatchTrigger(transcript) {
        if (!this.triggerPhrase) return false;

        const similarity = this.calculateSimilarity(transcript, this.triggerPhrase);
        console.log(`Trigger match: ${similarity.toFixed(2)} (threshold: 0.75)`);
        return similarity >= 0.75;
    }

    /**
     * Calculate Levenshtein similarity between two strings
     */
    calculateSimilarity(str1, str2) {
        const track = Array(str2.length + 1).fill(null).map(() => Array(str1.length + 1).fill(null));
        for (let i = 0; i <= str1.length; i += 1) track[0][i] = i;
        for (let j = 0; j <= str2.length; j += 1) track[j][0] = j;

        for (let j = 1; j <= str2.length; j += 1) {
            for (let i = 1; i <= str1.length; i += 1) {
                const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1;
                track[j][i] = Math.min(
                    track[j][i - 1] + 1,
                    track[j - 1][i] + 1,
                    track[j - 1][i - 1] + indicator
                );
            }
        }

        const distance = track[str2.length][str1.length];
        const maxLength = Math.max(str1.length, str2.length);
        return 1 - (distance / maxLength);
    }

    /**
     * Trigger detected
     */
    triggerDetected() {
        console.log('Trigger detected!');
        this.setState('TRIGGER_DETECTED');
        
        // Play activation sound
        this.playSound('activation');
        
        // Visual feedback
        this.micButton.classList.add('listening');
        this.updateMicStatus('Listening…');
        
        // Transition to capture state
        setTimeout(() => {
            this.setState('CAPTURING');
            this.updateMicStatus('Say your command…');
        }, 500);
    }

    /**
     * Process voice command via backend
     */
    async processCommand(transcript) {
        if (this.isProcessing || !transcript) return;
        
        this.isProcessing = true;
        this.setState('PROCESSING');
        this.showProcessing(true);
        this.micButton.disabled = true;

        try {
            const response = await fetch('/api/voice_cmd', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    transcript: transcript,
                    user_id: document.querySelector('[data-user-id]')?.dataset.userId || 'unknown'
                })
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();

            if (data.ok) {
                this.setState('RESPONDING');
                await this.handleResponse(data);
            } else {
                this.showError(data.assistant_text || 'Failed to process command');
            }
        } catch (error) {
            console.error('Command processing error:', error);
            this.showError('I could not process that. Please try again.');
        } finally {
            this.isProcessing = false;
            this.showProcessing(false);
        }
    }

    /**
     * Handle response from backend
     */
    async handleResponse(data) {
        const { assistant_text, spoken_time, needs_more_info, data: responseData } = data;

        // Show assistant response
        this.showAssistantResponse(assistant_text);

        // Speak response
        if (this.enableTTS && assistant_text) {
            await this.speak(assistant_text, spoken_time);
        }

        // Handle events display
        if (responseData?.events && responseData.events.length > 0) {
            this.displayEvents(responseData.events);
        }

        // Handle follow-up questions
        if (needs_more_info) {
            this.setState('NEEDS_INFO');
            this.updateMicStatus('Please answer…');
        } else {
            // Reset after response
            setTimeout(() => {
                this.resetToIdle();
            }, 2000);
        }
    }

    /**
     * Show assistant response in bubble
     */
    showAssistantResponse(text) {
        this.micButton.classList.remove('listening');
        this.assistantBubble.style.display = 'flex';
        this.bubbleContent.textContent = text;
    }

    /**
     * Clear assistant bubble
     */
    clearAssistantResponse() {
        this.assistantBubble.classList.add('hidden');
        setTimeout(() => {
            this.assistantBubble.style.display = 'none';
            this.assistantBubble.classList.remove('hidden');
            this.bubbleContent.textContent = '';
        }, 400);
    }

    /**
     * Display events
     */
    displayEvents(events) {
        this.eventsList.innerHTML = '';
        events.forEach(event => {
            const card = document.createElement('div');
            card.className = 'event-card';
            card.innerHTML = `
                <div class="event-title">${this.escapeHtml(event.title)}</div>
                <div class="event-time">${this.escapeHtml(event.spoken_time || event.iso_time)}</div>
                <div class="event-date">${this.escapeHtml(event.date || 'Today')}</div>
            `;
            this.eventsList.appendChild(card);
        });

        this.eventsDisplay.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.eventsDisplay.style.display = 'none';
        }, 5000);
    }

    /**
     * Text-to-speech
     */
    async speak(text, spokenTime = null) {
        if (!window.speechSynthesis) return;

        return new Promise((resolve) => {
            // Cancel any existing speech
            speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = this.speechRate;
            utterance.pitch = this.speechPitch;
            utterance.voice = this.selectVoice();

            this.isSpeaking = true;

            utterance.onend = () => {
                this.isSpeaking = false;
                resolve();
            };

            utterance.onerror = (error) => {
                console.error('TTS error:', error);
                this.isSpeaking = false;
                resolve();
            };

            speechSynthesis.speak(utterance);
        });
    }

    /**
     * Select a female voice
     */
    selectVoice() {
        const voices = speechSynthesis.getVoices();
        const femaleVoices = voices.filter(v => v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('woman'));
        return femaleVoices.length > 0 ? femaleVoices[0] : voices[0];
    }

    /**
     * Show error message
     */
    showError(message) {
        this.playSound('error');
        this.showAssistantResponse(`Error: ${message}`);
        if (this.enableTTS) {
            this.speak(message);
        }
        setTimeout(() => this.resetToIdle(), 3000);
    }

    /**
     * Handle speech recognition error
     */
    onSpeechError(error) {
        console.error('Speech error:', error);
        if (error === 'no-speech' && this.state !== 'IDLE') {
            this.showError("I didn't catch that. Please try again.");
        } else if (error !== 'no-speech') {
            this.showError(`Speech error: ${error}`);
        }
    }

    /**
     * Reset to IDLE state
     */
    resetToIdle() {
        this.clearAssistantResponse();
        this.setState('IDLE');
        this.updateMicStatus('Say your trigger…');
        this.micButton.disabled = false;
        this.eventsDisplay.style.display = 'none';

        // Restart listening if always-on is enabled
        if (this.alwaysOnToggle.checked) {
            this.startListening();
        }
    }

    /**
     * Toggle microphone on/off
     */
    toggleMicrophone() {
        if (this.state === 'IDLE') {
            this.startListening();
        } else {
            this.stopListening();
            this.resetToIdle();
        }
    }

    /**
     * Start listening
     */
    startListening() {
        try {
            this.recognition.start();
            this.setState('IDLE');
            this.updateMicStatus('Say your trigger…');
        } catch (e) {
            console.error('Could not start listening:', e);
        }
    }

    /**
     * Stop listening
     */
    stopListening() {
        try {
            this.recognition.stop();
        } catch (e) {
            console.error('Could not stop listening:', e);
        }
    }

    /**
     * Reset silence timer
     */
    resetSilenceTimer() {
        if (this.silenceTimer) clearTimeout(this.silenceTimer);

        if (this.state === 'CAPTURING') {
            this.silenceTimer = setTimeout(() => {
                if (this.lastTranscript && !this.isProcessing) {
                    this.processCommand(this.lastTranscript);
                }
            }, this.silenceTimeoutMs);
        }
    }

    /**
     * State machine
     */
    setState(newState) {
        console.log(`State: ${this.state} → ${newState}`);
        this.state = newState;

        // Update UI based on state
        if (newState === 'IDLE') {
            this.micButton.classList.remove('listening', 'processing');
        } else if (newState === 'CAPTURING') {
            this.micButton.classList.add('listening');
            this.micButton.classList.remove('processing');
        } else if (newState === 'PROCESSING') {
            this.micButton.classList.add('processing');
            this.micButton.classList.remove('listening');
        }
    }

    /**
     * Update mic status text
     */
    updateMicStatus(text) {
        this.micStatus.textContent = text;
        if (text.includes('Listening') || text.includes('Hearing')) {
            this.micStatus.classList.add('active');
        } else {
            this.micStatus.classList.remove('active');
        }
    }

    /**
     * Show/hide processing indicator
     */
    showProcessing(show) {
        this.processingIndicator.style.display = show ? 'flex' : 'none';
    }

    /**
     * Play audio sound
     */
    playSound(soundType) {
        const element = {
            'activation': this.activationSound,
            'ready': this.readySound,
            'error': this.errorSound
        }[soundType];

        if (element) {
            element.currentTime = 0;
            element.play().catch(e => console.warn('Could not play sound:', e));
        }
    }

    /**
     * Load trigger status from backend
     */
    async loadTriggerStatus() {
        try {
            const response = await fetch('/api/get_trigger_status');
            if (!response.ok) throw new Error('Failed to load trigger status');

            const data = await response.json();

            if (data.trigger_set) {
                // Load trigger from session storage
                this.triggerPhrase = sessionStorage.getItem('triggerPhrase');
                if (!this.triggerPhrase) {
                    // Trigger not in session, show setup
                    this.showTriggerSetup();
                } else {
                    // Greet user
                    this.greetUser();
                }
            } else {
                // No trigger set, show setup
                this.showTriggerSetup();
            }
        } catch (error) {
            console.error('Error loading trigger status:', error);
            this.showTriggerSetup();
        }
    }

    /**
     * Show trigger setup modal
     */
    showTriggerSetup() {
        this.openModal('triggerSetupModal');
    }

    /**
     * Greet user on login
     */
    async greetUser() {
        const greeting = "Welcome back, I'm ready. Say your trigger to begin.";
        if (this.enableTTS) {
            await this.speak(greeting);
        }
        this.startListening();
    }

    /**
     * Save trigger phrase
     */
    async saveTrigger() {
        const trigger = document.getElementById('triggerInput').value.trim();

        if (!trigger) {
            alert('Please enter a trigger phrase');
            return;
        }

        try {
            const response = await fetch('/api/set_trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ trigger })
            });

            if (!response.ok) throw new Error('Failed to save trigger');

            // Save to session storage (not localStorage for privacy)
            sessionStorage.setItem('triggerPhrase', trigger.toLowerCase());
            this.triggerPhrase = trigger.toLowerCase();

            this.closeModal('triggerSetupModal');
            this.greetUser();
        } catch (error) {
            console.error('Error saving trigger:', error);
            alert('Failed to save trigger. Please try again.');
        }
    }

    /**
     * Open change trigger modal
     */
    openChangeTriggerModal() {
        this.closeModal('settingsModal');
        this.openModal('changeTriggerModal');
    }

    /**
     * Confirm new trigger
     */
    async confirmNewTrigger() {
        const newTrigger = document.getElementById('newTriggerInput').value.trim();

        if (!newTrigger) {
            alert('Please enter a new trigger phrase');
            return;
        }

        try {
            const response = await fetch('/api/set_trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ trigger: newTrigger })
            });

            if (!response.ok) throw new Error('Failed to update trigger');

            sessionStorage.setItem('triggerPhrase', newTrigger.toLowerCase());
            this.triggerPhrase = newTrigger.toLowerCase();

            this.closeModal('changeTriggerModal');
            this.openSettingsModal();
            
            const feedback = "Trigger phrase updated successfully.";
            if (this.enableTTS) await this.speak(feedback);
        } catch (error) {
            console.error('Error updating trigger:', error);
            alert('Failed to update trigger. Please try again.');
        }
    }

    /**
     * Settings management
     */
    loadSettings() {
        this.enableTTS = localStorage.getItem('enableTTS') !== 'false';
        this.speechRate = parseFloat(localStorage.getItem('speechRate') || '0.9');
        this.speechPitch = parseFloat(localStorage.getItem('speechPitch') || '1.0');

        this.enableTTSCheckbox.checked = this.enableTTS;
        this.speechRateInput.value = this.speechRate;
        this.speechPitchInput.value = this.speechPitch;
        document.getElementById('rateDisplay').textContent = this.speechRate;
        document.getElementById('pitchDisplay').textContent = this.speechPitch;
    }

    setSpeechRate(rate) {
        this.speechRate = rate;
        localStorage.setItem('speechRate', rate);
        document.getElementById('rateDisplay').textContent = rate;
    }

    setSpeechPitch(pitch) {
        this.speechPitch = pitch;
        localStorage.setItem('speechPitch', pitch);
        document.getElementById('pitchDisplay').textContent = pitch;
    }

    setTTS(enabled) {
        this.enableTTS = enabled;
        localStorage.setItem('enableTTS', enabled);
    }

    setAlwaysOn(enabled) {
        if (enabled) {
            this.startListening();
        } else {
            this.stopListening();
        }
    }

    /**
     * Modal management
     */
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    openSettingsModal() {
        this.openModal('settingsModal');
    }

    /**
     * Utility functions
     */
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Wait for speech synthesis voices to load
    speechSynthesis.onvoiceschanged = () => {
        console.log('Voices loaded');
    };

    window.voiceInterface = new VoiceInterface();
});
