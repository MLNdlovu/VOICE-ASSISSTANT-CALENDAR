/**
 * Voice Assistant Module
 * Handles Web Speech API integration, trigger phrase detection, and TTS
 * 
 * Usage:
 *   VoiceAssistant.initialize();
 *   VoiceAssistant.startListening();
 *   VoiceAssistant.stopListening();
 */

const VoiceAssistant = (() => {
  // Configuration
  const config = {
    triggerPhrase: localStorage.getItem('voice_trigger') || 'activate',
    continuousListening: true,
    language: 'en-US',
    interimResults: true,
    maxAlternatives: 1
  };

  // State tracking
  let state = {
    isListening: false,
    isSpeaking: false,
    transcript: '',
    interimTranscript: '',
    confidence: 0,
    triggerDetected: false
  };

  // Web Speech API instance
  let recognition = null;
  let synthesis = window.speechSynthesis;

  /**
   * Initialize Voice Assistant
   */
  function initialize() {
    // Set up Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.error('Speech Recognition not supported in this browser');
      showNotification('Speech Recognition not supported', 'error');
      return false;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = config.continuousListening;
    recognition.interimResults = config.interimResults;
    recognition.language = config.language;
    recognition.maxAlternatives = config.maxAlternatives;

    // Set up event handlers
    recognition.onstart = handleRecognitionStart;
    recognition.onresult = handleRecognitionResult;
    recognition.onerror = handleRecognitionError;
    recognition.onend = handleRecognitionEnd;

    console.log('✓ Voice Assistant initialized');
    return true;
  }

  /**
   * Handle recognition start
   */
  function handleRecognitionStart() {
    state.isListening = true;
    state.interimTranscript = '';
    updateUI('listening');
    console.log('🎤 Listening started');
  }

  /**
   * Handle recognition result
   */
  function handleRecognitionResult(event) {
    state.interimTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      const isFinal = event.results[i].isFinal;
      const confidence = event.results[i][0].confidence;

      if (isFinal) {
        state.transcript += transcript + ' ';
        state.confidence = confidence;
        console.log(`✓ Final: "${transcript}" (${(confidence * 100).toFixed(1)}%)`);
        
        // Check for trigger phrase
        checkTrigger(state.transcript);
      } else {
        state.interimTranscript += transcript;
        console.log(`↳ Interim: "${transcript}"`);
      }
    }

    // Update display with current transcript
    updateTranscriptDisplay();
  }

  /**
   * Handle recognition error
   */
  function handleRecognitionError(event) {
    console.error('Speech Recognition error:', event.error);
    updateUI('error');
    
    let message = '';
    switch (event.error) {
      case 'no-speech':
        message = 'No speech detected. Please try again.';
        break;
      case 'audio-capture':
        message = 'Microphone not found. Check permissions.';
        break;
      case 'network':
        message = 'Network error. Check connection.';
        break;
      default:
        message = `Speech error: ${event.error}`;
    }
    
    showNotification(message, 'error');
  }

  /**
   * Handle recognition end
   */
  function handleRecognitionEnd() {
    state.isListening = false;
    console.log('🎤 Listening stopped');
    
    // Automatically restart if continuous listening enabled
    if (config.continuousListening && !state.triggerDetected) {
      setTimeout(() => {
        if (!state.isSpeaking) {
          startListening();
        }
      }, 500);
    }
  }

  /**
   * Check if trigger phrase was detected
   */
  function checkTrigger(transcript) {
    const trigger = config.triggerPhrase.toLowerCase();
    const text = transcript.toLowerCase();

    if (text.includes(trigger)) {
      state.triggerDetected = true;
      console.log(`🔔 Trigger detected: "${trigger}"`);
      
      // Extract command after trigger
      const commandIndex = text.indexOf(trigger) + trigger.length;
      const command = transcript.substring(commandIndex).trim();
      
      updateUI('triggered');
      
      if (command) {
        // Process the command immediately
        processVoiceCommand(command);
      } else {
        // Wait for next input
        speakText('Ready for your command.');
      }
    }
  }

  /**
   * Process voice command
   */
  async function processVoiceCommand(commandText) {
    try {
      updateUI('processing');
      console.log(`📝 Processing command: "${commandText}"`);

      // Stop listening while processing
      stopListening();

      // Use the Web Speech transcript
      let transcript = commandText;
      
      // Note: For full Whisper API integration with raw audio,
      // you would need to capture audio using MediaRecorder and send base64 audio
      // For now, we send the Web Speech transcript to the backend which can
      // optionally use Whisper API for enhancement
      
      // Send to backend for processing
      const response = await fetch('/api/voice/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: transcript,
          context: '',
          confidence: state.confidence
        })
      });

      const data = await response.json();

      if (data.ok) {
        console.log(`✓ Response: "${data.speak_text}"`);
        
        // Display response in UI
        addMessageToChat('assistant', data.speak_text);
        
        // Speak response
        speakText(data.speak_text);
        
        // Update state
        updateUI('responding');
        
        // Resume listening after response completes
        setTimeout(() => {
          state.triggerDetected = false;
          state.transcript = '';
          startListening();
        }, 3000);
      } else {
        console.error('Backend error:', data.error);
        speakText('Sorry, there was an error processing your command.');
      }
    } catch (error) {
      console.error('Command processing error:', error);
      speakText('An error occurred while processing your command.');
    }
  }

  /**
   * Start listening
   */
  function startListening() {
    if (!recognition) {
      initialize();
    }

    if (recognition && !state.isListening) {
      recognition.start();
      console.log('🎤 Starting to listen...');
    }
  }

  /**
   * Stop listening
   */
  function stopListening() {
    if (recognition && state.isListening) {
      recognition.stop();
      console.log('⏹️ Stopped listening');
    }
  }

  /**
   * Abort listening
   */
  function abortListening() {
    if (recognition) {
      recognition.abort();
      state.isListening = false;
      state.interimTranscript = '';
      console.log('🛑 Aborted listening');
    }
  }

  /**
   * Speak text using Text-to-Speech
   */
  function speakText(text) {
    if (!text) return;

    // Cancel any ongoing speech
    synthesis.cancel();

    state.isSpeaking = true;
    updateUI('speaking');

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = localStorage.getItem('tts_speed') || 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Handle speech end
    utterance.onend = () => {
      state.isSpeaking = false;
      console.log('🔊 Speech completed');
      updateUI('idle');
      
      // Resume listening if needed
      if (config.continuousListening) {
        startListening();
      }
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event.error);
      state.isSpeaking = false;
      updateUI('error');
    };

    synthesis.speak(utterance);
    console.log(`🔊 Speaking: "${text.substring(0, 50)}..."`);
  }

  /**
   * Stop speaking
   */
  function stopSpeaking() {
    synthesis.cancel();
    state.isSpeaking = false;
    console.log('⏹️ Stopped speaking');
    updateUI('idle');
  }

  /**
   * Set trigger phrase
   */
  function setTrigger(trigger) {
    config.triggerPhrase = trigger.toLowerCase().trim();
    localStorage.setItem('voice_trigger', config.triggerPhrase);
    console.log(`✓ Trigger phrase updated (hidden for privacy)`);
  }

  /**
   * Get trigger phrase
   */
  function getTrigger() {
    return config.triggerPhrase;
  }

  /**
   * Transcribe audio using Whisper API
   */
  async function transcribeWithWhisper(audioBase64) {
    try {
      const response = await fetch('/api/voice/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          audio: audioBase64,
          format: 'wav'
        })
      });

      const data = await response.json();
      if (data.ok) {
        console.log(`✓ Whisper transcribed: "${data.transcript}"`);
        return data.transcript;
      } else {
        console.error('Whisper error:', data.error);
        return null;
      }
    } catch (error) {
      console.error('Whisper API error:', error);
      return null;
    }
  }

  /**
   * Update UI state
   */
  function updateUI(newState) {
    const elements = {
      micBtn: document.getElementById('voice-mic-btn'),
      stopBtn: document.getElementById('voice-stop-btn'),
      indicator: document.getElementById('voice-indicator'),
      status: document.getElementById('voice-status')
    };

    // Update button states
    if (elements.micBtn) {
      elements.micBtn.disabled = newState !== 'idle' && newState !== 'listening';
      elements.micBtn.classList.toggle('active', newState === 'listening');
    }

    if (elements.stopBtn) {
      elements.stopBtn.disabled = newState !== 'listening' && newState !== 'speaking';
    }

    // Update indicator
    if (elements.indicator) {
      elements.indicator.className = `voice-indicator ${newState}`;
      
      const colors = {
        idle: '#4CAF50',
        listening: '#2196F3',
        triggered: '#FF9800',
        processing: '#9C27B0',
        speaking: '#F44336',
        responding: '#00BCD4',
        error: '#f44336'
      };
      
      elements.indicator.style.backgroundColor = colors[newState] || '#4CAF50';
    }

    // Update status text
    if (elements.status) {
      const statusTexts = {
        idle: 'Ready',
        listening: 'Listening...',
        triggered: 'Triggered',
        processing: 'Processing...',
        speaking: 'Speaking...',
        responding: 'Responding...',
        error: 'Error'
      };
      
      elements.status.textContent = statusTexts[newState] || 'Ready';
    }

    console.log(`[UI] State: ${newState}`);
  }

  /**
   * Update transcript display
   */
  function updateTranscriptDisplay() {
    const display = document.getElementById('voice-transcript');
    if (display) {
      const interim = state.interimTranscript ? `<em>${state.interimTranscript}</em>` : '';
      display.innerHTML = state.transcript + interim;
    }
  }

  /**
   * Add message to chat
   */
  function addMessageToChat(role, text) {
    const chatContainer = document.getElementById('voice-chat-container');
    if (!chatContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = text;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  /**
   * Show notification
   */
  function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  /**
   * Get current state
   */
  function getState() {
    return { ...state };
  }

  /**
   * Check browser support
   */
  function isSupported() {
    return !!(
      window.SpeechRecognition ||
      window.webkitSpeechRecognition
    ) && !!window.speechSynthesis;
  }

  // Public API
  return {
    initialize,
    startListening,
    stopListening,
    abortListening,
    speakText,
    stopSpeaking,
    setTrigger,
    getTrigger,
    getState,
    isSupported,
    processVoiceCommand,
    updateUI
  };
})();

/**
 * Initialize Voice Assistant when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
  if (VoiceAssistant.isSupported()) {
    console.log('✓ Voice Assistant supported');
    VoiceAssistant.initialize();
    
    // Set up UI event listeners
    setupVoiceUI();
  } else {
    console.warn('⚠️ Voice Assistant not supported in this browser');
    showNotification('Voice commands not supported', 'warning');
  }
});

/**
 * Set up voice UI controls
 */
function setupVoiceUI() {
  const micBtn = document.getElementById('voice-mic-btn');
  const stopBtn = document.getElementById('voice-stop-btn');
  const triggerInput = document.getElementById('voice-trigger-input');
  const saveTriggerBtn = document.getElementById('voice-save-trigger-btn');

  // Microphone button
  if (micBtn) {
    micBtn.addEventListener('click', () => {
      if (!VoiceAssistant.getState().isListening) {
        VoiceAssistant.startListening();
      }
    });
  }

  // Stop button
  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      VoiceAssistant.stopSpeaking();
      VoiceAssistant.stopListening();
      VoiceAssistant.updateUI('idle');
    });
  }

  // Trigger phrase setup
  if (triggerInput && saveTriggerBtn) {
    triggerInput.value = VoiceAssistant.getTrigger();
    
    saveTriggerBtn.addEventListener('click', () => {
      const newTrigger = triggerInput.value.trim();
      if (newTrigger.length > 0) {
        VoiceAssistant.setTrigger(newTrigger);
        showNotification(`Trigger phrase updated: "${newTrigger}"`, 'success');
      }
    });
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', (event) => {
    // Ctrl+M: Microphone toggle
    if (event.ctrlKey && event.key === 'm') {
      event.preventDefault();
      const state = VoiceAssistant.getState();
      if (state.isListening) {
        VoiceAssistant.stopListening();
      } else {
        VoiceAssistant.startListening();
      }
    }

    // Ctrl+Shift+S: Stop speaking
    if (event.ctrlKey && event.shiftKey && event.key === 'S') {
      event.preventDefault();
      VoiceAssistant.stopSpeaking();
    }
  });

  console.log('✓ Voice UI controls set up');
}

/**
 * Show notification helper
 */
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    background: ${type === 'error' ? '#f44336' : type === 'success' ? '#4CAF50' : '#2196F3'};
    color: white;
    border-radius: 4px;
    z-index: 10000;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 3000);
}
