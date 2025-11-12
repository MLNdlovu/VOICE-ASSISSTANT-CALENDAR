// Voice Assistant Calendar - Web Dashboard JavaScript

const API_BASE = '/api';

// Tab switching
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const tab = this.getAttribute('data-tab');
        switchTab(tab);
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
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Add active class to clicked button
    event.target.classList.add('active');

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

    try {
        const response = await fetch(`${API_BASE}/cancel/${eventId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to cancel event');

        showMessage('events-list', '✅ Event cancelled', 'success');
        loadEvents();
    } catch (error) {
        console.error('Error cancelling event:', error);
        showMessage('events-list', `❌ ${error.message}`, 'error');
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
        showMessage('booking-message', '✅ Event booked successfully!', 'success');
        
        // Reset form
        this.reset();
        
        // Set date to today if not already
        document.getElementById('event-date').valueAsDate = new Date();

        // Show success for 3 seconds
        setTimeout(() => {
            document.getElementById('booking-message').style.display = 'none';
        }, 3000);

    } catch (error) {
        console.error('Error booking event:', error);
        showMessage('booking-message', `❌ ${error.message}`, 'error');
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

        showMessage('settings-message', '✅ Settings saved successfully!', 'success');

        // Hide message after 3 seconds
        setTimeout(() => {
            document.getElementById('settings-message').style.display = 'none';
        }, 3000);

    } catch (error) {
        console.error('Error saving settings:', error);
        showMessage('settings-message', `❌ ${error.message}`, 'error');
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
});
