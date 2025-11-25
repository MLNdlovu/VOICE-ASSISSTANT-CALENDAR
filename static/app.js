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
                    <button class="btn btn-ghost" onclick="openAiModalForEvent('${event.id}','${escapeHtml(event.summary).replace(/'/g, "\\'")}')">🤖 Agenda</button>
                    <button class="btn btn-ghost" onclick="callAiActionsForEvent('${event.id}','${escapeHtml(event.summary).replace(/'/g, "\\'")}')">📌 Actions</button>
                    <button class="btn btn-ghost" onclick="callAiFollowupsForEvent('${event.id}','${escapeHtml(event.summary).replace(/'/g, "\\'")}')">🔁 Follow-ups</button>
                    <button class="btn btn-ghost" onclick="openSummarizeModal('${event.id}')">📝 Summarize</button>
                    <button class="btn btn-ghost" onclick="callAiEmailForEvent('${event.id}','${escapeHtml(event.summary).replace(/'/g, "\\'")}')">✉️ Draft Email</button>
                    <button class="btn btn-ghost" onclick="callAiSuggestTimesForEvent('${event.id}','${escapeHtml(event.summary).replace(/'/g, "\\'")}')">⏰ Suggest Times</button>
                    <button class="btn btn-ghost" onclick="exportEvent('${event.id}')">⬇️ Export</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading events:', error);
        eventsList.innerHTML = `<p class="no-events">Error loading events: ${error.message}</p>`;
    }
}

// New AI helpers for per-event actions
async function callAiActionsForEvent(eventId, title) {
    openAiModal();
    const input = document.getElementById('ai-input');
    input.value = '';
    document.getElementById('ai-modal').dataset.eventId = eventId;
    document.getElementById('ai-response').innerText = 'Extracting action items...';

    // Optionally fetch event description to provide context
    try {
        const resEvent = await fetch(`${API_BASE}/events`);
        const events = await resEvent.json();
        const ev = events.find(e => e.id === eventId) || {};
        const notes = ev.description || '';

        const res = await fetch(`${API_BASE}/ai/actions`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ title: title, notes: notes })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById('ai-response').innerText = data.actions;
        } else {
            document.getElementById('ai-response').innerText = data.error || 'AI error';
        }
    } catch (err) {
        document.getElementById('ai-response').innerText = err.message;
    }
}

async function callAiEmailForEvent(eventId, title) {
    openAiModal();
    document.getElementById('ai-input').value = title || '';
    document.getElementById('ai-response').innerText = 'Drafting email...';
    try {
        const resEvent = await fetch(`${API_BASE}/events`);
        const events = await resEvent.json();
        const ev = events.find(e => e.id === eventId) || {};
        const context = ev.description || '';
        // Try to prefill recipients from organizer or attendees
        let recipients = [];
        if (ev.organizer && ev.organizer.email) recipients.push(ev.organizer.email);
        if (ev.attendees && Array.isArray(ev.attendees)) {
            ev.attendees.forEach(a => { if (a.email) recipients.push(a.email); });
        }
        // Deduplicate
        recipients = Array.from(new Set(recipients));

        const res = await fetch(`${API_BASE}/ai/email`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ title: title, recipients: recipients, context: context })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById('ai-response').innerText = data.email;
            // Add copy and mailto buttons
            addAiModalEmailActions(title, data.email);
        } else {
            document.getElementById('ai-response').innerText = data.error || 'AI error';
        }
    } catch (err) {
        document.getElementById('ai-response').innerText = err.message;
    }
}

function addAiModalEmailActions(subject, body) {
    // remove previous actions
    const existing = document.getElementById('ai-email-actions');
    if (existing) existing.remove();
    const container = document.createElement('div');
    container.id = 'ai-email-actions';
    container.style.marginTop = '12px';
    container.innerHTML = `
        <button class="btn btn-ghost" onclick="navigator.clipboard.writeText(${JSON.stringify(body)})">Copy Email</button>
        <button class="btn btn-primary" onclick="window.location.href='mailto:?subject='+encodeURIComponent(${JSON.stringify(subject)})+'&body='+encodeURIComponent(${JSON.stringify(body)})">Open Mail Client</button>
    `;
    document.querySelector('.modal-content').appendChild(container);
}

async function callAiSuggestTimesForEvent(eventId, title) {
    openAiModal();
    document.getElementById('ai-input').value = title || '';
    document.getElementById('ai-response').innerText = 'Suggesting times...';
    try {
        const res = await fetch(`${API_BASE}/ai/suggest-times`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ duration: 30, participants: [] })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById('ai-response').innerText = data.suggestions;
        } else {
            document.getElementById('ai-response').innerText = data.error || 'AI error';
        }
    } catch (err) {
        document.getElementById('ai-response').innerText = err.message;
    }
}

async function callAiFollowupsForEvent(eventId, title) {
    openAiModal();
    document.getElementById('ai-input').value = title || '';
    document.getElementById('ai-response').innerText = 'Generating follow-ups and suggested emails...';
    try {
        const resEvent = await fetch(`${API_BASE}/events`);
        const events = await resEvent.json();
        const ev = events.find(e => e.id === eventId) || {};
        const notes = ev.description || '';

        const res = await fetch(`${API_BASE}/ai/followups`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ title: title, notes: notes })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById('ai-response').innerText = data.followups;
        } else {
            document.getElementById('ai-response').innerText = data.error || 'AI error';
        }
    } catch (err) {
        document.getElementById('ai-response').innerText = err.message;
    }
}

async function callAiTranslate() {
    const text = document.getElementById('ai-response').innerText || document.getElementById('ai-input').value || '';
    if (!text) {
        showToast('Nothing to translate', 'warning');
        return;
    }
    const target = document.getElementById('ai-translate-lang')?.value || 'en';
    document.getElementById('ai-response').innerText = 'Translating...';
    try {
        const res = await fetch(`${API_BASE}/ai/translate`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ text: text, target_language: target })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById('ai-response').innerText = data.translation;
        } else {
            document.getElementById('ai-response').innerText = data.error || 'AI error';
        }
    } catch (err) {
        document.getElementById('ai-response').innerText = err.message;
    }
}

// --- Top-level AI Assistant client functions ---
function openAiModal() {
    document.getElementById('ai-modal').style.display = 'flex';
}

function closeAiModal() {
    document.getElementById('ai-modal').style.display = 'none';
    document.getElementById('ai-input').value = '';
    document.getElementById('ai-response').innerText = '';
    // clear attached event id
    document.getElementById('ai-modal').dataset.eventId = '';
}

function openAiModalForEvent(eventId, title) {
    openAiModal();
    const input = document.getElementById('ai-input');
    input.value = title || '';
    document.getElementById('ai-modal').dataset.eventId = eventId;
}

function openSummarizeModal(eventId) {
    // Reuse the AI modal but switch UI to summarization: prefill input with placeholder
    openAiModal();
    const input = document.getElementById('ai-input');
    input.value = '';
    document.getElementById('ai-modal').dataset.eventId = eventId;
    document.getElementById('ai-response').innerText = 'Paste meeting notes above and click Ask to summarize.';
}

async function callAiChat() {
    const input = document.getElementById('ai-input').value.trim();
    if (!input) {
        showToast('Please enter a question for the AI', 'warning');
        return;
    }

    document.getElementById('ai-response').innerText = 'Thinking...';

    try {
        // If user prefixes message with "project:", forward to project-aware endpoint
        const isProject = /^project:\s*/i.test(input);
        const payload = { message: isProject ? input.replace(/^project:\s*/i, '') : input };
        const endpoint = isProject ? `${API_BASE}/ai/project-chat` : `${API_BASE}/ai/chat`;

        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById('ai-response').innerText = data.response;
            // Speak AI response for accessibility
            try { speakText(data.response); } catch (e) { console.warn('TTS failed:', e); }
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
            // Offer to save if opened for an event
            const eventId = document.getElementById('ai-modal').dataset.eventId;
            if (eventId) {
                const saveBtn = document.createElement('button');
                saveBtn.className = 'btn btn-primary';
                saveBtn.innerText = 'Save Agenda to Event';
                saveBtn.onclick = () => saveAgendaToEvent(eventId, data.agenda);
                // append the button if not already present
                if (!document.getElementById('ai-save-agenda')) {
                    saveBtn.id = 'ai-save-agenda';
                    document.querySelector('.modal-content').appendChild(saveBtn);
                }
            }
        } else {
            document.getElementById('ai-response').innerText = data.error || 'AI error';
        }
    } catch (err) {
        document.getElementById('ai-response').innerText = err.message;
    }
}

async function callAiRecommend() {
    document.getElementById('ai-response').innerText = 'Fetching recommendations...';
    try {
        const res = await fetch(`${API_BASE}/ai/recommendations`);
        const data = await res.json();
        if (res.ok && data.success) {
            const recs = data.recommendations || [];
            if (!recs.length) {
                document.getElementById('ai-response').innerText = 'No recommendations available.';
                speakText('No recommendations available.');
                return;
            }
            // Format output
            let out = '';
            recs.forEach((r, idx) => {
                out += `${idx+1}. ${r.summary} — ${r.count} times, usually on ${r.weekday} at ${r.common_time}\n`;
                if (r.suggested_slots && r.suggested_slots.length) {
                    out += `   Suggested slots: ${r.suggested_slots.join(', ')}\n`;
                }
            });
            document.getElementById('ai-response').innerText = out;
            try { speakText('I recommend the following bookings. ' + recs.map(r => `${r.summary} on ${r.weekday} at ${r.common_time}`).join('. ')); } catch(e){console.warn('TTS failed', e)}
        } else {
            document.getElementById('ai-response').innerText = data.error || 'Recommendation error';
        }
    } catch (err) {
        document.getElementById('ai-response').innerText = err.message;
    }
}

async function callAiSummarize() {
    const notes = document.getElementById('ai-input').value.trim();
    if (!notes) {
        showToast('Please paste the meeting notes to summarize', 'warning');
        return;
    }
    document.getElementById('ai-response').innerText = 'Summarizing notes...';
    try {
        const res = await fetch(`${API_BASE}/ai/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: notes })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById('ai-response').innerText = data.summary;
            const eventId = document.getElementById('ai-modal').dataset.eventId;
            if (eventId && !document.getElementById('ai-save-summary')) {
                const saveBtn = document.createElement('button');
                saveBtn.className = 'btn btn-primary';
                saveBtn.id = 'ai-save-summary';
                saveBtn.innerText = 'Save Summary to Event';
                saveBtn.onclick = () => saveSummaryToEvent(eventId, data.summary);
                document.querySelector('.modal-content').appendChild(saveBtn);
            }
        } else {
            document.getElementById('ai-response').innerText = data.error || 'AI error';
        }
    } catch (err) {
        document.getElementById('ai-response').innerText = err.message;
    }
}

async function saveAgendaToEvent(eventId, agendaText) {
    try {
        // Open confirmation modal to let the user choose append vs overwrite
        openAiConfirmModal(eventId, agendaText);
    } catch (err) {
        showToast('❌ ' + err.message, 'error');
    }
}

async function saveSummaryToEvent(eventId, summaryText) {
    try {
        // Open confirmation modal to let the user choose append vs overwrite
        openAiConfirmModal(eventId, summaryText);
    } catch (err) {
        showToast('❌ ' + err.message, 'error');
    }
}

// Confirmation modal helpers
function openAiConfirmModal(eventId, content) {
    const modal = document.getElementById('ai-confirm-modal');
    const preview = document.getElementById('ai-confirm-preview');
    modal.style.display = 'flex';
    preview.innerText = content || '';
    modal.dataset.eventId = eventId;
    modal.dataset.content = content || '';

    // Ensure save handler is attached once
    const saveBtn = document.getElementById('ai-confirm-save');
    const newHandler = async function() {
        const mode = document.querySelector('input[name="ai-save-mode"]:checked').value || 'overwrite';
        const body = { description: modal.dataset.content, mode: mode };
        try {
            const res = await fetch(`${API_BASE}/events/${modal.dataset.eventId}/description`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await res.json();
            if (res.ok && data.success) {
                showToast('✅ Content saved to event (' + mode + ')', 'success');
                closeAiConfirmModal();
                closeAiModal();
                loadEvents();
            } else {
                showToast('❌ Failed to save: ' + (data.error || ''), 'error');
            }
        } catch (err) {
            showToast('❌ ' + err.message, 'error');
        }
    };

    // Remove previous handlers to avoid duplicates
    saveBtn.replaceWith(saveBtn.cloneNode(true));
    const newSaveBtn = document.getElementById('ai-confirm-save');
    newSaveBtn.addEventListener('click', newHandler);
}

function closeAiConfirmModal() {
    const modal = document.getElementById('ai-confirm-modal');
    modal.style.display = 'none';
    modal.dataset.eventId = '';
    modal.dataset.content = '';
    document.getElementById('ai-confirm-preview').innerText = '';
}

// Cancel event
async function cancelEvent(eventId) {
    if (!confirm('Are you sure you want to cancel this event?')) {
        return;
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

// Export event as .ics file
function formatDateToICS(dateString) {
    const d = new Date(dateString);
    // Ensure we have UTC format YYYYMMDDTHHMMSSZ
    const YYYY = d.getUTCFullYear();
    const MM = String(d.getUTCMonth() + 1).padStart(2, '0');
    const DD = String(d.getUTCDate()).padStart(2, '0');
    const hh = String(d.getUTCHours()).padStart(2, '0');
    const mm = String(d.getUTCMinutes()).padStart(2, '0');
    const ss = String(d.getUTCSeconds()).padStart(2, '0');
    return `${YYYY}${MM}${DD}T${hh}${mm}${ss}Z`;
}

async function exportEvent(eventId) {
    try {
        const res = await fetch(`${API_BASE}/events`);
        if (!res.ok) throw new Error('Failed to load events');
        const events = await res.json();
        const ev = events.find(e => e.id === eventId);
        if (!ev) throw new Error('Event not found');

        const uid = ev.id || `${Date.now()}@voice-assistant`;
        const dtstamp = formatDateToICS(new Date().toISOString());
        const dtstart = formatDateToICS(ev.start || ev.start.dateTime || ev.start.date);
        const dtend = formatDateToICS(ev.end || ev.end.dateTime || ev.end.date);
        const summary = ev.summary || 'Untitled Event';
        const description = (ev.description || '').replace(/\n/g, '\\n');
        const location = ev.location || '';

        const ics = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Voice Assistant Calendar//EN',
            'CALSCALE:GREGORIAN',
            'BEGIN:VEVENT',
            `UID:${uid}`,
            `DTSTAMP:${dtstamp}`,
            `DTSTART:${dtstart}`,
            `DTEND:${dtend}`,
            `SUMMARY:${summary.replace(/\r?\n/g, ' ')}`,
            `DESCRIPTION:${description}`,
            `LOCATION:${location}`,
            'END:VEVENT',
            'END:VCALENDAR'
        ].join('\r\n');

        const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const filename = summary.replace(/[^a-z0-9\-\._ ]/ig, '').trim() || 'event';
        a.href = url;
        a.download = `${filename}.ics`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showToast('✅ Event exported as .ics', 'success');
    } catch (err) {
        console.error('Export failed:', err);
        showToast('❌ Export failed: ' + err.message, 'error');
    }
}

// Export all loaded events as a single .ics file
async function exportAllEvents() {
    try {
        const res = await fetch(`${API_BASE}/events`);
        if (!res.ok) throw new Error('Failed to load events');
        const events = await res.json();
        if (!events || events.length === 0) {
            showToast('No events to export', 'warning');
            return;
        }

        const dtstamp = formatDateToICS(new Date().toISOString());
        const lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Voice Assistant Calendar//EN',
            'CALSCALE:GREGORIAN'
        ];

        events.forEach(ev => {
            const uid = ev.id || `${Date.now()}-${Math.floor(Math.random()*1000)}@voice-assistant`;
            const dtstart = formatDateToICS(ev.start || ev.start?.dateTime || ev.start?.date);
            const dtend = formatDateToICS(ev.end || ev.end?.dateTime || ev.end?.date);
            const summary = (ev.summary || 'Untitled Event').replace(/\r?\n/g, ' ');
            const description = (ev.description || '').replace(/\n/g, '\\n');
            const location = ev.location || '';

            lines.push('BEGIN:VEVENT');
            lines.push(`UID:${uid}`);
            lines.push(`DTSTAMP:${dtstamp}`);
            if (dtstart) lines.push(`DTSTART:${dtstart}`);
            if (dtend) lines.push(`DTEND:${dtend}`);
            lines.push(`SUMMARY:${summary}`);
            if (description) lines.push(`DESCRIPTION:${description}`);
            if (location) lines.push(`LOCATION:${location}`);
            lines.push('END:VEVENT');
        });

        lines.push('END:VCALENDAR');

        const ics = lines.join('\r\n');
        const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `events-${new Date().toISOString().slice(0,10)}.ics`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showToast('✅ All events exported as .ics', 'success');
    } catch (err) {
        console.error('Export all failed:', err);
        showToast('❌ Export all failed: ' + err.message, 'error');
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

// Theme handling: set, toggle, load from localStorage
function setTheme(theme) {
    if (!theme) return;
    document.body.classList.remove('theme-light');
    document.body.classList.remove('theme-dark');
    if (theme === 'light') {
        document.body.classList.add('theme-light');
    } else {
        // default dark
        document.body.classList.add('theme-dark');
    }
    localStorage.setItem('vac_theme', theme);
}

function toggleTheme() {
    const current = localStorage.getItem('vac_theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
}

function loadTheme() {
    const theme = localStorage.getItem('vac_theme') || 'dark';
    setTheme(theme);
}

// Compact view toggle: adds .compact to event cards
function applyCompactMode(enabled) {
    const events = document.querySelectorAll('.event-card');
    events.forEach(e => {
        if (enabled) e.classList.add('compact'); else e.classList.remove('compact');
    });
}

function toggleCompactView() {
    const current = localStorage.getItem('vac_compact') === '1';
    const next = !current;
    localStorage.setItem('vac_compact', next ? '1' : '0');
    applyCompactMode(next);
    // update button state
    const btn = document.getElementById('compact-toggle-btn');
    if (btn) btn.classList.toggle('active', next);
}

function loadCompactView() {
    const enabled = localStorage.getItem('vac_compact') === '1';
    applyCompactMode(enabled);
    const btn = document.getElementById('compact-toggle-btn');
    if (btn) btn.classList.toggle('active', enabled);
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Set today's date as default
    const today = new Date();
    document.getElementById('event-date').valueAsDate = today;

    // Load initial events
    loadEvents();

    // Load theme and compact view preferences
    loadTheme();
    loadCompactView();

    // Wire theme and compact buttons
    document.getElementById('theme-toggle-btn')?.addEventListener('click', function() {
        toggleTheme();
    });
    document.getElementById('compact-toggle-btn')?.addEventListener('click', function() {
        toggleCompactView();
    });
    // Wire Export All button
    document.getElementById('export-all-btn')?.addEventListener('click', function() {
        exportAllEvents();
    });
    
    // Wire translate button in modal (delegated via attribute)
    // The button uses inline onclick="callAiTranslate()" in the template
    // Display command history on page load
    displayCommandHistory();

    // Add keyboard support for voice input (Enter key to execute)
    document.getElementById('voice-text-input')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            executeVoiceCommand();
        }
    });

    // If user visited /ai, the server redirects to /dashboard#ai - open modal automatically
    if (window.location.hash === '#ai') {
        openAiModal();
    }

    // Chat tab keyboard support
    document.getElementById('chat-input')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {  // Ctrl+Enter to send
            e.preventDefault();
            sendChatMessage();
        }
    });
});

// ===== AI CHAT TAB FUNCTIONS =====

/**
 * Add a message to the chat history and display it
 */
function addChatMessage(role, content) {
    const chatHistory = document.getElementById('chat-history');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}-message`;
    
    const isAi = role === 'ai';
    const bgColor = isAi ? 'rgba(66, 165, 245, 0.1)' : 'rgba(76, 175, 80, 0.1)';
    const borderColor = isAi ? '#42a5f5' : '#4caf50';
    const icon = isAi ? '🤖' : '👤';
    const name = isAi ? 'AI Assistant' : 'You';
    
    messageDiv.innerHTML = `
        <div style="background: ${bgColor}; padding: 12px; border-radius: 8px; border-left: 3px solid ${borderColor};">
            <strong>${icon} ${name}:</strong>
            <div style="margin-top: 8px; white-space: pre-wrap; word-break: break-word;">${escapeHtml(content)}</div>
        </div>
    `;
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;  // Auto-scroll to bottom
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Send a chat message to the AI
 */
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) {
        showToast('Please enter a message', 'warning');
        return;
    }
    
    // Add user message to chat
    addChatMessage('user', message);
    input.value = '';
    input.style.height = 'auto';  // Reset textarea height
    
    // Show loading indicator
    addChatMessage('ai', '⏳ Thinking...');
    
    try {
        const res = await fetch(`${API_BASE}/ai/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        
        const data = await res.json();
        
        // Remove loading message
        const chatHistory = document.getElementById('chat-history');
        const lastMsg = chatHistory.lastChild;
        if (lastMsg && lastMsg.innerText.includes('Thinking')) {
            lastMsg.remove();
        }
        
        if (res.ok && data.success) {
            addChatMessage('ai', data.response);
            // Optional: speak the response
            try { speakText(data.response); } catch (e) { console.warn('TTS failed:', e); }
        } else {
            addChatMessage('ai', '❌ Error: ' + (data.error || 'Failed to get response from AI'));
        }
    } catch (err) {
        // Remove loading message
        const chatHistory = document.getElementById('chat-history');
        const lastMsg = chatHistory.lastChild;
        if (lastMsg && lastMsg.innerText.includes('Thinking')) {
            lastMsg.remove();
        }
        addChatMessage('ai', '❌ Error: ' + err.message);
    }
}

/**
 * Quick action buttons for common chat requests
 */
async function quickChatAction(action) {
    let message = '';
    
    switch(action) {
        case 'suggest':
            message = 'Please suggest the best times for me to schedule a meeting next week.';
            break;
        case 'agenda':
            message = 'Generate an agenda and action items for my meetings today.';
            break;
        case 'summary':
            message = 'Summarize my schedule for this week and highlight busy periods.';
            break;
        case 'email':
            message = 'Draft a professional follow-up email for my last meeting.';
            break;
    }
    
    if (message) {
        document.getElementById('chat-input').value = message;
        await sendChatMessage();
    }
}

