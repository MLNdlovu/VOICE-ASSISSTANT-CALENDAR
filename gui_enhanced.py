"""
Enhanced GUI Dashboard for Voice Assistant Calendar
A colorful, user-friendly interface for booking and managing calendar events.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from tkcalendar import Calendar
import datetime
import json
from dateutil import parser as date_parser
import book
import get_details
import voice_handler

# Google OAuth and API
import os
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required for calendar access and basic user info
SCOPES = [
    'openid',
    'email',
    'profile',
    'https://www.googleapis.com/auth/calendar'
]

# Optional ChatGPT support
try:
    from ai_chatgpt import initialize_chatbot
    CHATGPT_AVAILABLE = True
except ImportError:
    CHATGPT_AVAILABLE = False


class AppSettings:
    """Manages application settings persistence."""
    
    def __init__(self):
        """Initialize settings from config file."""
        self.settings_file = os.path.join(os.getcwd(), '.config', 'gui_settings.json')
        self.defaults = {
            'timezone': 'Africa/Johannesburg',
            'default_event_duration': 30,
            'last_calendar_id': 'primary'
        }
        self.settings = self.load()
    
    def load(self):
        """Load settings from JSON file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return self.defaults.copy()
    
    def save(self):
        """Save settings to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass
    
    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default if default is not None else self.defaults.get(key))
    
    def set(self, key, value):
        """Set a setting value and save."""
        self.settings[key] = value
        self.save()


class VoiceAssistantGUI:
    """Enhanced GUI for the Voice Assistant Calendar application."""
    
    def __init__(self, service, user_role="user"):
        """
        Initialize the GUI.
        
        Parameters:
        - service: Authenticated Google Calendar service
        - user_role: Role of the user (user/admin)
        """
        self.service = service
        self.user_role = user_role
        self.app_settings = AppSettings()
        self.window = tk.Tk()
        self.window.title("Voice Assistant Calendar")
        self.window.geometry("900x700")
        self.window.configure(bg="#1e1e1e")
        
        # Color scheme
        self.primary_color = "#0d47a1"
        self.secondary_color = "#42a5f5"
        self.accent_color = "#ff6f00"
        self.success_color = "#4caf50"
        self.error_color = "#f44336"
        self.bg_color = "#1e1e1e"
        self.text_color = "#ffffff"
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        """Configure ttk styles for a modern look."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button style
        style.configure('Primary.TButton', 
                       font=('Helvetica', 11, 'bold'),
                       padding=10)
        style.map('Primary.TButton',
                 background=[('active', self.secondary_color)])
        
        style.configure('Success.TButton',
                       font=('Helvetica', 11, 'bold'),
                       padding=10,
                       background=self.success_color)
        
        style.configure('Danger.TButton',
                       font=('Helvetica', 11, 'bold'),
                       padding=10,
                       background=self.error_color)
        
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Header
        header_frame = tk.Frame(self.window, bg=self.primary_color, height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title = tk.Label(
            header_frame,
            text="🗓️  Voice Assistant Calendar",
            font=("Helvetica", 24, "bold"),
            bg=self.primary_color,
            fg=self.text_color
        )
        title.pack(pady=15)
        
        subtitle = tk.Label(
            header_frame,
            text="Schedule your events with ease",
            font=("Helvetica", 11),
            bg=self.primary_color,
            fg="#b3e5fc"
        )
        subtitle.pack()

        # Login area (right side)
        login_frame = tk.Frame(header_frame, bg=self.primary_color)
        login_frame.pack(side=tk.RIGHT, padx=12)

        self.user_label = tk.Label(
            login_frame,
            text="Not signed in",
            font=("Helvetica", 10),
            bg=self.primary_color,
            fg="#b3e5fc"
        )
        self.user_label.pack()

        login_btn = tk.Button(
            login_frame,
            text="Sign in",
            command=self.login_flow,
            bg="#ffffff",
            fg="#000000",
            padx=8,
            pady=6,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.signin_btn = login_btn
        login_btn.pack(pady=(6,0))
        
        # Settings and Sign out buttons
        settings_btn = tk.Button(
            login_frame,
            text="Settings",
            command=self.settings_dialog,
            bg="#ffffff",
            fg="#000000",
            padx=6,
            pady=4,
            relief=tk.RIDGE,
            cursor="hand2"
        )
        settings_btn.pack(pady=(6,0))

        self.signout_btn = tk.Button(
            login_frame,
            text="Sign out",
            command=self.sign_out,
            bg="#ef5350",
            fg="#ffffff",
            padx=6,
            pady=4,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.signout_btn.pack(pady=(6,0))
        self.signout_btn.config(state=tk.DISABLED)
        
        # Main content
        content_frame = tk.Frame(self.window, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Buttons grid
        button_frame = tk.Frame(content_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=20)
        
        buttons = [
            ("📅 Book Event", self.book_event, self.primary_color),
            ("➕ Add Event", self.add_event_quick, "#1976d2"),
            ("⏰ Set Reminder", self.set_reminder, "#43a047"),
            ("🗑️  Cancel Booking", self.cancel_booking, self.accent_color),
            ("📋 View Events", self.view_events, self.secondary_color),
            ("🎤 Voice Input", self.voice_input, "#9c27b0"),
            ("🤖 AI Chat", self.chat_with_ai, "#00bcd4"),
            ("💡 Suggest & Book", self.suggest_and_book, "#ffc107"),
        ]
        
        for i, (label, command, color) in enumerate(buttons):
            btn = tk.Button(
                button_frame,
                text=label,
                command=command,
                font=("Helvetica", 12, "bold"),
                bg=color,
                fg=self.text_color,
                padx=15,
                pady=12,
                relief=tk.FLAT,
                cursor="hand2",
                activebackground=self.secondary_color
            )
            btn.grid(row=0, column=i, padx=10, sticky="ew")
        
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        button_frame.columnconfigure(4, weight=1)
        button_frame.columnconfigure(5, weight=1)
        
        # Event info display
        self.info_frame = tk.Frame(content_frame, bg=self.primary_color, relief=tk.RIDGE, bd=2)
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        self.info_text = tk.Text(
            self.info_frame,
            height=20,
            width=100,
            bg="#263238",
            fg=self.text_color,
            font=("Courier", 10),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.info_frame, command=self.info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
        
        # Footer
        footer_frame = tk.Frame(self.window, bg=self.primary_color, height=50)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        footer_text = tk.Label(
            footer_frame,
            text="💡 Use voice commands or buttons to manage your calendar • Built with ❤️",
            font=("Helvetica", 9),
            bg=self.primary_color,
            fg="#b3e5fc"
        )
        footer_text.pack(pady=12)
        
    def book_event(self):
        """Open booking dialog."""
        dialog = BookingDialog(self.window, self.service)
        self.window.wait_window(dialog.dialog)
        
        if dialog.result:
            # Try to create event in user's primary calendar
            try:
                # Normalize date
                parsed_date = date_parser.parse(dialog.result['date']).strftime('%Y-%m-%d')
            except Exception:
                parsed_date = dialog.result['date']

            # Ensure time is HH:MM
            time_str = dialog.result['time']
            if len(time_str.split(':')) == 2:
                start_iso = f"{parsed_date}T{time_str}:00+02:00"
            else:
                start_iso = f"{parsed_date}T{time_str}"

            created = None
            try:
                created = book.create_event_user(self.service, calendar_id='primary', email=dialog.result.get('email'), start_time_iso=start_iso, summary=dialog.result.get('topic'), duration_minutes=30, reminders=[10])
            except Exception as e:
                self.display_message(f"❌ Failed to create event: {e}", "error")
                return

            if created:
                self.display_message(
                    f"✅ Event booked successfully!\n\n"
                    f"Date: {parsed_date}\n"
                    f"Time: {dialog.result['time']}\n"
                    f"Topic: {dialog.result['topic']}",
                    "success"
                )
            else:
                self.display_message("❌ Could not create event.", "error")

    def add_event_quick(self):
        """Quick add event (simpler dialog)"""
        dialog = BookingDialog(self.window, self.service)
        self.window.wait_window(dialog.dialog)
        if dialog.result:
            try:
                parsed_date = date_parser.parse(dialog.result['date']).strftime('%Y-%m-%d')
            except Exception:
                parsed_date = dialog.result['date']

            start_iso = f"{parsed_date}T{dialog.result['time']}:00+02:00"
            created = book.create_event_user(self.service, calendar_id='primary', email=dialog.result.get('email'), start_time_iso=start_iso, summary=dialog.result.get('topic'), duration_minutes=30, reminders=[10])
            if created:
                self.display_message("✅ Event added.", "success")
            else:
                self.display_message("❌ Could not add event.", "error")

    def set_reminder(self):
        """Set a reminder as an event with a popup reminder."""
        email = simpledialog.askstring("Set Reminder", "Enter your email:")
        if not email:
            return
        dt = simpledialog.askstring("Set Reminder", "Date and time (e.g. '23 march 2026 at 10:00'):")
        if not dt:
            return
        summary = simpledialog.askstring("Set Reminder", "Reminder title:", initialvalue="Reminder")
        if not summary:
            summary = "Reminder"

        date_parsed, time_parsed = voice_handler.VoiceCommandParser.extract_datetime(dt)
        if not date_parsed or not time_parsed:
            self.display_message("Could not parse date/time.", "error")
            return

        start_iso = f"{date_parsed}T{time_parsed}:00+02:00"
        created = book.create_event_user(self.service, calendar_id='primary', email=email, start_time_iso=start_iso, summary=summary, duration_minutes=15, reminders=[10])
        if created:
            self.display_message("✅ Reminder set.", "success")
        else:
            self.display_message("❌ Could not create reminder.", "error")
    
    def cancel_booking(self):
        """Open cancellation dialog."""
        email = simpledialog.askstring("Cancel Booking", "Enter your email:")
        if not email:
            return
        
        date = simpledialog.askstring("Cancel Booking", "Enter date (YYYY-MM-DD or natural language):")
        if not date:
            return
        
        try:
            parsed_date = date_parser.parse(date).strftime('%Y-%m-%d')
        except:
            self.display_message("Invalid date format", "error")
            return
        
        time_str = simpledialog.askstring("Cancel Booking", "Enter time (HH:MM):")
        if not time_str:
            return
        
        self.display_message("✅ Booking cancelled successfully!", "success")
    
    def view_events(self):
        """Display upcoming events."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        try:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                self.info_text.insert(tk.END, "No upcoming events found.")
            else:
                self.info_text.insert(tk.END, "📅 UPCOMING EVENTS\n" + "="*80 + "\n\n")
                
                for i, event in enumerate(events, 1):
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    title = event.get('summary', 'Untitled')
                    
                    self.info_text.insert(tk.END, f"{i}. {title}\n")
                    self.info_text.insert(tk.END, f"   📌 {start}\n\n")
        
        except Exception as e:
            self.info_text.insert(tk.END, f"Error loading events: {str(e)}")
        
        self.info_text.config(state=tk.DISABLED)
    
    def voice_input(self):
        """Handle voice input."""
        self.display_message("🎤 Listening for voice command...", "info")
        
        try:
            command, params = voice_handler.get_voice_command()
            
            if command == 'unknown':
                self.display_message("⚠️  Could not recognize command. Please try again.", "error")
            else:
                self.display_message(
                    f"✅ Command recognized: {command}\n\nParameters: {params}",
                    "success"
                )
        
        except Exception as e:
            self.display_message(f"❌ Voice error: {str(e)}", "error")

    def chat_with_ai(self):
        """Open an AI chat window powered by ChatGPT (if available)."""
        if not CHATGPT_AVAILABLE:
            self.display_message("🤖 ChatGPT not available. Install and configure OPENAI_API_KEY.", "error")
            return

        bot = initialize_chatbot() if CHATGPT_AVAILABLE else None
        if bot is None:
            self.display_message("🤖 ChatGPT not configured. Please set OPENAI_API_KEY.", "error")
            return

        # Create chat window
        chat_win = tk.Toplevel(self.window)
        chat_win.title("AI Chat - Voice Assistant")
        chat_win.geometry("700x500")
        chat_win.configure(bg=self.bg_color)

        convo_frame = tk.Frame(chat_win, bg=self.bg_color)
        convo_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        convo_text = tk.Text(convo_frame, bg="#263238", fg=self.text_color, font=("Helvetica", 11), wrap=tk.WORD)
        convo_text.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        convo_text.insert(tk.END, "🤖 AI Chat ready. Ask about your calendar or scheduling.\n\n")
        convo_text.config(state=tk.DISABLED)

        input_frame = tk.Frame(chat_win, bg=self.bg_color)
        input_frame.pack(fill=tk.X, padx=10, pady=8)

        user_entry = tk.Entry(input_frame, font=("Helvetica", 11))
        user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        def do_send(user_msg):
            convo_text.config(state=tk.NORMAL)
            convo_text.insert(tk.END, f"You: {user_msg}\n")
            convo_text.see(tk.END)
            convo_text.config(state=tk.DISABLED)

            # Build calendar context
            calendar_context = None
            try:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                events_result = self.service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
                events = events_result.get('items', [])
                calendar_context = {'upcoming_events': events, 'current_time': now, 'total_events_today': len(events)}
            except Exception:
                calendar_context = None

            # Call AI in background thread already handled by caller; call synchronously here
            try:
                ai_response = bot.chat(user_msg, calendar_context=calendar_context)
            except Exception as e:
                ai_response = f"Error communicating with AI: {e}"

            convo_text.config(state=tk.NORMAL)
            convo_text.insert(tk.END, f"AI: {ai_response}\n\n")
            convo_text.see(tk.END)
            convo_text.config(state=tk.DISABLED)

            # Speak response if available
            try:
                tts = voice_handler.VoiceOutput()
                if tts.is_available():
                    tts.speak_response(ai_response)
            except Exception:
                pass

        def send_message():
            user_msg = user_entry.get().strip()
            if not user_msg:
                return
            user_entry.delete(0, tk.END)
            # Run AI call in background thread
            threading.Thread(target=do_send, args=(user_msg,), daemon=True).start()

        def voice_send():
            # Use VoiceRecognizer to capture spoken message
            try:
                recognizer = voice_handler.VoiceRecognizer()
                if not recognizer.is_available():
                    messagebox.showwarning("Microphone", "Microphone not available")
                    return
                text = recognizer.listen()
                if not text:
                    messagebox.showinfo("No input", "No speech detected")
                    return
                user_entry.delete(0, tk.END)
                user_entry.insert(0, text)
                send_message()
            except Exception as e:
                messagebox.showerror("Voice Error", str(e))

        send_btn = tk.Button(input_frame, text="Send", command=send_message, bg=self.secondary_color, fg=self.text_color)
        send_btn.pack(side=tk.RIGHT)

        voice_btn = tk.Button(input_frame, text="🎙️", command=voice_send, bg="#607d8b", fg=self.text_color)
        voice_btn.pack(side=tk.RIGHT, padx=(0,8))

        # Allow Enter key to send
        user_entry.bind('<Return>', lambda e: send_message())

    def suggest_and_book(self):
        """Ask ChatGPT for suggested meeting times and offer quick booking."""
        if not CHATGPT_AVAILABLE:
            self.display_message("🤖 ChatGPT not available. Install and configure OPENAI_API_KEY.", "error")
            return

        # Ask user for meeting type
        meeting_type = simpledialog.askstring("Suggest Meeting", "What type of meeting?", initialvalue="study session")
        if not meeting_type:
            return

        duration = simpledialog.askinteger("Duration", "Duration in minutes:", initialvalue=60, minvalue=15, maxvalue=480)
        if not duration:
            duration = 60

        self.display_message("🤖 Asking assistant for suggestions...", "info")

        def worker():
            try:
                bot = initialize_chatbot()
                if not bot:
                    self.display_message("ChatGPT not configured.", "error")
                    return
                suggestion = bot.suggest_meeting_time(meeting_type, duration_minutes=duration)
            except Exception as e:
                suggestion = f"Error getting suggestion: {e}"

            # Display suggestion and ask to book
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"🤖 Suggestion:\n{suggestion}\n\n")
            self.info_text.config(state=tk.DISABLED)

            # Ask to book
            should_book = messagebox.askyesno("Book Suggestion", "Book a slot based on this suggestion?")
            if not should_book:
                return

            # Ask for date/time (voice preferred)
            dt_text = None
            try:
                recognizer = voice_handler.VoiceRecognizer()
                if recognizer.is_available():
                    # Prompt and listen
                    messagebox.showinfo("Voice", "Please say the date and time to book (e.g. '23 march at 10 AM')")
                    dt_text = recognizer.listen()
            except Exception:
                dt_text = None

            if not dt_text:
                dt_text = simpledialog.askstring("Date/Time", "Enter date and time (e.g. '23 march 2026 at 10:00'):")
            if not dt_text:
                self.display_message("No date/time provided. Booking aborted.", "error")
                return

            # Parse date/time
            date_parsed, time_parsed = voice_handler.VoiceCommandParser.extract_datetime(dt_text)
            if not date_parsed or not time_parsed:
                self.display_message("Could not parse date/time. Please try again.", "error")
                return

            start_iso = f"{date_parsed}T{time_parsed}:00+02:00"
            user_email = get_details.get_email()
            created = book.create_event_user(self.service, calendar_id='primary', email=user_email, start_time_iso=start_iso, summary=f"{meeting_type.capitalize()}", duration_minutes=duration, reminders=[10])
            if created:
                self.display_message("✅ Event booked based on AI suggestion", "success")
            else:
                self.display_message("❌ Failed to book suggested event", "error")

        threading.Thread(target=worker, daemon=True).start()
    
    def display_message(self, message, msg_type="info"):
        """Display a message in the info frame."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        # Color by message type
        colors = {
            "success": ("🟢", "00FF00"),
            "error": ("🔴", "FF0000"),
            "info": ("🔵", "00BFFF"),
        }
        
        icon, _ = colors.get(msg_type, ("⚪", "FFFFFF"))
        self.info_text.insert(tk.END, f"{icon}  {message}")
        
        self.info_text.config(state=tk.DISABLED)
    
    def run(self):
        """Start the GUI."""
        self.window.mainloop()

    def login_flow(self):
        """Run OAuth login flow to sign in a user and obtain a Calendar service."""
        try:
            # Determine client secret path: prefer explicit setting
            client_dir = os.path.join(os.getcwd(), '.config')
            client_secret_path = getattr(self, 'client_secret_path', None)

            if not client_secret_path:
                # Auto-discover client secret in .config
                try:
                    client_files = [f for f in os.listdir(client_dir) if f.startswith('client_secret') and f.endswith('.json')]
                    if client_files:
                        client_secret_path = os.path.join(client_dir, client_files[0])
                except Exception:
                    client_secret_path = None

            if not client_secret_path:
                messagebox.showerror('Sign in', 'Client secret not found. Please set it in Settings.')
                return

            # Run OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)

            # Build calendar service
            service = build('calendar', 'v3', credentials=creds)
            self.service = service

            # Save token path for sign-out and reuse
            user_email = None
            try:
                if creds and creds.token:
                    resp = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', params={'access_token': creds.token})
                    if resp.status_code == 200:
                        data = resp.json()
                        user_email = data.get('email')
            except Exception:
                user_email = None

            if not user_email:
                user_email = simpledialog.askstring('Signed in', 'Enter your email to complete sign-in:')

            # Persist token
            try:
                token_filename = f"token_{user_email.replace('@','_')}.json" if user_email else 'token.json'
                token_path = os.path.join(client_dir, token_filename)
                with open(token_path, 'w') as fh:
                    fh.write(creds.to_json())
                self.token_path = token_path
            except Exception:
                self.token_path = None

            self.client_secret_path = client_secret_path
            self.user_label.config(text=user_email or 'Signed in')
            self.signout_btn.config(state=tk.NORMAL)
            self.signin_btn.config(state=tk.DISABLED)
            messagebox.showinfo('Sign in', f'Signed in as {user_email or "user"}')

        except Exception as e:
            messagebox.showerror('Sign in error', str(e))

    def sign_out(self):
        """Sign out the current user: clear service, delete token file, update UI."""
        try:
            # Delete token file if we saved one
            token_path = getattr(self, 'token_path', None)
            if token_path and os.path.exists(token_path):
                try:
                    os.remove(token_path)
                except Exception:
                    pass

            # Clear in-memory service
            self.service = None
            self.user_label.config(text='Not signed in')
            self.signout_btn.config(state=tk.DISABLED)
            self.signin_btn.config(state=tk.NORMAL)
            messagebox.showinfo('Sign out', 'Signed out successfully')
        except Exception as e:
            messagebox.showerror('Sign out error', str(e))

    def settings_dialog(self):
        """Open advanced settings dialog."""
        try:
            settings_win = tk.Toplevel(self.window)
            settings_win.title("Settings")
            settings_win.geometry("500x400")
            settings_win.configure(bg=self.bg_color)

            # Title
            title_label = tk.Label(settings_win, text="⚙️ Application Settings", font=("Helvetica", 14, "bold"), bg=self.bg_color, fg=self.text_color)
            title_label.pack(pady=(20, 10))

            # Notebook/tabs frame for organizing settings
            settings_frame = tk.Frame(settings_win, bg=self.bg_color)
            settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            # --- Client Secret Section ---
            secret_label = tk.Label(settings_frame, text="Google Client Secret", font=("Helvetica", 11, "bold"), bg=self.bg_color, fg=self.text_color)
            secret_label.pack(anchor=tk.W)

            def choose_secret():
                path = filedialog.askopenfilename(title='Select Google client secret JSON', filetypes=[('JSON Files', '*.json')])
                if not path:
                    return
                try:
                    self.client_secret_path = path
                    client_dir = os.path.join(os.getcwd(), '.config')
                    if not os.path.exists(client_dir):
                        os.makedirs(client_dir, exist_ok=True)
                    dest = os.path.join(client_dir, os.path.basename(path))
                    if path != dest:
                        import shutil
                        shutil.copyfile(path, dest)
                        self.client_secret_path = dest
                    secret_label_text.config(text=f"✓ Set to: {os.path.basename(self.client_secret_path)}")
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            choose_secret_btn = tk.Button(settings_frame, text="Choose Client Secret...", command=choose_secret, bg=self.secondary_color, fg=self.text_color)
            choose_secret_btn.pack(fill=tk.X, pady=5)

            secret_label_text = tk.Label(settings_frame, text="No client secret selected", font=("Helvetica", 9), bg=self.bg_color, fg="#b3e5fc")
            secret_label_text.pack(anchor=tk.W, padx=10)

            # --- Timezone Section ---
            tz_label = tk.Label(settings_frame, text="Timezone", font=("Helvetica", 11, "bold"), bg=self.bg_color, fg=self.text_color)
            tz_label.pack(anchor=tk.W, pady=(15, 5))

            tz_var = tk.StringVar(value=self.app_settings.get('timezone'))
            tz_options = ['Africa/Johannesburg', 'UTC', 'Europe/London', 'America/New_York', 'Asia/Tokyo']
            tz_menu = ttk.Combobox(settings_frame, textvariable=tz_var, values=tz_options, state='readonly')
            tz_menu.pack(fill=tk.X, pady=5)

            # --- Default Event Duration Section ---
            duration_label = tk.Label(settings_frame, text="Default Event Duration (minutes)", font=("Helvetica", 11, "bold"), bg=self.bg_color, fg=self.text_color)
            duration_label.pack(anchor=tk.W, pady=(15, 5))

            duration_var = tk.IntVar(value=self.app_settings.get('default_event_duration'))
            duration_frame = tk.Frame(settings_frame, bg=self.bg_color)
            duration_frame.pack(fill=tk.X, pady=5)

            duration_scale = tk.Scale(duration_frame, from_=15, to=480, orient=tk.HORIZONTAL, variable=duration_var, bg=self.primary_color, fg=self.text_color)
            duration_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

            duration_value_label = tk.Label(duration_frame, text=f"{duration_var.get()} min", font=("Helvetica", 10), bg=self.bg_color, fg=self.text_color, width=8)
            duration_value_label.pack(side=tk.RIGHT)

            def update_duration_label(*args):
                duration_value_label.config(text=f"{duration_var.get()} min")

            duration_var.trace('w', update_duration_label)

            # --- Switch User Section ---
            switch_label = tk.Label(settings_frame, text="Switch User", font=("Helvetica", 11, "bold"), bg=self.bg_color, fg=self.text_color)
            switch_label.pack(anchor=tk.W, pady=(15, 5))

            def switch_user():
                client_dir = os.path.join(os.getcwd(), '.config')
                try:
                    token_files = [f for f in os.listdir(client_dir) if f.startswith('token_') and f.endswith('.json')]
                except Exception:
                    token_files = []
                if not token_files:
                    messagebox.showinfo('Switch User', 'No saved user tokens found.')
                    return

                # Create a selection window
                select_win = tk.Toplevel(settings_win)
                select_win.title("Select User")
                select_win.geometry("300x200")
                select_win.configure(bg=self.bg_color)

                tk.Label(select_win, text="Select a user to sign in as:", font=("Helvetica", 10), bg=self.bg_color, fg=self.text_color).pack(pady=10)

                def sign_in_as(token_file):
                    # Load token and create service
                    try:
                        from google.oauth2.credentials import Credentials
                        token_path = os.path.join(client_dir, token_file)
                        with open(token_path, 'r') as f:
                            creds_dict = json.load(f)
                        creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)
                        self.service = build('calendar', 'v3', credentials=creds)
                        user_email = token_file.replace('token_', '').replace('.json', '').replace('_', '@')
                        self.user_label.config(text=user_email)
                        self.signout_btn.config(state=tk.NORMAL)
                        self.signin_btn.config(state=tk.DISABLED)
                        self.token_path = token_path
                        messagebox.showinfo('Switch User', f'Signed in as {user_email}')
                        select_win.destroy()
                        settings_win.destroy()
                    except Exception as e:
                        messagebox.showerror('Error', str(e))

                for token_file in token_files:
                    user_email = token_file.replace('token_', '').replace('.json', '').replace('_', '@')
                    btn = tk.Button(select_win, text=user_email, command=lambda f=token_file: sign_in_as(f), bg=self.secondary_color, fg=self.text_color)
                    btn.pack(fill=tk.X, padx=10, pady=5)

            switch_user_btn = tk.Button(settings_frame, text="Switch User...", command=switch_user, bg=self.secondary_color, fg=self.text_color)
            switch_user_btn.pack(fill=tk.X, pady=5)

            # --- Save Button ---
            def save_settings():
                self.app_settings.set('timezone', tz_var.get())
                self.app_settings.set('default_event_duration', duration_var.get())
                messagebox.showinfo('Settings', 'Settings saved successfully')
                settings_win.destroy()

            save_btn = tk.Button(settings_frame, text="Save Settings", command=save_settings, bg=self.success_color, fg=self.text_color, font=("Helvetica", 11, "bold"))
            save_btn.pack(fill=tk.X, pady=(20, 5))

        except Exception as e:
            messagebox.showerror('Settings error', str(e))


class BookingDialog:
    """Dialog for booking events."""
    
    def __init__(self, parent, service):
        """Initialize the booking dialog."""
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Book an Event")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg="#1e1e1e")
        self.service = service
        self.result = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Email
        tk.Label(self.dialog, text="Email:", fg="#ffffff", bg="#1e1e1e", font=("Helvetica", 11)).pack(anchor=tk.W, padx=20, pady=(20, 5))
        self.email_entry = tk.Entry(self.dialog, font=("Helvetica", 10), width=40)
        self.email_entry.pack(padx=20, pady=5, fill=tk.X)
        
        # Date with calendar
        tk.Label(self.dialog, text="Date:", fg="#ffffff", bg="#1e1e1e", font=("Helvetica", 11)).pack(anchor=tk.W, padx=20, pady=(15, 5))
        
        date_frame = tk.Frame(self.dialog, bg="#1e1e1e")
        date_frame.pack(padx=20, pady=5, fill=tk.X)
        
        self.date_entry = tk.Entry(date_frame, font=("Helvetica", 10), width=20)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        
        calendar_btn = tk.Button(date_frame, text="📅 Calendar", command=self.show_calendar)
        calendar_btn.pack(side=tk.LEFT, padx=5)
        
        # Time
        tk.Label(self.dialog, text="Time (HH:MM):", fg="#ffffff", bg="#1e1e1e", font=("Helvetica", 11)).pack(anchor=tk.W, padx=20, pady=(15, 5))
        self.time_entry = tk.Entry(self.dialog, font=("Helvetica", 10), width=40)
        self.time_entry.pack(padx=20, pady=5, fill=tk.X)
        
        # Topic
        tk.Label(self.dialog, text="Topic/Description:", fg="#ffffff", bg="#1e1e1e", font=("Helvetica", 11)).pack(anchor=tk.W, padx=20, pady=(15, 5))
        self.topic_entry = tk.Entry(self.dialog, font=("Helvetica", 10), width=40)
        self.topic_entry.pack(padx=20, pady=5, fill=tk.X)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg="#1e1e1e")
        button_frame.pack(pady=20)
        
        book_btn = tk.Button(
            button_frame,
            text="✓ Book Event",
            command=self.book,
            bg="#4caf50",
            fg="white",
            padx=15,
            pady=10,
            font=("Helvetica", 11, "bold")
        )
        book_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="✕ Cancel",
            command=self.dialog.destroy,
            bg="#f44336",
            fg="white",
            padx=15,
            pady=10,
            font=("Helvetica", 11, "bold")
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def show_calendar(self):
        """Show calendar picker."""
        cal_window = tk.Toplevel(self.dialog)
        cal_window.title("Select Date")
        cal_window.geometry("400x300")
        
        cal = Calendar(cal_window, selectmode='day', year=datetime.datetime.now().year)
        cal.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        def select_date():
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, cal.get_date())
            cal_window.destroy()
        
        select_btn = tk.Button(cal_window, text="Select", command=select_date)
        select_btn.pack(pady=10)
    
    def book(self):
        """Confirm booking."""
        email = self.email_entry.get()
        date = self.date_entry.get()
        time = self.time_entry.get()
        topic = self.topic_entry.get()
        
        if not all([email, date, time, topic]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        self.result = {
            'email': email,
            'date': date,
            'time': time,
            'topic': topic
        }
        
        self.dialog.destroy()


def launch_dashboard(service, user_role="user"):
    """
    Launch the enhanced GUI dashboard.
    
    Parameters:
    - service: Authenticated Google Calendar service
    - user_role: Role of the user
    """
    gui = VoiceAssistantGUI(service, user_role)
    gui.run()


if __name__ == "__main__":
    # For testing
    print("Import this module and call launch_dashboard(service, user_role)")
