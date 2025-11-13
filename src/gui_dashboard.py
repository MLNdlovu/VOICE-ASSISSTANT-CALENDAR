"""
GUI Dashboard for Voice Assistant Calendar

A simple Tkinter-based dashboard showing the next 7 events with controls
for adding, canceling, and managing calendar bookings via voice or text.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import datetime
import threading
from typing import Optional, Callable, Any
import book
import voice_handler
from voice_handler import VoiceOutput, VoiceCommandParser, get_voice_output


class CalendarDashboard:
    """
    Main GUI dashboard for Voice Assistant Calendar.
    
    Features:
    - Display next 7 events in a table
    - Book events (voice or text input)
    - Cancel events
    - Refresh calendar
    - Voice command recognition and response
    """
    
    def __init__(self, root: tk.Tk, service: Any, username: str = ""):
        """
        Initialize the dashboard.
        
        Parameters:
        - root: Tkinter root window
        - service: Google Calendar API service object
        - username: Current user's username
        """
        self.root = root
        self.service = service
        self.username = username
        self.events = []
        self.voice_output = get_voice_output()
        
        # Window configuration
        self.root.title("🗓️  Voice Assistant Calendar")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        
        # Create UI elements
        self._create_header()
        self._create_controls()
        self._create_events_table()
        self._create_status_bar()
        
        # Initial load
        self.refresh_events()

    def _create_header(self) -> None:
        """Create the header section with title and welcome message."""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=20, pady=15)
        
        title_label = ttk.Label(
            header_frame,
            text="🗓️  Voice Assistant Calendar Dashboard",
            font=("Arial", 18, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        if self.username:
            user_label = ttk.Label(
                header_frame,
                text=f"User: {self.username}",
                font=("Arial", 10)
            )
            user_label.pack(side=tk.RIGHT)

    def _create_controls(self) -> None:
        """Create control buttons and input fields."""
        control_frame = ttk.LabelFrame(self.root, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Button row 1: Main actions
        button_frame1 = ttk.Frame(control_frame)
        button_frame1.pack(fill=tk.X, pady=5)
        
        refresh_btn = ttk.Button(
            button_frame1,
            text="🔄 Refresh Calendar",
            command=self.refresh_events
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        add_event_btn = ttk.Button(
            button_frame1,
            text="➕ Add Event (Text)",
            command=self.add_event_text
        )
        add_event_btn.pack(side=tk.LEFT, padx=5)
        
        add_voice_btn = ttk.Button(
            button_frame1,
            text="🎤 Add Event (Voice)",
            command=self.add_event_voice
        )
        add_voice_btn.pack(side=tk.LEFT, padx=5)
        
        # Button row 2: More actions
        button_frame2 = ttk.Frame(control_frame)
        button_frame2.pack(fill=tk.X, pady=5)
        
        cancel_btn = ttk.Button(
            button_frame1,
            text="❌ Cancel Event",
            command=self.cancel_event
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        settings_btn = ttk.Button(
            button_frame1,
            text="⚙️  Settings",
            command=self.open_settings
        )
        settings_btn.pack(side=tk.LEFT, padx=5)
        
        help_btn = ttk.Button(
            button_frame1,
            text="❓ Help",
            command=self.show_help
        )
        help_btn.pack(side=tk.LEFT, padx=5)

    def _create_events_table(self) -> None:
        """Create the events display table."""
        table_frame = ttk.LabelFrame(self.root, text="Next 7 Events", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview for events
        columns = ("Date", "Time", "Event", "Creator")
        self.tree = ttk.Treeview(table_frame, columns=columns, height=10, show="headings")
        
        # Define column headings and widths
        self.tree.column("Date", width=100, anchor=tk.W)
        self.tree.column("Time", width=80, anchor=tk.CENTER)
        self.tree.column("Event", width=400, anchor=tk.W)
        self.tree.column("Creator", width=250, anchor=tk.W)
        
        self.tree.heading("Date", text="Date")
        self.tree.heading("Time", text="Time")
        self.tree.heading("Event", text="Event Name")
        self.tree.heading("Creator", text="Creator Email")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to select event
        self.tree.bind("<Double-1>", self.on_event_selected)

    def _create_status_bar(self) -> None:
        """Create the status bar at the bottom."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=5)

    def update_status(self, message: str) -> None:
        """Update the status bar message."""
        self.status_label.config(text=message)
        self.root.update()

    def refresh_events(self) -> None:
        """Refresh the events display."""
        self.update_status("Loading events...")
        
        try:
            # Load events from calendar
            self.events = book.load_voice_assistant_calendar()
            
            # Clear current table
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Add events to table
            for event in self.events[:7]:  # Show next 7 events
                if 'start' in event and 'dateTime' in event['start']:
                    start_datetime = event['start']['dateTime']
                    # Parse datetime
                    dt_obj = datetime.datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                    date_str = dt_obj.strftime('%Y-%m-%d')
                    time_str = dt_obj.strftime('%H:%M')
                    summary = event.get('summary', 'No Title')
                    creator = event.get('creator', {}).get('email', 'Unknown')
                    
                    self.tree.insert("", tk.END, values=(date_str, time_str, summary, creator))
            
            self.update_status(f"✅ Loaded {len(self.events)} events")
            
        except Exception as e:
            self.update_status(f"❌ Error loading events: {str(e)}")
            messagebox.showerror("Error", f"Failed to load events: {str(e)}")

    def add_event_text(self) -> None:
        """Open dialog to add event via text input."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Event (Text)")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Date (YYYY-MM-DD):", font=("Arial", 10)).pack(padx=10, pady=5)
        date_entry = ttk.Entry(dialog, width=30)
        date_entry.pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Time (HH:MM):", font=("Arial", 10)).pack(padx=10, pady=5)
        time_entry = ttk.Entry(dialog, width=30)
        time_entry.pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Event Title:", font=("Arial", 10)).pack(padx=10, pady=5)
        title_entry = ttk.Entry(dialog, width=30)
        title_entry.pack(padx=10, pady=5)
        
        def save_event():
            date = date_entry.get()
            time = time_entry.get()
            title = title_entry.get()
            
            if not all([date, time, title]):
                messagebox.showwarning("Input Error", "Please fill in all fields")
                return
            
            try:
                # Format datetime
                start_time = f"{date}T{time}:00+02:00"
                # Book the event
                book.book_as_student(self.service, self.username, start_time, title)
                messagebox.showinfo("Success", "Event added successfully!")
                dialog.destroy()
                self.refresh_events()
                self.voice_output.speak_response(f"Event {title} added successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add event: {str(e)}")
        
        ttk.Button(dialog, text="Save Event", command=save_event).pack(pady=20)

    def add_event_voice(self) -> None:
        """Add event via voice input."""
        self.update_status("🎤 Listening for voice command...")
        
        # Run voice recognition in background thread
        def voice_thread():
            try:
                recognizer = voice_handler.VoiceRecognizer()
                if not recognizer.is_available():
                    self.update_status("❌ Voice input not available")
                    messagebox.showerror("Error", "Voice recognition not available")
                    return
                
                voice_text = recognizer.listen("Say: Book a slot on [date] at [time] for [topic]")
                if voice_text:
                    command, params = VoiceCommandParser.parse_command(voice_text)
                    
                    if command == 'book' and params['date'] and params['time'] and params['summary']:
                        start_time = f"{params['date']}T{params['time']}:00+02:00"
                        book.book_as_student(self.service, self.username, start_time, params['summary'])
                        self.voice_output.speak_response(f"Event {params['summary']} booked successfully!")
                        self.refresh_events()
                    else:
                        self.voice_output.speak_response("Could not parse booking command. Please try again.")
                else:
                    self.update_status("❌ Could not recognize voice")
            except Exception as e:
                self.update_status(f"❌ Error: {str(e)}")
                messagebox.showerror("Error", f"Voice input failed: {str(e)}")
        
        thread = threading.Thread(target=voice_thread, daemon=True)
        thread.start()

    def cancel_event(self) -> None:
        """Cancel selected event."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select an event to cancel")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to cancel this event?"):
            try:
                self.update_status("Canceling event...")
                # Get the selected event
                item = selection[0]
                values = self.tree.item(item)['values']
                date_str = values[0]
                time_str = values[1]
                start_time = f"{date_str}T{time_str}:00+02:00"
                
                book.cancel_booking(self.service, self.username, start_time)
                messagebox.showinfo("Success", "Event canceled successfully!")
                self.refresh_events()
                self.voice_output.speak_response("Event canceled successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to cancel event: {str(e)}")

    def on_event_selected(self, event) -> None:
        """Handle event selection (double-click)."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item)['values']
            messagebox.showinfo("Event Details", f"Date: {values[0]}\nTime: {values[1]}\nEvent: {values[2]}\nCreator: {values[3]}")

    def open_settings(self) -> None:
        """Open settings dialog."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x250")
        
        ttk.Label(settings_window, text="Voice Settings", font=("Arial", 12, "bold")).pack(padx=10, pady=10)
        
        ttk.Label(settings_window, text="Speech Rate (100-200):").pack(padx=10, pady=5)
        rate_scale = ttk.Scale(settings_window, from_=100, to=200, orient=tk.HORIZONTAL)
        rate_scale.set(150)
        rate_scale.pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(settings_window, text="Volume (0.0-1.0):").pack(padx=10, pady=5)
        volume_scale = ttk.Scale(settings_window, from_=0.0, to=1.0, orient=tk.HORIZONTAL)
        volume_scale.set(0.9)
        volume_scale.pack(padx=10, pady=5, fill=tk.X)
        
        def apply_settings():
            self.voice_output.set_rate(int(rate_scale.get()))
            self.voice_output.set_volume(volume_scale.get())
            self.voice_output.speak_response("Settings updated!")
            settings_window.destroy()
        
        ttk.Button(settings_window, text="Apply", command=apply_settings).pack(pady=20)

    def show_help(self) -> None:
        """Show help dialog."""
        help_text = """
📖 VOICE ASSISTANT CALENDAR HELP

VOICE COMMANDS:
🎤 "Book a slot on [date] at [time] for [topic]"
   Example: "Book a slot on 2024-03-15 at 10:00 for Python help"

🎤 "Show me upcoming events"
   Displays all upcoming events

🎤 "Cancel my booking on [date] at [time]"
   Cancels an existing booking

🎤 "Show code clinics calendar"
   Displays the shared calendar

SUPPORTED DATE FORMATS:
• Absolute: 2024-03-15, 03/15/2024
• Relative: "today", "tomorrow", "next Monday"
• Duration: "in 3 days", "in 2 weeks"

TIME FORMAT:
• 24-hour: 14:30, 10:00
• 12-hour: 2:30 pm, 10:00 am

BUTTONS:
• 🔄 Refresh Calendar: Update event list
• ➕ Add Event (Text): Manual event entry
• 🎤 Add Event (Voice): Voice-based booking
• ❌ Cancel Event: Remove selected event
• ⚙️  Settings: Adjust voice preferences
        """
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=("Arial", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)


def launch_dashboard(service: Any, username: str = "") -> None:
    """
    Launch the calendar dashboard.
    
    Parameters:
    - service: Google Calendar API service object
    - username: Current user's username
    """
    root = tk.Tk()
    dashboard = CalendarDashboard(root, service, username)
    root.mainloop()


if __name__ == "__main__":
    print("GUI Dashboard Module")
    print("This module is meant to be imported and used with the main application.")
    print("To launch the dashboard, use: gui_dashboard.launch_dashboard(service, username)")
