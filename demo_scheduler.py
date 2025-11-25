"""
Smart Scheduler & Agenda Summary Demo

Run this script to see:
- AI event understanding
- Smart scheduling
- Agenda summaries
- AI pattern detection & predictions
"""

import datetime
from src.nlu import parse_natural_language_event
from src.ai_scheduler import SmartScheduler, SchedulePreferences, TimeSlot, AvailabilityBuilder
from src.agenda_summary import AgendaSummaryService, AgendaEvent
from src.ai_patterns import PatternPredictionService


def demo_nlu_parser():
    """Demonstrate NLU parsing of messy voice commands."""
    print("\n" + "="*70)
    print("DEMO 1: Natural Language Understanding (NLU) Parser")
    print("="*70)
    
    examples = [
        "Yo, remind me to submit that assignment the day before it's due.",
        "Set up something with Vusi sometime Friday morning — nothing too early.",
        "Plan a 1-hour revision session each day this week."
    ]
    
    for text in examples:
        print(f"\n📝 Input: {text}")
        parsed = parse_natural_language_event(text)
        
        print(f"   ✓ Title: {parsed.get('title')}")
        if parsed.get('duration'):
            print(f"   ✓ Duration: {parsed['duration']}")
        if parsed.get('recurrence'):
            print(f"   ✓ Recurrence: {parsed['recurrence']}")
        if parsed.get('time_window'):
            tw = parsed['time_window']
            print(f"   ✓ Time Window: {tw['start'].strftime('%H:%M')} - {tw['end'].strftime('%H:%M')}")
        if parsed.get('relative'):
            print(f"   ✓ Relative: {parsed['relative']}")


def demo_availability_builder():
    """Demonstrate finding available time slots."""
    print("\n" + "="*70)
    print("DEMO 2: Availability Builder (Find Free Slots)")
    print("="*70)
    
    # Simulate some busy events (Google Calendar format)
    events = [
        {
            'start': {'dateTime': '2025-11-25T09:00:00'},
            'end': {'dateTime': '2025-11-25T10:30:00'}
        },
        {
            'start': {'dateTime': '2025-11-25T11:00:00'},
            'end': {'dateTime': '2025-11-25T12:00:00'}
        },
        {
            'start': {'dateTime': '2025-11-25T14:00:00'},
            'end': {'dateTime': '2025-11-25T15:30:00'}
        }
    ]
    
    # Define preferences
    prefs = SchedulePreferences(
        avoid_times=['morning'],
        work_hours_only=True,
        earliest_hour=9,
        latest_hour=17
    )
    
    builder = AvailabilityBuilder(prefs)
    
    start = datetime.datetime(2025, 11, 25, 8, 0)
    end = datetime.datetime(2025, 11, 25, 18, 0)
    
    print(f"\n📅 Searching for 2-hour slots on Tuesday, Nov 25, 2025")
    print(f"   Busy events: 9:00-10:30, 11:00-12:00, 14:00-15:30")
    print(f"   Preferences: No mornings (afternoon only), Work hours 9-5")
    
    slots = builder.build_availability_blocks(events, start, end, duration_minutes=120)
    
    print(f"\n✓ Found {len(slots)} available 2-hour slots (avoiding mornings):")
    for i, slot in enumerate(slots, 1):
        print(f"   {i}. {slot.start.strftime('%I:%M %p')} - {slot.end.strftime('%I:%M %p')} ({slot.duration_minutes} min)")


def demo_scheduler_without_calendar():
    """Demonstrate scheduler with simulated availability."""
    print("\n" + "="*70)
    print("DEMO 3: Smart Scheduler (Simulated - No Google Calendar)")
    print("="*70)
    
    prefs = SchedulePreferences(
        avoid_times=['morning', 'weekend'],
        preferred_times=['afternoon'],
        work_hours_only=True
    )
    
    # Create scheduler without Google creds (uses fallback)
    scheduler = SmartScheduler(preferences=prefs)
    
    print("\n🤖 Finding best time for: '2-hour team meeting'")
    print("   Duration: 2 hours")
    print("   Search window: Next 7 days")
    print("   Preferences: Afternoon, weekdays only, 9-5")
    
    results = scheduler.find_best_times(
        event_description="2-hour team meeting",
        duration_minutes=120,
        search_window_days=7,
        top_n=3
    )
    
    print(f"\n✓ Status: {results['status']}")
    print(f"✓ Total available slots found: {results.get('total_available_slots', 'N/A')}")
    
    if results.get('recommendations'):
        print(f"✓ Top {len(results['recommendations'])} recommendations:")
        for i, rec in enumerate(results['recommendations'][:3], 1):
            if isinstance(rec, dict):
                print(f"   {i}. {rec.get('start', 'N/A')[:10]} {rec.get('start', 'N/A')[11:16]}")
                if rec.get('reason'):
                    print(f"      Reason: {rec['reason']}")


def demo_voice_command_parsing():
    """Demonstrate voice command parsing."""
    print("\n" + "="*70)
    print("DEMO 4: Voice Command Parsing")
    print("="*70)
    
    from src.voice_handler import VoiceCommandParser
    
    commands = [
        "Find the best time for a 2-hour session next week",
        "Find best time for 1-hour meeting on Friday",
        "What time can we meet for 90 minutes this week?"
    ]
    
    for cmd in commands:
        print(f"\n🎤 Voice input: \"{cmd}\"")
        command_type, params = VoiceCommandParser.parse_command(cmd)
        
        if command_type == 'find-best-time':
            print(f"   ✓ Detected: Find Best Time Request")
            print(f"   ✓ Event: {params.get('event_description')}")
            print(f"   ✓ Duration: {params.get('duration_minutes')} minutes")
            print(f"   ✓ Search Window: {params.get('search_window_days')} days")
        else:
            print(f"   ✓ Detected: {command_type} (not find-best-time)")


def demo_agenda_summary():
    """Demonstrate agenda summary generation."""
    print("\n" + "="*70)
    print("DEMO 5: AI Agenda Summaries")
    print("="*70)
    
    # Create mock calendar events
    today = datetime.datetime.now()
    
    print(f"\n📅 Sample Day: Monday")
    print("   Events:")
    
    day_events = [
        AgendaEvent("Study session", today.replace(hour=10, minute=0), 
                   today.replace(hour=11, minute=0), 60, description="Python course"),
        AgendaEvent("Team meeting", today.replace(hour=15, minute=0),
                   today.replace(hour=16, minute=0), 60, description="Weekly sync"),
    ]
    
    for evt in day_events:
        print(f"   • {evt.title} at {evt.format_time()}")
    
    # Generate summary
    service = AgendaSummaryService(use_gpt=False)
    summary = service.get_today_summary(day_events, use_gpt=False)
    
    print(f"\n   🤖 AI Summary:")
    print(f"   \"{summary}\"")
    
    # Week example
    print(f"\n📅 Sample Week:")
    week_events = []
    for day_offset in range(7):
        day = today + datetime.timedelta(days=day_offset)
        # Vary events per day
        num_events = [0, 2, 4, 1, 3, 0, 1][day_offset]
        for i in range(num_events):
            hour = 9 + (i * 2)
            week_events.append(
                AgendaEvent(
                    f"Event {day_offset*5+i+1}",
                    day.replace(hour=hour, minute=0),
                    day.replace(hour=hour+1, minute=0),
                    60
                )
            )
    
    week_summary = service.get_week_summary(week_events, use_gpt=False)
    
    print(f"\n   🤖 AI Summary:")
    print(f"   \"{week_summary}\"")
    
    # Show metrics
    print(f"\n   📊 Week Metrics:")
    metrics = service.get_summary_with_details(week_events, period='week')
    if metrics.get('metrics'):
        m = metrics['metrics']
        print(f"   • Total events: {m.get('total_events', 0)}")
        print(f"   • Busy hours: {m.get('total_busy_hours', 0):.1f}")
        print(f"   • Days with events: {m.get('days_with_events', 0)}")


def demo_ai_patterns():
    """Demonstrate AI pattern detection and predictions."""
    print("\n📊 Analyzing calendar patterns...")
    
    # Create sample calendar with predictable patterns
    today = datetime.datetime.now()
    events = []
    
    # Pattern 1: Consistent Tuesday mornings (busy pattern)
    for week in range(4):
        tuesday = today + datetime.timedelta(days=(8-today.weekday()) % 7 + 7*week)
        events.extend([
            {
                'title': 'Morning Standup',
                'start_time': tuesday.replace(hour=9, minute=0).isoformat() + 'Z',
                'end_time': tuesday.replace(hour=9, minute=30).isoformat() + 'Z'
            },
            {
                'title': 'Team Sync',
                'start_time': tuesday.replace(hour=10, minute=0).isoformat() + 'Z',
                'end_time': tuesday.replace(hour=11, minute=0).isoformat() + 'Z'
            },
            {
                'title': 'Dev Meeting',
                'start_time': tuesday.replace(hour=11, minute=0).isoformat() + 'Z',
                'end_time': tuesday.replace(hour=12, minute=0).isoformat() + 'Z'
            }
        ])
    
    # Pattern 2: Close events (travel time issue)
    thursday = today + datetime.timedelta(days=(3-today.weekday()) % 7)
    events.extend([
        {
            'title': 'Project Review',
            'start_time': thursday.replace(hour=14, minute=0).isoformat() + 'Z',
            'end_time': thursday.replace(hour=14, minute=30).isoformat() + 'Z'
        },
        {
            'title': 'Client Call',
            'start_time': thursday.replace(hour=14, minute=35).isoformat() + 'Z',
            'end_time': thursday.replace(hour=15, minute=30).isoformat() + 'Z'
        }
    ])
    
    # Pattern 3: Early morning events
    for day in range(5):
        day_date = today + datetime.timedelta(days=day)
        if day_date.weekday() < 5:  # Weekday only
            events.append({
                'title': 'Early Email Review',
                'start_time': day_date.replace(hour=8, minute=0).isoformat() + 'Z',
                'end_time': day_date.replace(hour=8, minute=30).isoformat() + 'Z'
            })
    
    # Analyze patterns
    service = PatternPredictionService(use_gpt=False, min_gap_minutes=15)
    analysis = service.analyze_calendar(events)
    
    print(f"\n   📈 Analysis of {analysis['event_count']} events:\n")
    
    # Show detected patterns
    print("   🔍 Patterns Detected:")
    for i, pattern in enumerate(analysis['patterns'][:3], 1):
        confidence = pattern['confidence']
        print(f"      {i}. {pattern['name']} ({confidence}%)")
        print(f"         {pattern['description']}")
    
    # Show predictions
    print("\n   💡 AI Predictions & Recommendations:")
    for i, pred in enumerate(analysis['predictions'][:3], 1):
        priority = f"[{pred['priority'].upper()}]"
        print(f"      {i}. {priority} {pred['category'].title()}")
        print(f"         Insight: {pred['insight']}")
        print(f"         Recommendation: {pred['recommendation']}")
        print()
    
    # Show summary
    print(f"   📝 Summary: {analysis['summary']}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*10 + "AI SCHEDULER & AGENDA SUMMARIES - DEMO" + " "*20 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        demo_nlu_parser()
        demo_availability_builder()
        demo_scheduler_without_calendar()
        demo_voice_command_parsing()
        demo_agenda_summary()
        
        print("\n" + "="*70)
        print("DEMO 4: AI Pattern Detection & Predictions")
        print("="*70)
        demo_ai_patterns()
        
        print("\n" + "="*70)
        print("✅ All demos completed successfully!")
        print("="*70)
        print("\n📚 Next Steps:")
        print("   1. Set up Google Calendar credentials (.config/credentials.json)")
        print("   2. Set OPENAI_API_KEY environment variable")
        print("   3. Run: pip install -r requirements-voice.txt")
        print("   4. Start web app: python web_app.py")
        print("   5. Try voice commands:")
        print("      - 'What's my day looking like?'")
        print("      - 'Summarize my week'")
        print("      - 'Find the best time for a 2-hour meeting next week'")
        print("\n📖 See SCHEDULER_GUIDE.md and AGENDA_SUMMARY_GUIDE.md\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
