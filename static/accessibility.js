/**
 * Accessibility Module for Voice Assistant Calendar
 * Manages ARIA attributes, onboarding, accessibility features, and keyboard navigation
 */

// ===========================
// ACCESSIBILITY STATE MANAGEMENT
// ===========================

const AccessibilityManager = {
    // Onboarding state
    firstRun: localStorage.getItem('firstRunOnboarding') === null,
    onboardingStep: 0,
    isOnboarding: false,
    
    // Accessibility features
    highContrastEnabled: localStorage.getItem('highContrast') === 'true',
    reduceMotionEnabled: localStorage.getItem('reduceMotion') === 'true',
    fontSizeLevel: parseInt(localStorage.getItem('fontSizeLevel') || '0'),
    ttsSpeed: parseFloat(localStorage.getItem('ttsSpeed') || '1'),
    
    // Onboarding steps
    onboardingSteps: [
        {
            title: "Welcome to Voice Assistant Calendar!",
            text: "I'm your assistant. Let's get your trigger phrase set so I can respond to your voice commands.",
            targetElement: null,
            action: null
        },
        {
            title: "Set Your Trigger Phrase",
            text: "Please speak your trigger phrase now. Example: 'Hey Gemini'. The microphone button will pulse while listening.",
            targetElement: "#voice-record-btn",
            action: () => {
                // Highlight the microphone button
                const btn = document.getElementById('voice-record-btn');
                if (btn) btn.classList.add('onboarding-highlight');
            }
        },
        {
            title: "Confirm Trigger Phrase",
            text: "Great! Your trigger phrase is set. I won't show it to anyone else.",
            targetElement: null,
            action: null
        },
        {
            title: "Quick Book Demo",
            text: "Try saying: 'Book a meeting tomorrow at 3 PM.' I'll ask you for any missing info.",
            targetElement: "[data-tab='book']",
            action: () => {
                const btn = document.querySelector("[data-tab='book']");
                if (btn) btn.classList.add('onboarding-highlight');
            }
        },
        {
            title: "Check Your Events",
            text: "You can ask me to show today's events, upcoming week, or summarize your schedule.",
            targetElement: "[data-tab='events']",
            action: () => {
                const btn = document.querySelector("[data-tab='events']");
                if (btn) btn.classList.add('onboarding-highlight');
            }
        },
        {
            title: "Accessibility Features",
            text: "There's an accessibility toggle in the header. You can adjust text size, enable high-contrast mode, reduce animations, and set TTS speed.",
            targetElement: "#accessibility-toggle-btn",
            action: () => {
                const btn = document.getElementById('accessibility-toggle-btn');
                if (btn) btn.classList.add('onboarding-highlight');
            }
        },
        {
            title: "Theme Selection",
            text: "Switch themes anytime using the Theme button. Your preference will be remembered.",
            targetElement: "#theme-toggle-btn",
            action: () => {
                const btn = document.getElementById('theme-toggle-btn');
                if (btn) btn.classList.add('onboarding-highlight');
            }
        },
        {
            title: "Micro-Interactions",
            text: "Hover over cards for subtle animations. The assistant bubble pulses when listening. The stop button cancels TTS instantly.",
            targetElement: ".ai-card",
            action: () => {
                const card = document.querySelector('.ai-card');
                if (card) card.classList.add('onboarding-highlight');
            }
        },
        {
            title: "Keyboard Shortcuts",
            text: "Press Ctrl+K to focus on the assistant, Ctrl+N to create a new event, and Ctrl+/ to see help.",
            targetElement: null,
            action: null
        }
    ],

    /**
     * Initialize accessibility features on page load
     */
    init() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Apply saved accessibility settings
        this.applyAccessibilitySettings();
        
        // Set up keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Show onboarding if first run
        if (this.firstRun) {
            setTimeout(() => {
                this.showOnboarding();
            }, 1000);
        }
        
        // Announce page load to screen readers
        this.announceToScreenReader("Voice Assistant Calendar loaded successfully.");
    },

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Accessibility toggle button
        const accessibilityToggle = document.getElementById('accessibility-toggle-btn');
        if (accessibilityToggle) {
            accessibilityToggle.addEventListener('click', () => this.toggleAccessibilityPanel());
        }

        // High contrast toggle
        const highContrastToggle = document.getElementById('high-contrast-toggle');
        if (highContrastToggle) {
            highContrastToggle.checked = this.highContrastEnabled;
            highContrastToggle.addEventListener('change', (e) => this.toggleHighContrast(e.target.checked));
        }

        // Reduce motion toggle
        const reduceMotionToggle = document.getElementById('reduce-motion-toggle');
        if (reduceMotionToggle) {
            reduceMotionToggle.checked = this.reduceMotionEnabled;
            reduceMotionToggle.addEventListener('change', (e) => this.toggleReduceMotion(e.target.checked));
        }

        // Font size controls
        const fontSizeDecrease = document.getElementById('font-size-decrease');
        const fontSizeReset = document.getElementById('font-size-reset');
        const fontSizeIncrease = document.getElementById('font-size-increase');

        if (fontSizeDecrease) fontSizeDecrease.addEventListener('click', () => this.adjustFontSize(-1));
        if (fontSizeReset) fontSizeReset.addEventListener('click', () => this.adjustFontSize(0, true));
        if (fontSizeIncrease) fontSizeIncrease.addEventListener('click', () => this.adjustFontSize(1));

        // TTS speed control
        const ttsSpeedControl = document.getElementById('tts-speed-control');
        if (ttsSpeedControl) {
            ttsSpeedControl.value = this.ttsSpeed;
            ttsSpeedControl.addEventListener('change', (e) => this.setTTSSpeed(parseFloat(e.target.value)));
        }

        // Start onboarding button
        const startOnboardingBtn = document.getElementById('start-onboarding-btn');
        if (startOnboardingBtn) {
            startOnboardingBtn.addEventListener('click', () => this.showOnboarding());
        }

        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle-btn');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Tab navigation - update aria-selected
        const navButtons = document.querySelectorAll('.nav-btn');
        navButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleTabClick(e));
        });

        // Assistant bubble close button
        const assistantBubbleCloseBtn = document.querySelector('#assistant-bubble button:last-child');
        if (assistantBubbleCloseBtn) {
            assistantBubbleCloseBtn.addEventListener('click', () => this.hideAssistantBubble());
        }

        // Assistant stop button
        const assistantStopBtn = document.getElementById('assistant-stop-btn');
        if (assistantStopBtn) {
            assistantStopBtn.addEventListener('click', () => this.stopAssistantSpeaking());
        }
    },

    /**
     * Apply saved accessibility settings
     */
    applyAccessibilitySettings() {
        if (this.highContrastEnabled) {
            document.body.classList.add('high-contrast');
        }
        
        if (this.reduceMotionEnabled) {
            document.body.classList.add('reduce-motion');
        }
        
        if (this.fontSizeLevel !== 0) {
            document.body.style.fontSize = (16 + this.fontSizeLevel * 2) + 'px';
        }

        // Update theme from localStorage
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            document.body.classList.add('theme-light');
        }
    },

    /**
     * Toggle accessibility panel visibility
     */
    toggleAccessibilityPanel() {
        const panel = document.getElementById('accessibility-panel');
        if (panel) {
            const isVisible = panel.style.display !== 'none';
            panel.style.display = isVisible ? 'none' : 'block';
            
            // Update aria-checked on toggle button
            const btn = document.getElementById('accessibility-toggle-btn');
            if (btn) {
                btn.setAttribute('aria-checked', !isVisible);
            }

            if (!isVisible) {
                this.announceToScreenReader('Accessibility panel opened');
            }
        }
    },

    /**
     * Toggle high contrast mode
     */
    toggleHighContrast(enabled) {
        this.highContrastEnabled = enabled;
        localStorage.setItem('highContrast', enabled);
        
        if (enabled) {
            document.body.classList.add('high-contrast');
            this.announceToScreenReader('High contrast mode enabled');
        } else {
            document.body.classList.remove('high-contrast');
            this.announceToScreenReader('High contrast mode disabled');
        }
    },

    /**
     * Toggle reduce motion
     */
    toggleReduceMotion(enabled) {
        this.reduceMotionEnabled = enabled;
        localStorage.setItem('reduceMotion', enabled);
        
        if (enabled) {
            document.body.classList.add('reduce-motion');
            this.announceToScreenReader('Reduce motion enabled');
        } else {
            document.body.classList.remove('reduce-motion');
            this.announceToScreenReader('Reduce motion disabled');
        }
    },

    /**
     * Adjust font size
     */
    adjustFontSize(direction, reset = false) {
        if (reset) {
            this.fontSizeLevel = 0;
        } else {
            this.fontSizeLevel += direction;
            // Clamp between -3 and 3
            this.fontSizeLevel = Math.max(-3, Math.min(3, this.fontSizeLevel));
        }
        
        localStorage.setItem('fontSizeLevel', this.fontSizeLevel);
        
        const baseFontSize = 16 + this.fontSizeLevel * 2;
        document.body.style.fontSize = baseFontSize + 'px';
        
        const sizeLabel = ['smaller', 'default', 'larger'][this.fontSizeLevel + 3] || 'custom';
        this.announceToScreenReader(`Font size set to ${sizeLabel}`);
    },

    /**
     * Set TTS playback speed
     */
    setTTSSpeed(speed) {
        this.ttsSpeed = speed;
        localStorage.setItem('ttsSpeed', speed);
        
        // Update global TTS speed if available
        if (window.ttsSpeed !== undefined) {
            window.ttsSpeed = speed;
        }
        
        const speedLabel = {
            0.75: 'slow',
            1: 'normal',
            1.25: 'fast'
        }[speed] || 'custom';
        
        this.announceToScreenReader(`Text-to-speech speed set to ${speedLabel}`);
    },

    /**
     * Set up keyboard shortcuts
     * Ctrl+K: Focus assistant
     * Ctrl+N: New event
     * Ctrl+/: Help
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key.toLowerCase()) {
                    case 'k':
                        e.preventDefault();
                        this.focusAssistant();
                        break;
                    case 'n':
                        e.preventDefault();
                        this.newEvent();
                        break;
                    case '/':
                        e.preventDefault();
                        this.showHelp();
                        break;
                }
            }

            // Tab management for accessibility
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                const activeTab = document.querySelector('.nav-btn.active');
                if (activeTab && activeTab.closest('.nav-menu')) {
                    e.preventDefault();
                    this.navigateTabs(e.key === 'ArrowRight' ? 1 : -1);
                }
            }
        });
    },

    /**
     * Handle tab click and update ARIA attributes
     */
    handleTabClick(e) {
        const activeBtn = document.querySelector('.nav-btn.active');
        if (activeBtn) {
            activeBtn.classList.remove('active');
            activeBtn.setAttribute('aria-selected', 'false');
            activeBtn.setAttribute('tabindex', '-1');
        }

        const btn = e.target.closest('.nav-btn');
        if (btn) {
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
            btn.setAttribute('tabindex', '0');
            
            this.announceToScreenReader(`Switched to ${btn.textContent.trim()} tab`);
        }
    },

    /**
     * Navigate between tabs with arrow keys
     */
    navigateTabs(direction) {
        const tabs = Array.from(document.querySelectorAll('.nav-btn'));
        const activeIndex = tabs.findIndex(tab => tab.classList.contains('active'));
        
        if (activeIndex === -1) return;
        
        let newIndex = activeIndex + direction;
        if (newIndex < 0) newIndex = tabs.length - 1;
        if (newIndex >= tabs.length) newIndex = 0;
        
        tabs[newIndex].click();
        tabs[newIndex].focus();
    },

    /**
     * Focus on assistant
     */
    focusAssistant() {
        const micBtn = document.getElementById('voice-record-btn');
        if (micBtn) {
            micBtn.focus();
            this.announceToScreenReader('Assistant focused. Press space to start recording.');
        }
    },

    /**
     * Create new event
     */
    newEvent() {
        const bookTab = document.querySelector('[data-tab="book"]');
        if (bookTab) {
            bookTab.click();
            const titleInput = document.getElementById('event-summary');
            if (titleInput) {
                setTimeout(() => titleInput.focus(), 100);
            }
            this.announceToScreenReader('New event form opened');
        }
    },

    /**
     * Show help/commands
     */
    showHelp() {
        const commandsTab = document.querySelector('[data-tab="commands"]');
        if (commandsTab) {
            commandsTab.click();
            this.announceToScreenReader('Voice commands help displayed');
        }
    },

    /**
     * Show onboarding sequence
     */
    showOnboarding() {
        this.isOnboarding = true;
        this.onboardingStep = 0;
        
        // Mark first run as complete
        localStorage.setItem('firstRunOnboarding', 'true');
        
        this.showOnboardingStep();
    },

    /**
     * Show current onboarding step
     */
    showOnboardingStep() {
        if (this.onboardingStep >= this.onboardingSteps.length) {
            this.endOnboarding();
            return;
        }

        const step = this.onboardingSteps[this.onboardingStep];
        const stepNumber = this.onboardingStep + 1;
        
        // Show notification with step
        const message = `Step ${stepNumber} of ${this.onboardingSteps.length}: ${step.title}. ${step.text}`;
        
        // Clear previous highlights
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
        });

        // Apply action
        if (step.action) {
            step.action();
        }

        // Show toast notification
        const toast = showToast(message, 'info', 0);
        
        // Add onboarding controls to toast
        const controls = document.createElement('div');
        controls.style.cssText = 'display: flex; gap: 8px; margin-top: 12px;';
        controls.innerHTML = `
            <button class="btn btn-ghost btn-small" onclick="AccessibilityManager.skipOnboarding()" aria-label="Skip onboarding tour">Skip</button>
            <button class="btn btn-primary btn-small" onclick="AccessibilityManager.nextOnboardingStep()" aria-label="Continue to next step">Next →</button>
        `;
        
        toast.appendChild(controls);

        // Announce to screen reader
        this.announceToScreenReader(`Onboarding step ${stepNumber}: ${step.title}. ${step.text}`);
        
        // Also speak via TTS if available
        if (window.playAssistantAudio) {
            window.playAssistantAudio(`Step ${stepNumber}. ${step.text}`, false);
        }
    },

    /**
     * Go to next onboarding step
     */
    nextOnboardingStep() {
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
        });
        
        this.onboardingStep++;
        this.showOnboardingStep();
    },

    /**
     * Skip onboarding
     */
    skipOnboarding() {
        this.endOnboarding();
        showToast('Onboarding skipped. You can restart it anytime from the accessibility menu.', 'info', 4000);
    },

    /**
     * End onboarding sequence
     */
    endOnboarding() {
        this.isOnboarding = false;
        
        // Clear highlights
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
        });

        showToast('✓ Onboarding complete! You\'re all set. Press Ctrl+/ for help anytime.', 'success', 4000);
        this.announceToScreenReader('Onboarding tour complete. You can now start using the application.');
    },

    /**
     * Show assistant bubble
     */
    showAssistantBubble(message) {
        const bubble = document.getElementById('assistant-bubble');
        if (bubble) {
            const textEl = document.getElementById('assistant-bubble-text');
            if (textEl) textEl.textContent = message;
            bubble.style.display = 'block';
            this.announceToScreenReader(`Assistant says: ${message}`);
        }
    },

    /**
     * Hide assistant bubble
     */
    hideAssistantBubble() {
        const bubble = document.getElementById('assistant-bubble');
        if (bubble) {
            bubble.style.display = 'none';
        }
    },

    /**
     * Stop assistant speaking
     */
    stopAssistantSpeaking() {
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        this.announceToScreenReader('Assistant stopped speaking');
    },

    /**
     * Toggle theme
     */
    toggleTheme() {
        const isLight = document.body.classList.toggle('theme-light');
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
        
        const themeBtn = document.getElementById('theme-toggle-btn');
        if (themeBtn) {
            const newLabel = isLight ? 'Toggle color theme (current: light)' : 'Toggle color theme (current: dark)';
            themeBtn.setAttribute('aria-label', newLabel);
            themeBtn.setAttribute('aria-checked', isLight);
        }

        const themeName = isLight ? 'light' : 'dark';
        this.announceToScreenReader(`Theme switched to ${themeName} mode`);
    },

    /**
     * Announce message to screen readers
     */
    announceToScreenReader(message) {
        // Create or reuse live region
        let liveRegion = document.getElementById('sr-live-region');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'sr-live-region';
            liveRegion.className = 'sr-only';
            liveRegion.setAttribute('role', 'status');
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            document.body.appendChild(liveRegion);
        }
        
        liveRegion.textContent = message;
    }
};

/**
 * Initialize accessibility on DOM ready
 */
document.addEventListener('DOMContentLoaded', () => {
    AccessibilityManager.init();
});

/**
 * Export for global access
 */
window.AccessibilityManager = AccessibilityManager;
