/**
 * Voice Assistant with OpenAI GPT
 * Handles trigger phrase detection, voice commands, and single-bubble UI
 * 
 * Features:
 * - Hidden trigger phrase (not displayed in UI)
 * - Continuous listening for trigger detection
 * - Web Speech API for voice recognition
 * - OpenAI GPT for intelligent responses
 * - Single message bubble with auto-disappear
 * - Browser TTS (SpeechSynthesis)
 */

const synth = window.speechSynthesis;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

let recognition = null;
try {
  recognition = new SpeechRecognition();
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.lang = 'en-US';
} catch (e) {
  console.warn('SpeechRecognition not available', e);
}

/**
 * Speak text using browser SpeechSynthesis with female voice preference
 */
async function speak(text) {
  if (!text) return;
  
  // Cancel any existing speech
  synth.cancel();
  
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.2;  // Higher pitch for more feminine voice
  utterance.volume = 1.0;
  
  // Try to select a female voice
  try {
    const voices = synth.getVoices();
    // Look for female voice (prefer Google or Microsoft female voices)
    const femaleVoice = voices.find(v => 
      v.name.toLowerCase().includes('female') || 
      v.name.toLowerCase().includes('woman') ||
      (v.name.toLowerCase().includes('google') && v.name.toLowerCase().includes('us-en')) ||
      v.name.toLowerCase().includes('zira')
    ) || voices.find(v => v.name.toLowerCase().includes('english'));
    
    if (femaleVoice) {
      utterance.voice = femaleVoice;
    }
  } catch (e) {
    console.warn('Could not set voice:', e);
  }
  
  synth.speak(utterance);
  
  return new Promise(resolve => {
    utterance.onend = resolve;
    utterance.onerror = resolve;
  });
}

/**
 * Show single assistant message bubble with auto-disappear
 */
function showBubble(text, timeout = 3500) {
  let bubble = document.getElementById('assistantBubble');
  
  if (!bubble) {
    bubble = document.createElement('div');
    bubble.id = 'assistantBubble';
    bubble.style.cssText = `
      position: fixed;
      right: 20px;
      bottom: 20px;
      max-width: 280px;
      padding: 12px 18px;
      background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%);
      color: #fff;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.2);
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 9999;
      font-size: 14px;
      line-height: 1.4;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      word-wrap: break-word;
    `;
    document.body.appendChild(bubble);
  }
  
  bubble.textContent = text;
  bubble.style.display = 'block';
  
  // Speak the text
  speak(text);
  
  // Clear previous timeout
  if (bubble._timer) clearTimeout(bubble._timer);
  
  // Auto-hide after timeout
  bubble._timer = setTimeout(() => {
    bubble.style.display = 'none';
  }, timeout);
}

/**
 * Fetch trigger status from server (only returns if it's set, not the actual value)
 */
async function triggerStatus() {
  try {
    const res = await fetch('/api/get_trigger');
    if (!res.ok) return false;
    const j = await res.json();
    return j.trigger_set || false;
  } catch (e) {
    console.warn('Error checking trigger status:', e);
    return false;
  }
}

/**
 * Save trigger phrase to server and client storage
 * Trigger is saved on server but never returned; stored locally for matching
 */
async function setTrigger(triggerText) {
  const trigger = triggerText.trim().toLowerCase();
  if (!trigger) {
    showBubble('Please enter a trigger phrase.');
    return;
  }
  
  try {
    const res = await fetch('/api/set_trigger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger: trigger })
    });
    
    if (!res.ok) {
      showBubble('Failed to save trigger. Try again.');
      return;
    }
    
    // Store locally for matching
    sessionStorage.setItem('user_trigger', trigger);
    showBubble('✓ Trigger phrase saved. Say it to activate.');
    
  } catch (e) {
    console.error('Error setting trigger:', e);
    showBubble('Error saving trigger phrase.');
  }
}

/**
 * Start continuous listening loop for trigger phrase
 * Uses short listen sessions to avoid resource drain
 */
function startWakeLoop() {
  if (!recognition) {
    console.warn('Speech Recognition not available');
    return;
  }
  
  recognition.continuous = true;
  recognition.interimResults = false;
  
  recognition.onresult = async (event) => {
    if (!event.results || event.results.length === 0) return;
    
    const transcript = event.results[event.results.length - 1][0].transcript.trim().toLowerCase();
    const isFinal = event.results[event.results.length - 1].isFinal;
    
    if (!isFinal) return;
    
    // Check if trigger was detected
    const triggerSet = await triggerStatus();
    if (!triggerSet) return;
    
    const trigger = sessionStorage.getItem('user_trigger') || '';
    if (!trigger || !transcript.includes(trigger)) return;
    
    console.log('🔔 Trigger detected:', trigger);
    
    // Stop listening and activate assistant
    recognition.stop();
    await handleVoiceFlow();
    
    // Resume listening after brief pause
    setTimeout(() => {
      try {
        recognition.start();
      } catch (e) {
        console.warn('Error restarting recognition:', e);
      }
    }, 1000);
  };
  
  recognition.onerror = (event) => {
    console.warn('Recognition error:', event.error);
    // Auto-restart on error
    setTimeout(() => {
      try {
        recognition.start();
      } catch (e) {}
    }, 2000);
  };
  
  recognition.onend = () => {
    console.log('Recognition ended, restarting...');
    setTimeout(() => {
      try {
        recognition.start();
      } catch (e) {
        console.warn('Could not restart recognition:', e);
      }
    }, 500);
  };
  
  try {
    recognition.start();
    console.log('🎤 Voice assistant listening for trigger...');
  } catch (e) {
    console.warn('Could not start recognition:', e);
  }
}

/**
 * Main voice interaction flow
 * 1. Greet user
 * 2. Listen for command
 * 3. Send to server for processing
 * 4. Speak response and show bubble
 */
async function handleVoiceFlow() {
  console.log('💬 Voice flow activated');
  
  // Show greeting
  showBubble('What can I do for you today?', 6000);
  
  // Listen for command (8 second timeout)
  const command = await listenOnce(8000);
  
  if (!command) {
    showBubble("I didn't catch that. Please repeat.");
    return;
  }
  
  console.log('📝 Command heard:', command);
  
  // Show processing indicator
  showBubble('Processing...', 2000);
  
  // Send to server
  try {
    const response = await fetch('/api/voice_cmd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript: command })
    });
    
    const data = await response.json();
    
    if (!data || !data.ok) {
      showBubble(data?.reply || 'Sorry, I could not process that.');
      return;
    }
    
    // Show assistant response
    const assistantText = data.assistant_text || data.reply || 'Done.';
    showBubble(assistantText);
    
    console.log('✓ Response:', assistantText);
    
    // If more info needed, listen for follow-up
    if (data.needs_more_info) {
      await new Promise(resolve => setTimeout(resolve, 3500)); // Wait for bubble to show
      
      const followUp = await listenOnce(8000);
      if (followUp) {
        showBubble('Processing...', 2000);
        
        const res2 = await fetch('/api/voice_cmd', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ transcript: followUp })
        });
        
        const data2 = await res2.json();
        showBubble(data2.assistant_text || 'Okay.');
      }
    }
    
  } catch (error) {
    console.error('Error communicating with server:', error);
    showBubble('Connection error. Please try again.');
  }
}

/**
 * Listen for a single voice command with timeout
 */
function listenOnce(timeoutMs = 8000) {
  return new Promise((resolve) => {
    if (!recognition) {
      resolve(null);
      return;
    }
    
    let heard = null;
    const recognizer = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognizer.interimResults = false;
    recognizer.continuous = false;
    recognizer.lang = 'en-US';
    
    recognizer.onstart = () => {
      console.log('🎤 Listening for command...');
    };
    
    recognizer.onresult = (event) => {
      if (event.results && event.results.length > 0) {
        heard = event.results[event.results.length - 1][0].transcript;
        console.log('Heard:', heard);
        recognizer.stop();
      }
    };
    
    recognizer.onerror = (event) => {
      console.warn('Listen error:', event.error);
      resolve(null);
    };
    
    recognizer.onend = () => {
      console.log('Listening stopped');
      resolve(heard);
    };
    
    // Start listening
    try {
      recognizer.start();
    } catch (e) {
      console.warn('Could not start listening:', e);
      resolve(null);
      return;
    }
    
    // Timeout fallback
    setTimeout(() => {
      try {
        recognizer.stop();
      } catch (e) {}
    }, timeoutMs);
  });
}

/**
 * Stop current speech and listening
 */
function stopAssistant() {
  synth.cancel();
  if (recognition) {
    try {
      recognition.stop();
    } catch (e) {}
  }
  const bubble = document.getElementById('assistantBubble');
  if (bubble) bubble.style.display = 'none';
}

/**
 * Initialize on page load
 */
window.addEventListener('load', async () => {
  console.log('🚀 Initializing Voice Assistant...');
  
  // Create bubble container
  if (!document.getElementById('assistantBubble')) {
    const bubble = document.createElement('div');
    bubble.id = 'assistantBubble';
    bubble.style.display = 'none';
    document.body.appendChild(bubble);
  }
  
  // Create stop button
  if (!document.getElementById('voiceStopBtn')) {
    const stopBtn = document.createElement('button');
    stopBtn.id = 'voiceStopBtn';
    stopBtn.innerHTML = '⏹️ Stop';
    stopBtn.style.cssText = `
      position: fixed;
      right: 20px;
      top: 20px;
      padding: 8px 16px;
      background: #EF4444;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      z-index: 9998;
      font-size: 12px;
      font-weight: 500;
      display: none;
    `;
    stopBtn.onclick = stopAssistant;
    document.body.appendChild(stopBtn);
  }
  
  // Check if user has trigger set locally
  const localTrigger = sessionStorage.getItem('user_trigger');
  if (localTrigger) {
    console.log('✓ Trigger found locally. Starting wake loop...');
    startWakeLoop();
  } else {
    console.log('ℹ️ No trigger set. Use settings to configure.');
  }
});

// Export functions for use in HTML
window.VoiceAssistant = {
  setTrigger,
  startListening: startWakeLoop,
  stopListening: stopAssistant,
  speak
};
