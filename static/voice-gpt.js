/**
 * Voice Assistant with GPT-5 Integration
 * Modern Web Speech API + OpenAI GPT for intelligent voice-activated assistant
 * 
 * Features:
 * - User-defined trigger phrase (private, not displayed)
 * - Continuous listening with trigger detection
 * - GPT-powered responses with context awareness
 * - Browser TTS (SpeechSynthesis) for natural speech output
 * - Smart event booking with field validation
 * - One-bubble UI with auto-disappear
 * - Error handling with silent trigger failures
 */

const VoiceGPT = (() => {
  // ============ CONFIGURATION ============
  
  const config = {
    triggerPhrase: '', // Will be loaded from server
    language: 'en-US',
    continuousListening: true,
    confidenceThreshold: 0.6,
    bubbleDisplayTime: 3500, // ms, disappears after this if no follow-up
    maxRetries: 3
  };

  // ============ STATE MANAGEMENT ============
  
  let state = {
    isListening: false,
    isSpeaking: false,
    isProcessing: false,
    transcript: '',
    confidence: 0,
    triggerDetected: false,
    conversationHistory: [], // [{role: 'user'/'assistant', content: '...'}]
    currentBubbleTimer: null,
    assistantState: 'idle' // idle, listening, speaking, processing
  };

  // Web Speech API
  let recognition = null;
  let synthesis = window.speechSynthesis;

  // ============ INITIALIZATION ============

  async function initialize() {
    console.log('🚀 Initializing Voice GPT Assistant...');
    
    // Load user's trigger phrase from server
    try {
      const response = await fetch('/api/get_trigger', { method: 'GET' });
      const data = await response.json();
      if (data.ok && data.trigger_phrase) {
        config.triggerPhrase = data.trigger_phrase.toLowerCase().trim();
        console.log('✓ Trigger phrase loaded (hidden for security)');
      } else {
        console.warn('No trigger phrase set. Use Settings to configure.');
        return false;
      }
    } catch (error) {
      console.error('Failed to load trigger phrase:', error);
      return false;
    }

    // Initialize Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.error('Speech Recognition API not supported in this browser');
      showNotification('Voice not supported in your browser', 'error');
      return false;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = config.continuousListening;
    recognition.interimResults = true;
    recognition.language = config.language;

    // Event handlers
    recognition.onstart = handleRecognitionStart;
    recognition.onresult = handleRecognitionResult;
    recognition.onerror = handleRecognitionError;
    recognition.onend = handleRecognitionEnd;

    console.log('✓ Voice GPT initialized successfully');
    return true;
  }

  // ============ WEB SPEECH API HANDLERS ============

  function handleRecognitionStart() {
    state.isListening = true;
    state.transcript = '';
    state.assistantState = 'listening';
    updateAssistantState('listening');
    console.log('🎤 Listening...');
  }

  function handleRecognitionResult(event) {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      const isFinal = event.results[i].isFinal;
      const confidence = event.results[i][0].confidence;

      if (isFinal) {
        state.transcript += transcript + ' ';
        state.confidence = confidence;
        console.log(`✓ Heard: "${transcript}" (${(confidence * 100).toFixed(0)}%)`);
        
        // Check for trigger phrase
        checkTriggerPhrase(state.transcript);
      }
    }
  }

  function handleRecognitionError(event) {
    console.warn('Speech error:', event.error);
    // Silent ignore: don't show error to user for common cases
    if (event.error === 'no-speech' || event.error === 'network') {
      // These are normal, just restart listening
      setTimeout(() => startListening(), 1000);
    } else if (event.error === 'audio-capture') {
      showNotification('Microphone not found. Check permissions.', 'error');
    }
  }

  function handleRecognitionEnd() {
    state.isListening = false;
    console.log('🎤 Listening stopped');
    
    // Auto-restart continuous listening
    if (!state.isSpeaking && !state.isProcessing) {
      setTimeout(() => startListening(), 500);
    }
  }

  // ============ TRIGGER DETECTION ============

  function checkTriggerPhrase(transcript) {
    const text = transcript.toLowerCase();
    const trigger = config.triggerPhrase.toLowerCase();

    // Simple substring match (can add fuzzy matching later)
    if (text.includes(trigger)) {
      state.triggerDetected = true;
      console.log('🔔 Trigger detected!');
      updateAssistantState('triggered');

      // Extract command after trigger
      const commandIndex = text.indexOf(trigger) + trigger.length;
      const command = transcript.substring(commandIndex).trim();

      // Stop listening and clear transcript
      stopListening();
      state.transcript = '';

      if (command) {
        // User said trigger + command
        handleVoiceCommand(command);
      } else {
        // Just trigger, ask what to do
        respondToUser('What can I do for you today?');
        state.assistantState = 'waiting';
      }
    }
  }

  // ============ COMMAND PROCESSING ============

  async function handleVoiceCommand(commandText) {
    console.log(`📝 Processing command: "${commandText}"`);
    state.isProcessing = true;
    state.assistantState = 'processing';
    updateAssistantState('processing');

    try {
      // Add to conversation history
      state.conversationHistory.push({
        role: 'user',
        content: commandText
      });

      // Check if booking intent
      const isBookingIntent = detectBookingIntent(commandText);

      let assistantResponse = '';

      if (isBookingIntent) {
        // Parse event details
        const eventData = await parseEventFromCommand(commandText);
        
        if (!eventData || !eventData.title || !eventData.date) {
          assistantResponse = 'I need a few details. What\'s the meeting title and what date would you like?';
        } else if (!eventData.start_time) {
          assistantResponse = `Got it. "${eventData.title}" on ${eventData.date}. What time?`;
        } else {
          // Try to book
          const bookResult = await bookEvent(eventData);
          if (bookResult.success) {
            assistantResponse = `✓ Meeting booked! "${eventData.title}" on ${eventData.date} at ${eventData.start_time}.`;
            state.conversationHistory.push({
              role: 'assistant',
              content: assistantResponse
            });
          } else {
            assistantResponse = 'Sorry, I couldn\'t book that meeting. Try again?';
          }
        }
      } else {
        // Send to GPT for response
        assistantResponse = await getGPTResponse(commandText);
      }

      // Add response to history
      state.conversationHistory.push({
        role: 'assistant',
        content: assistantResponse
      });

      // Display and speak response
      respondToUser(assistantResponse);

    } catch (error) {
      console.error('Error processing command:', error);
      respondToUser('Sorry, something went wrong. Please try again.');
    } finally {
      state.isProcessing = false;
    }
  }

  // ============ GPT INTEGRATION ============

  async function getGPTResponse(userMessage) {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          history: state.conversationHistory.slice(-10) // Last 10 messages for context
        })
      });

      if (!response.ok) {
        console.error('Chat API error:', response.status);
        return 'I couldn\'t process that. Try again?';
      }

      const data = await response.json();
      return data.response || 'Hmm, I didn\'t get a response. Try again?';

    } catch (error) {
      console.error('Error calling chat API:', error);
      return 'Sorry, I couldn\'t connect to the server.';
    }
  }

  // ============ EVENT PARSING & BOOKING ============

  function detectBookingIntent(text) {
    const bookingKeywords = [
      'book', 'schedule', 'meeting', 'appointment', 'event', 
      'call', 'conference', 'lunch', 'dinner', 'set up'
    ];
    const lowerText = text.toLowerCase();
    return bookingKeywords.some(keyword => lowerText.includes(keyword));
  }

  async function parseEventFromCommand(commandText) {
    try {
      const response = await fetch('/api/parse_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: commandText })
      });

      if (!response.ok) return null;

      const data = await response.json();
      return data.event || null;

    } catch (error) {
      console.error('Error parsing event:', error);
      return null;
    }
  }

  async function bookEvent(eventData) {
    try {
      const response = await fetch('/api/scheduler', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventData)
      });

      if (!response.ok) return { success: false };

      const data = await response.json();
      return { success: data.ok === true };

    } catch (error) {
      console.error('Error booking event:', error);
      return { success: false };
    }
  }

  // ============ TEXT-TO-SPEECH ============

  function speak(text) {
    // Cancel any existing speech
    window.speechSynthesis.cancel();

    state.isSpeaking = true;
    state.assistantState = 'speaking';
    updateAssistantState('speaking');

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Format times properly (1200 -> 12:00 PM, not "one two zero zero")
    utterance.text = formatTimesInText(text);

    utterance.onend = () => {
      state.isSpeaking = false;
      state.assistantState = 'idle';
      updateAssistantState('idle');
      
      // Resume listening after response
      setTimeout(() => {
        if (!state.isProcessing) {
          startListening();
        }
      }, 500);
    };

    utterance.onerror = (event) => {
      console.error('TTS error:', event.error);
      state.isSpeaking = false;
    };

    window.speechSynthesis.speak(utterance);
  }

  function formatTimesInText(text) {
    // Convert "1200" -> "12:00 PM", "1530" -> "3:30 PM", etc.
    return text.replace(/(\d{1,2}):?(\d{2})\s*(am|pm|AM|PM)?/g, (match, hours, minutes, period) => {
      let h = parseInt(hours);
      let m = parseInt(minutes);
      let ap = period ? period.toUpperCase() : (h >= 12 ? 'PM' : 'AM');
      
      if (!period) {
        if (h > 12) ap = 'PM';
        if (h > 12) h -= 12;
        if (h === 0) h = 12;
      }
      
      return `${h}:${String(m).padStart(2, '0')} ${ap}`;
    });
  }

  function stopSpeech() {
    window.speechSynthesis.cancel();
    state.isSpeaking = false;
    state.assistantState = 'idle';
    updateAssistantState('idle');
  }

  // ============ UI & DISPLAY ============

  function respondToUser(message) {
    // Hide previous bubble
    const previousBubble = document.querySelector('.assistant-bubble');
    if (previousBubble) previousBubble.remove();

    // Create new bubble
    const bubble = document.createElement('div');
    bubble.className = 'assistant-bubble';
    bubble.textContent = message;
    bubble.style.cssText = `
      position: fixed;
      bottom: 100px;
      right: 30px;
      max-width: 300px;
      padding: 16px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      z-index: 9999;
      font-size: 14px;
      line-height: 1.5;
      animation: slideUp 0.3s ease-out;
    `;

    document.body.appendChild(bubble);

    // Clear previous timer
    if (state.currentBubbleTimer) clearTimeout(state.currentBubbleTimer);

    // Auto-remove after timeout (unless waiting for input)
    if (state.assistantState !== 'waiting') {
      state.currentBubbleTimer = setTimeout(() => {
        bubble.style.animation = 'slideDown 0.3s ease-out';
        setTimeout(() => bubble.remove(), 300);
      }, config.bubbleDisplayTime);
    }

    // Speak the message
    speak(message);
  }

  function updateAssistantState(newState) {
    state.assistantState = newState;
    
    // Update visual indicator in UI
    const stateIndicator = document.getElementById('voice-state-indicator');
    if (stateIndicator) {
      let icon = '⭕';
      switch (newState) {
        case 'listening':
          icon = '🎤';
          break;
        case 'speaking':
          icon = '🔊';
          break;
        case 'processing':
          icon = '⏳';
          break;
        case 'triggered':
          icon = '✨';
          break;
      }
      stateIndicator.textContent = icon;
      stateIndicator.title = `Assistant: ${newState}`;
    }
  }

  function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}]`, message);
    // Could integrate with a toast library here
  }

  // ============ LISTENING CONTROLS ============

  function startListening() {
    if (!recognition) {
      console.warn('Speech Recognition not initialized');
      return;
    }

    if (!state.isListening && !state.isSpeaking && !state.isProcessing) {
      try {
        recognition.start();
      } catch (error) {
        console.warn('Listening already started or recognition error:', error);
      }
    }
  }

  function stopListening() {
    if (recognition && state.isListening) {
      try {
        recognition.stop();
      } catch (error) {
        console.warn('Error stopping recognition:', error);
      }
    }
  }

  function toggleListening() {
    if (state.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }

  // ============ PUBLIC API ============

  return {
    initialize: initialize,
    startListening: startListening,
    stopListening: stopListening,
    toggleListening: toggleListening,
    speak: speak,
    stopSpeech: stopSpeech,
    getState: () => ({ ...state }),
    setTrigger: async (newTrigger) => {
      try {
        const response = await fetch('/api/set_trigger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ trigger_phrase: newTrigger })
        });
        if (response.ok) {
          config.triggerPhrase = newTrigger.toLowerCase().trim();
          console.log('✓ Trigger phrase updated');
          return true;
        }
        return false;
      } catch (error) {
        console.error('Error setting trigger:', error);
        return false;
      }
    },
    sendMessage: async (message) => {
      state.conversationHistory.push({ role: 'user', content: message });
      const response = await getGPTResponse(message);
      state.conversationHistory.push({ role: 'assistant', content: response });
      respondToUser(response);
      return response;
    }
  };
})();

// ============ CSS ANIMATIONS ============

const style = document.createElement('style');
style.textContent = `
  @keyframes slideUp {
    from {
      transform: translateY(20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes slideDown {
    from {
      transform: translateY(0);
      opacity: 1;
    }
    to {
      transform: translateY(20px);
      opacity: 0;
    }
  }

  .assistant-bubble {
    word-wrap: break-word;
  }

  #voice-state-indicator {
    font-size: 24px;
    cursor: help;
    display: inline-block;
    margin-right: 8px;
  }
`;
document.head.appendChild(style);
