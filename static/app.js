// Voice Assistant Calendar - Web Dashboard JavaScript

const API_BASE = '/api';

// Toast Notification System
function createToastContainer() {
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
}

function showToast(message, type = 'info', duration = 4000) {
    createToastContainer();
    const container = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;
    
    container.appendChild(toast);
    
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.add('hide');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    return toast;
}

// Command History System
let commandHistory = JSON.parse(localStorage.getItem('voiceCommandHistory')) || [];
const MAX_HISTORY = 10;

function addToCommandHistory(command, status = 'success') {
    const entry = {
        command: command,
        status: status,
        timestamp: new Date().toLocaleTimeString(),
        date: new Date().toLocaleDateString()
    };
    commandHistory.unshift(entry);
    if (commandHistory.length > MAX_HISTORY) {
        commandHistory.pop();
    }
    localStorage.setItem('voiceCommandHistory', JSON.stringify(commandHistory));
}

function displayCommandHistory() {
    const historyContainer = document.getElementById('command-history');
    if (!historyContainer) return;
    
    if (commandHistory.length === 0) {
        historyContainer.innerHTML = '<p style="color: #b3e5fc; text-align: center; padding: 20px;">No command history yet</p>';
        return;
    }
    
    historyContainer.innerHTML = `
        <div style="max-height: 300px; overflow-y: auto;">
            ${commandHistory.map((entry, index) => `
                <div style="background: rgba(66, 165, 245, 0.1); border-left: 3px solid ${entry.status === 'success' ? '#4caf50' : '#f44336'}; padding: 12px; margin-bottom: 8px; border-radius: 4px; cursor: pointer;" onclick="document.getElementById('voice-text-input').value = '${entry.command.replace(/'/g, "\\'")}'; executeVoiceCommand();">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 13px; color: #b3e5fc;">${entry.date} ${entry.timestamp}</span>
                        <span style="font-size: 12px; color: ${entry.status === 'success' ? '#4caf50' : '#f44336'};">${entry.status.toUpperCase()}</span>
                    </div>
                    <p style="margin: 8px 0 0 0; color: #e3f2fd;">${escapeHtml(entry.command)}</p>
                </div>
            `).join('')}
        </div>
    `;
}

// Web Speech API Recognition (if available)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;
let waitingForTrigger = false;
let triggerPhrase = 'hey voice assistant';  // User must say this first

// Text-to-Speech Synthesis (if available)
const SpeechSynthesis = window.speechSynthesis;
let isSpeaking = false;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    // Increase timeout for longer voice input (booking commands with more details)
    recognition.maxAlternatives = 1;
    
    recognition.onstart = function() {
        isListening = true;
        document.getElementById('voice-record-btn').style.display = 'none';
        document.getElementById('voice-stop-btn').style.display = 'block';
        if (waitingForTrigger) {
            document.getElementById('voice-response').innerHTML = '<p style="color: #42a5f5;">🎤 Listening for trigger phrase... Say "' + triggerPhrase + '" to start</p>';
        } else {
            document.getElementById('voice-response').innerHTML = '<p style="color: #42a5f5;">🎤 Listening for your command (up to 15 seconds)...</p>';
        }
    };
    
    recognition.onresult = function(event) {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                transcript += event.results[i][0].transcript;
            }
        }
        transcript = transcript.toLowerCase().trim();
        
        // If waiting for trigger phrase, check if user said it (match full phrase or keyword)
        if (waitingForTrigger) {
            const normalized = transcript.toLowerCase();
            const triggerDetected = normalized.includes(triggerPhrase) || normalized.includes('assistant') || normalized.includes('voice assistant');
            if (triggerDetected) {
                document.getElementById('voice-response').innerHTML = '<p style="color: #4caf50;">✅ Trigger detected! Now listening for your command...</p>';
                waitingForTrigger = false;
                // Restart listening for the actual command
                setTimeout(() => recognition.start(), 500);
                return;
            } else {
                document.getElementById('voice-response').innerHTML = '<p style="color: #ff9800;">⚠️ Trigger phrase not detected. Try again. Say "' + triggerPhrase + '"</p>';
                document.getElementById('voice-text-input').value = '';
                // Restart listening
                setTimeout(() => recognition.start(), 1000);
                return;
            }
        }
        
        document.getElementById('voice-text-input').value = transcript;
    };
    
    recognition.onerror = function(event) {
        document.getElementById('voice-response').innerHTML = `<p style="color: #f44336;">❌ Error: ${event.error}</p>`;
    };
    
    recognition.onend = function() {
        isListening = false;
        document.getElementById('voice-record-btn').style.display = 'block';
        document.getElementById('voice-stop-btn').style.display = 'none';
    };
}

// Function to speak text using Web Speech API Text-to-Speech
function speakText(text) {
    if (!SpeechSynthesis) {
        console.warn('Text-to-Speech not supported in this browser');
        return;
    }
    
    // Cancel any ongoing speech
    SpeechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 0.9;  // Slightly slower speech for clarity
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    utterance.onstart = function() {
        isSpeaking = true;
        console.log('[VOICE OUTPUT] Speaking: ' + text);
    };
    
    utterance.onend = function() {
        isSpeaking = false;
        console.log('[VOICE OUTPUT] Speech finished');
    };
    
    utterance.onerror = function(event) {
        console.warn('[VOICE OUTPUT] Error:', event.error);
        isSpeaking = false;
    };
    
    SpeechSynthesis.speak(utterance);
}

function startVoiceInput() {
    if (recognition) {
        // Set flag to wait for trigger phrase first
        waitingForTrigger = true;
        document.getElementById('voice-response').innerHTML = '<p style="color: #2196f3;">📢 Say "' + triggerPhrase + '" to start listening to your command</p>';
        document.getElementById('voice-text-input').value = '';
        recognition.start();
    } else {
        document.getElementById('voice-response').innerHTML = '<p style="color: #f44336;">❌ Web Speech API not supported in this browser. Please type a command instead.</p>';
    }
}

function stopVoiceInput() {
    if (recognition && isListening) {
        recognition.stop();
    }
}

async function executeVoiceCommand() {
    let voiceText = document.getElementById('voice-text-input').value.trim();
    
    // If still waiting for trigger, remind user
    if (waitingForTrigger) {
        showToast('⚠️ Please say the trigger phrase first: "' + triggerPhrase + '"', 'warning');
        speakText('Please say the trigger phrase ' + triggerPhrase + ' first');
        return;
    }
    
    if (!voiceText) {
        showToast('⚠️ Please enter or speak a command.', 'warning');
        speakText('Please enter or speak a command');
        return;
    }
    
    document.getElementById('voice-response').innerHTML = '<p style="color: #42a5f5;">⏳ Processing command...</p>';
    
    try {
        const response = await fetch(`${API_BASE}/voice`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: voiceText })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            document.getElementById('voice-response').innerHTML = `
                <div style="background: rgba(76, 175, 80, 0.2); border-left: 4px solid #4caf50; padding: 16px; border-radius: 6px;">
                    <h4 style="color: #4caf50; margin: 0 0 10px 0;">✅ Command Executed</h4>
                    <p style="margin: 0;"><strong>Command:</strong> ${result.command}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Message:</strong> ${result.message}</p>
                </div>
            `;
            
            addToCommandHistory(voiceText, 'success');
            displayCommandHistory();
            showToast(`✅ ${result.message}`, 'success');
            
            // Speak the feedback for accessibility
            if (result.speak_text) {
                speakText(result.speak_text);
            }
            
            // Auto-refresh events if applicable
            if (result.command === 'book' || result.command === 'cancel-book' || result.command === 'events') {
                setTimeout(() => loadEvents(), 1000);
            }
        } else {
            const errorMsg = result.error || result.message || 'Unknown error';
            document.getElementById('voice-response').innerHTML = `
                <div style="background: rgba(244, 67, 54, 0.2); border-left: 4px solid #f44336; padding: 16px; border-radius: 6px;">
                    <h4 style="color: #f44336; margin: 0 0 10px 0;">❌ Command Failed</h4>
                    <p style="margin: 0;"><strong>Error:</strong> ${errorMsg}</p>
                    ${result.params ? `<p style="margin: 10px 0 0 0;"><small>Parsed: ${JSON.stringify(result.params)}</small></p>` : ''}
                </div>
            `;
            
            addToCommandHistory(voiceText, 'error');
            displayCommandHistory();
            showToast(`❌ ${errorMsg}`, 'error');
            
            // Speak the error for accessibility
            if (result.speak_text) {
                speakText(result.speak_text);
            } else {
                speakText('Command failed. ' + errorMsg);
            }
        }
    } catch (error) {
        document.getElementById('voice-response').innerHTML = `<div style="background: rgba(244, 67, 54, 0.2); border-left: 4px solid #f44336; padding: 16px; border-radius: 6px;"><p style="color: #f44336; margin: 0;">❌ Error: ${error.message}</p></div>`;
        addToCommandHistory(voiceText, 'error');
        displayCommandHistory();
        showToast(`❌ Error: ${error.message}`, 'error');
        speakText('An error occurred. ' + error.message);
    }
    
    // Clear input
    document.getElementById('voice-text-input').value = '';
}

// Tab switching with keyboard support
document.querySelectorAll('.nav-btn').forEach((btn, index) => {
    btn.addEventListener('click', function() {
        const tab = this.getAttribute('data-tab');
        switchTab(tab);
    });
    
    // Keyboard navigation: Arrow keys to switch tabs
    btn.addEventListener('keydown', function(e) {
        const buttons = Array.from(document.querySelectorAll('.nav-btn'));
        const currentIndex = buttons.indexOf(this);
        
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIndex = (currentIndex + 1) % buttons.length;
            buttons[nextIndex].focus();
            buttons[nextIndex].click();
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIndex = (currentIndex - 1 + buttons.length) % buttons.length;
            buttons[prevIndex].focus();
            buttons[prevIndex].click();
        }
    });
});

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Add active class to clicked button
    const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.setAttribute('aria-selected', 'true');
        activeBtn.focus();
    }

    // Load data if switching to events
    if (tabName === 'events') {
        loadEvents();
    }

    // Load settings if switching to settings
    if (tabName === 'settings') {
        loadSettings();
    }
}

// Load events
async function loadEvents() {
    const eventsList = document.getElementById('events-list');
    eventsList.innerHTML = '<p class="loading">Loading events...</p>';

    try {
        const response = await fetch(`${API_BASE}/events`);
        if (!response.ok) throw new Error('Failed to load events');

        const events = await response.json();

        if (events.length === 0) {
            eventsList.innerHTML = '<p class="no-events">No upcoming events</p>';
            return;
        }

        eventsList.innerHTML = events.map(event => `
            <div class="event-card">
                <div class="event-header">
                    <div class="event-title">${escapeHtml(event.summary)}</div>
                </div>
                <div class="event-time">📅 ${formatDateTime(event.start)} - ${formatTime(event.end)}</div>
                ${event.description ? `<div class="event-description">${escapeHtml(event.description)}</div>` : ''}
                <div class="event-actions">
                    <button class="btn-cancel-event" onclick="cancelEvent('${event.id}')">🗑️ Cancel</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading events:', error);
        eventsList.innerHTML = `<p class="no-events">Error loading events: ${error.message}</p>`;
    }
}

// Cancel event
async function cancelEvent(eventId) {
    if (!confirm('Are you sure you want to cancel this event?')) {
        return;
    }


    // --- AI Assistant client functions ---
    function openAiModal() {
        document.getElementById('ai-modal').style.display = 'flex';
    }

    function closeAiModal() {
        document.getElementById('ai-modal').style.display = 'none';
        document.getElementById('ai-input').value = '';
        document.getElementById('ai-response').innerText = '';
    }

    async function callAiChat() {
        const input = document.getElementById('ai-input').value.trim();
        if (!input) {
            showToast('Please enter a question for the AI', 'warning');
            return;
        }

        document.getElementById('ai-response').innerText = 'Thinking...';

        try {
            const res = await fetch(`${API_BASE}/ai/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: input })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                document.getElementById('ai-response').innerText = data.response;
            } else {
                document.getElementById('ai-response').innerText = data.error || 'AI error';
            }
        } catch (err) {
            document.getElementById('ai-response').innerText = err.message;
        }
    }

    async function callAiAgenda() {
        const input = document.getElementById('ai-input').value.trim();
        if (!input) {
            showToast('Please provide a meeting title or description', 'warning');
            return;
        }
        document.getElementById('ai-response').innerText = 'Generating agenda...';

        try {
            const res = await fetch(`${API_BASE}/ai/agenda`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: input })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                document.getElementById('ai-response').innerText = data.agenda;
            } else {
                document.getElementById('ai-response').innerText = data.error || 'AI error';
            }
        } catch (err) {
            document.getElementById('ai-response').innerText = err.message;
        }
    }
    try {
        const response = await fetch(`${API_BASE}/cancel/${eventId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to cancel event');

        showToast('✅ Event cancelled successfully', 'success');
        loadEvents();
    } catch (error) {
        console.error('Error cancelling event:', error);
        showToast(`❌ ${error.message}`, 'error');
    }
}

// Book event form
document.getElementById('booking-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = {
        summary: document.getElementById('event-summary').value,
        date: document.getElementById('event-date').value,
        time: document.getElementById('event-time').value,
        duration: parseInt(document.getElementById('event-duration').value),
        description: document.getElementById('event-description').value
    };

    try {
        const response = await fetch(`${API_BASE}/book`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to book event');
        }

        const result = await response.json();
        showToast('✅ Event booked successfully!', 'success');
        
        // Speak confirmation for accessibility if provided
        try {
            if (result.speak_text) speakText(result.speak_text);
            else speakText('Event booked successfully');
        } catch (e) {
            console.warn('TTS failed:', e);
        }

        // Reset form
        this.reset();
        
        // Set date to today if not already
        document.getElementById('event-date').valueAsDate = new Date();

    } catch (error) {
        console.error('Error booking event:', error);
        showToast(`❌ ${error.message}`, 'error');
    }
});

// Load settings
async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/settings`);
        if (!response.ok) throw new Error('Failed to load settings');

        const settings = await response.json();

        document.getElementById('timezone').value = settings.timezone || 'Africa/Johannesburg';
        document.getElementById('default-duration').value = settings.default_event_duration || 30;

    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Save settings form
document.getElementById('settings-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = {
        timezone: document.getElementById('timezone').value,
        default_event_duration: parseInt(document.getElementById('default-duration').value),
        last_calendar_id: 'primary'
    };

    try {
        const response = await fetch(`${API_BASE}/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) throw new Error('Failed to save settings');

        showToast('✅ Settings saved successfully!', 'success');

    } catch (error) {
        console.error('Error saving settings:', error);
        showToast(`❌ ${error.message}`, 'error');
    }
});

// Helper functions
function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    if (element.classList) {
        // It's a form message element
        const msgElement = element;
        msgElement.textContent = message;
        msgElement.className = `message ${type}`;
        msgElement.style.display = 'block';
    }
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Set today's date as default
    const today = new Date();
    document.getElementById('event-date').valueAsDate = today;

    // Load initial events
    loadEvents();

    // Display command history on page load
    displayCommandHistory();

    // Add keyboard support for voice input (Enter key to execute)
    document.getElementById('voice-text-input')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            executeVoiceCommand();
        }
    });
});
