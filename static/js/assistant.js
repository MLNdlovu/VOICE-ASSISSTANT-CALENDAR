/**
 * Voice Assistant JavaScript
 * Handles speech recognition, assistant responses, and calendar integration
 */

// Configuration
const CONFIG = {
    triggerPhrase: 'hey assistant',
    apiBaseUrl: '/api',
    speechLang: 'en-US',
};

// State
let state = {
    isListening: false,
    recognition: null,
    transcript: '',
};

// DOM Elements
const assistantBubble = document.getElementById('assistantBubble');
const startListeningBtn = document.getElementById('startListening');
const voiceVisualizer = document.querySelector('.voice-visualizer');
const transcriptDisplay = document.getElementById('transcriptDisplay');
const manualBookingForm = document.getElementById('manualBookingForm');
const eventList = document.getElementById('eventList');

/**
 * Initialize Speech Recognition
 */
function initializeSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        showAssistantMessage('Speech recognition is not supported in your browser.');
        return;
    }

    state.recognition = new SpeechRecognition();
    state.recognition.continuous = false;
    state.recognition.interimResults = true;
    state.recognition.lang = CONFIG.speechLang;

    state.recognition.onstart = () => {
        state.isListening = true;
        startListeningBtn.classList.add('listening');
        startListeningBtn.textContent = '🛑 Listening...';
        voiceVisualizer.classList.add('listening');
        transcriptDisplay.classList.remove('show');
    };

    state.recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i].transcript;
            if (event.results[i].isFinal) {
                state.transcript = transcript.toLowerCase().trim();
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Show interim results
        if (interimTranscript) {
            transcriptDisplay.textContent = interimTranscript;
            transcriptDisplay.classList.add('show');
        }
    };

    state.recognition.onend = () => {
        state.isListening = false;
        startListeningBtn.classList.remove('listening');
        startListeningBtn.textContent = '🎤 Talk to Assistant';
        voiceVisualizer.classList.remove('listening');

        // Process transcript if final
        if (state.transcript) {
            processSpeechInput(state.transcript);
            state.transcript = '';
        }
    };

    state.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech') {
            showAssistantMessage('Error: ' + event.error);
        }
        state.isListening = false;
        startListeningBtn.classList.remove('listening');
        voiceVisualizer.classList.remove('listening');
    };
}

/**
 * Process speech input
 */
async function processSpeechInput(transcript) {
    console.log('Processing transcript:', transcript);
    
    // Check if trigger phrase is present
    if (!transcript.includes(CONFIG.triggerPhrase)) {
        console.log('Trigger phrase not detected. Ignoring.');
        return;
    }

    // Remove trigger phrase and get command
    const command = transcript.replace(CONFIG.triggerPhrase, '').trim();
    if (!command) return;

    // Show transcript
    transcriptDisplay.textContent = `You: ${transcript}`;
    transcriptDisplay.classList.add('show');

    try {
        // Send to GPT for parsing
        const response = await fetch(`${CONFIG.apiBaseUrl}/parse_event`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: command }),
        });

        if (!response.ok) throw new Error('Failed to parse command');
        const data = await response.json();

        if (data.success && data.event) {
            // Book the event
            await bookEvent(data.event);
            showAssistantMessage(`Booked: ${data.event.title} on ${data.event.date} at ${data.event.time}`);
            loadEvents();
        } else {
            showAssistantMessage(data.message || 'Could not understand the request.');
        }
    } catch (error) {
        console.error('Error processing command:', error);
        showAssistantMessage('Error processing your command.');
    }
}

/**
 * Show assistant message in bubble
 */
function showAssistantMessage(message) {
    assistantBubble.textContent = message;
    assistantBubble.classList.add('show');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        assistantBubble.classList.remove('show');
    }, 5000);
}

/**
 * Start/stop listening
 */
function toggleListening() {
    if (!state.recognition) {
        initializeSpeechRecognition();
    }

    if (state.isListening) {
        state.recognition.stop();
    } else {
        state.recognition.start();
    }
}

/**
 * Book event via API
 */
async function bookEvent(event) {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/book_event`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(event),
        });

        if (!response.ok) throw new Error('Failed to book event');
        return await response.json();
    } catch (error) {
        console.error('Error booking event:', error);
        throw error;
    }
}

/**
 * Load and display events
 */
async function loadEvents() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/get_events`);
        if (!response.ok) throw new Error('Failed to load events');
        
        const data = await response.json();
        const events = data.events || [];

        eventList.innerHTML = '';

        if (events.length === 0) {
            eventList.innerHTML = '<div class="empty-state">No events scheduled</div>';
            return;
        }

        events.forEach(event => {
            const eventElement = createEventElement(event);
            eventList.appendChild(eventElement);
        });
    } catch (error) {
        console.error('Error loading events:', error);
        eventList.innerHTML = '<div class="empty-state">Error loading events</div>';
    }
}

/**
 * Create event DOM element
 */
function createEventElement(event) {
    const div = document.createElement('div');
    div.className = 'event-item';
    
    const eventDate = new Date(event.start || event.date);
    const dateStr = eventDate.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric' 
    });
    const timeStr = event.time || eventDate.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });

    div.innerHTML = `
        <div class="event-info">
            <div class="event-title">${event.title || 'Untitled'}</div>
            <div class="event-datetime">📅 ${dateStr} at ${timeStr}</div>
        </div>
        <button class="event-delete-btn" data-event-id="${event.id || event.event_id}">Delete</button>
    `;

    const deleteBtn = div.querySelector('.event-delete-btn');
    deleteBtn.addEventListener('click', () => deleteEvent(event.id || event.event_id));

    return div;
}

/**
 * Delete event
 */
async function deleteEvent(eventId) {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/delete_event`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event_id: eventId }),
        });

        if (!response.ok) throw new Error('Failed to delete event');
        loadEvents();
        showAssistantMessage('Event deleted.');
    } catch (error) {
        console.error('Error deleting event:', error);
        showAssistantMessage('Error deleting event.');
    }
}

/**
 * Handle manual booking form submission
 */
async function handleManualBooking(e) {
    e.preventDefault();

    const event = {
        title: document.getElementById('eventTitle').value,
        date: document.getElementById('eventDate').value,
        time: document.getElementById('eventTime').value,
    };

    try {
        await bookEvent(event);
        showAssistantMessage(`Event "${event.title}" booked!`);
        manualBookingForm.reset();
        loadEvents();
    } catch (error) {
        showAssistantMessage('Error booking event.');
    }
}

/**
 * Event Listeners
 */
startListeningBtn.addEventListener('click', toggleListening);
manualBookingForm.addEventListener('submit', handleManualBooking);

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    initializeSpeechRecognition();
    loadEvents();
});
