"""
AI-Powered Visual Calendar Analysis

Uses GPT-vision and local visualization to generate insights about calendar patterns:
- Visual descriptions of schedule
- Heatmaps of busiest times
- Availability graphs
- Stress level analysis
- Busiest day identification
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
import statistics

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class TimeSlotIntensity(Enum):
    """Intensity level of a time slot."""
    FREE = "free"           # No events
    LIGHT = "light"         # 1 event
    MODERATE = "moderate"   # 2-3 events
    BUSY = "busy"          # 4-5 events
    PACKED = "packed"      # 6+ events


class StressLevel(Enum):
    """User stress level based on calendar."""
    LOW = "low"             # Relaxed pace
    MODERATE = "moderate"   # Normal pace
    HIGH = "high"          # Busy but manageable
    CRITICAL = "critical"  # Overbooked


@dataclass
class TimeSlotAnalysis:
    """Analysis of a specific time slot."""
    date: str              # YYYY-MM-DD
    hour: int              # 0-23
    event_count: int       # Number of events
    intensity: TimeSlotIntensity
    events: List[str] = field(default_factory=list)
    total_duration: int = 0  # Minutes booked
    capacity_used: float = 0.0  # Percentage of hour used


@dataclass
class DayAnalysis:
    """Analysis of a specific day."""
    date: str              # YYYY-MM-DD
    day_name: str          # Monday, Tuesday, etc.
    event_count: int
    total_booked: int      # Minutes
    total_capacity: int    # 24 * 60 = 1440 minutes
    capacity_percentage: float
    intensity: TimeSlotIntensity
    stress_level: StressLevel
    busiest_hour: int      # Hour with most events (0-23)
    free_slots: List[Tuple[int, int]] = field(default_factory=list)  # (start_hour, end_hour)
    description: str = ""


@dataclass
class WeekAnalysis:
    """Analysis of a week."""
    week_number: int
    start_date: str
    end_date: str
    days: List[DayAnalysis] = field(default_factory=list)
    average_daily_load: float = 0.0
    busiest_day: Optional[DayAnalysis] = None
    freest_day: Optional[DayAnalysis] = None
    total_free_hours: float = 0.0
    recommended_breaks: List[str] = field(default_factory=list)


@dataclass
class MonthAnalysis:
    """Analysis of a full month."""
    month: int              # 1-12
    year: int
    weeks: List[WeekAnalysis] = field(default_factory=list)
    average_daily_load: float = 0.0
    busiest_day: Optional[DayAnalysis] = None
    freest_day: Optional[DayAnalysis] = None
    stress_trend: str = ""  # Increasing, stable, decreasing
    overall_stress: StressLevel = StressLevel.MODERATE


# ============================================================================
# Heatmap Generation
# ============================================================================

class CalendarHeatmap:
    """Generate text-based calendar heatmaps."""
    
    # Unicode intensity characters (darker = busier)
    INTENSITY_CHARS = {
        TimeSlotIntensity.FREE: "░",      # Light (empty)
        TimeSlotIntensity.LIGHT: "▒",     # Light (1 event)
        TimeSlotIntensity.MODERATE: "▓",  # Medium (2-3 events)
        TimeSlotIntensity.BUSY: "█",      # Dark (4-5 events)
        TimeSlotIntensity.PACKED: "██"    # Very dark (6+ events)
    }
    
    @staticmethod
    def generate_weekly_heatmap(days: List[DayAnalysis]) -> str:
        """Generate ASCII heatmap for a week."""
        heatmap = "WEEKLY HEATMAP\n"
        heatmap += "=" * 70 + "\n"
        heatmap += "Hour  Mon  Tue  Wed  Thu  Fri  Sat  Sun\n"
        heatmap += "-" * 70 + "\n"
        
        # For each hour of the day
        for hour in range(24):
            heatmap += f"{hour:02d}:00 "
            
            # For each day
            for day in days:
                # Find events in this hour
                events_in_hour = sum(
                    1 for ts in day.__dict__.get('time_slots', [])
                    if ts.hour == hour
                )
                
                # Determine intensity
                if events_in_hour == 0:
                    intensity = TimeSlotIntensity.FREE
                elif events_in_hour == 1:
                    intensity = TimeSlotIntensity.LIGHT
                elif events_in_hour <= 3:
                    intensity = TimeSlotIntensity.MODERATE
                elif events_in_hour <= 5:
                    intensity = TimeSlotIntensity.BUSY
                else:
                    intensity = TimeSlotIntensity.PACKED
                
                char = CalendarHeatmap.INTENSITY_CHARS[intensity]
                heatmap += f"{char:>4} "
            
            heatmap += "\n"
        
        heatmap += "-" * 70 + "\n"
        heatmap += "Legend: ░=Free  ▒=Light  ▓=Moderate  █=Busy  ██=Packed\n"
        
        return heatmap
    
    @staticmethod
    def generate_monthly_heatmap(weeks: List[WeekAnalysis]) -> str:
        """Generate ASCII heatmap for a month."""
        heatmap = "MONTHLY HEATMAP (Daily Load)\n"
        heatmap += "=" * 50 + "\n"
        
        for week in weeks:
            heatmap += f"Week {week.week_number}: "
            for day in week.days:
                # Map capacity to intensity
                if day.capacity_percentage < 25:
                    char = "░"
                elif day.capacity_percentage < 50:
                    char = "▒"
                elif day.capacity_percentage < 75:
                    char = "▓"
                elif day.capacity_percentage < 90:
                    char = "█"
                else:
                    char = "██"
                
                heatmap += char
            heatmap += "\n"
        
        heatmap += "-" * 50 + "\n"
        heatmap += "0-25%: ░  25-50%: ▒  50-75%: ▓  75-90%: █  90%+: ██\n"
        
        return heatmap


# ============================================================================
# Visual Calendar Analysis Engine
# ============================================================================

class VisualCalendarAnalyzer:
    """Analyzes calendar and generates visual insights."""
    
    def __init__(self, use_gpt: bool = True):
        self.use_gpt = use_gpt and OPENAI_AVAILABLE
    
    def analyze_day(self, events: List[Dict], date: str) -> DayAnalysis:
        """Analyze a single day."""
        from datetime import datetime
        
        day_obj = datetime.strptime(date, '%Y-%m-%d')
        day_name = day_obj.strftime('%A')
        
        # Calculate metrics
        event_count = len(events)
        total_booked = sum(event.get('duration_minutes', 60) for event in events)
        total_capacity = 24 * 60  # 1440 minutes in a day
        capacity_percentage = (total_booked / total_capacity) * 100
        
        # Determine intensity
        if event_count == 0:
            intensity = TimeSlotIntensity.FREE
        elif event_count == 1:
            intensity = TimeSlotIntensity.LIGHT
        elif event_count <= 3:
            intensity = TimeSlotIntensity.MODERATE
        elif event_count <= 5:
            intensity = TimeSlotIntensity.BUSY
        else:
            intensity = TimeSlotIntensity.PACKED
        
        # Determine stress
        if capacity_percentage < 30:
            stress = StressLevel.LOW
        elif capacity_percentage < 60:
            stress = StressLevel.MODERATE
        elif capacity_percentage < 85:
            stress = StressLevel.HIGH
        else:
            stress = StressLevel.CRITICAL
        
        # Find busiest hour
        busiest_hour = self._find_busiest_hour(events)
        
        # Find free slots
        free_slots = self._find_free_slots(events)
        
        # Generate description
        description = self._describe_day(
            day_name, event_count, capacity_percentage, stress
        )
        
        return DayAnalysis(
            date=date,
            day_name=day_name,
            event_count=event_count,
            total_booked=total_booked,
            total_capacity=total_capacity,
            capacity_percentage=capacity_percentage,
            intensity=intensity,
            stress_level=stress,
            busiest_hour=busiest_hour,
            free_slots=free_slots,
            description=description
        )
    
    def analyze_week(self, days_data: List[Tuple[str, List[Dict]]]) -> WeekAnalysis:
        """Analyze a week of days."""
        days = [self.analyze_day(events, date) for date, events in days_data]
        
        # Calculate week metrics
        avg_load = statistics.mean(d.capacity_percentage for d in days)
        busiest = max(days, key=lambda d: d.capacity_percentage)
        freest = min(days, key=lambda d: d.capacity_percentage)
        total_free = sum(
            (d.total_capacity - d.total_booked) / 60 
            for d in days
        )
        
        week_num = datetime.strptime(days[0].date, '%Y-%m-%d').isocalendar()[1]
        
        return WeekAnalysis(
            week_number=week_num,
            start_date=days[0].date,
            end_date=days[-1].date,
            days=days,
            average_daily_load=avg_load,
            busiest_day=busiest,
            freest_day=freest,
            total_free_hours=total_free
        )
    
    def analyze_month(self, weeks_data: List[WeekAnalysis]) -> MonthAnalysis:
        """Analyze a month of weeks."""
        if not weeks_data:
            return MonthAnalysis(month=1, year=2024)
        
        # Get month/year from first week
        first_date = datetime.strptime(weeks_data[0].start_date, '%Y-%m-%d')
        month = first_date.month
        year = first_date.year
        
        # Calculate metrics
        avg_load = statistics.mean(w.average_daily_load for w in weeks_data)
        
        # Find busiest and freest days
        all_days = []
        for week in weeks_data:
            all_days.extend(week.days)
        
        busiest_day = max(all_days, key=lambda d: d.capacity_percentage)
        freest_day = min(all_days, key=lambda d: d.capacity_percentage)
        
        # Determine stress trend
        week_loads = [w.average_daily_load for w in weeks_data]
        if len(week_loads) >= 2:
            if week_loads[-1] > week_loads[0]:
                trend = "increasing"
            elif week_loads[-1] < week_loads[0]:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Determine overall stress
        if avg_load < 30:
            stress = StressLevel.LOW
        elif avg_load < 60:
            stress = StressLevel.MODERATE
        elif avg_load < 85:
            stress = StressLevel.HIGH
        else:
            stress = StressLevel.CRITICAL
        
        return MonthAnalysis(
            month=month,
            year=year,
            weeks=weeks_data,
            average_daily_load=avg_load,
            busiest_day=busiest_day,
            freest_day=freest_day,
            stress_trend=trend,
            overall_stress=stress
        )
    
    def _find_busiest_hour(self, events: List[Dict]) -> int:
        """Find the hour with most events."""
        if not events:
            return 0
        
        hours = {}
        for event in events:
            start = event.get('start', '')
            if start:
                try:
                    hour = int(start.split(':')[0])
                    hours[hour] = hours.get(hour, 0) + 1
                except:
                    pass
        
        return max(hours, key=hours.get) if hours else 0
    
    def _find_free_slots(self, events: List[Dict], 
                        min_duration: int = 60) -> List[Tuple[int, int]]:
        """Find free time slots."""
        # Get all booked hours
        booked_hours = set()
        for event in events:
            start = event.get('start', '')
            duration = event.get('duration_minutes', 60)
            if start:
                try:
                    start_hour = int(start.split(':')[0])
                    for i in range(duration // 60):
                        booked_hours.add(start_hour + i)
                except:
                    pass
        
        # Find free slots
        free_slots = []
        current_slot_start = None
        
        for hour in range(24):
            if hour not in booked_hours:
                if current_slot_start is None:
                    current_slot_start = hour
            else:
                if current_slot_start is not None:
                    duration = (hour - current_slot_start) * 60
                    if duration >= min_duration:
                        free_slots.append((current_slot_start, hour))
                    current_slot_start = None
        
        # Handle final slot
        if current_slot_start is not None:
            duration = (24 - current_slot_start) * 60
            if duration >= min_duration:
                free_slots.append((current_slot_start, 24))
        
        return free_slots
    
    def _describe_day(self, day_name: str, event_count: int, 
                     capacity: float, stress: StressLevel) -> str:
        """Generate natural description of day."""
        if event_count == 0:
            return f"{day_name}: Wide open. Perfect for deep work or planning."
        elif event_count == 1:
            return f"{day_name}: Light schedule with one event. Plenty of buffer time."
        elif event_count <= 3:
            return f"{day_name}: Moderate day with {event_count} events. Manageable pace."
        elif event_count <= 5:
            return f"{day_name}: Busy day with {event_count} events. Time to stay focused."
        else:
            return f"{day_name}: Packed day with {event_count} events. Back-to-back schedule."
    
    def generate_visual_description(self, analysis: Any) -> str:
        """Generate comprehensive visual description using GPT."""
        if not self.use_gpt:
            return self._generate_description_rules(analysis)
        
        return self._generate_description_gpt(analysis)
    
    def _generate_description_gpt(self, analysis: Any) -> str:
        """Generate description using GPT."""
        try:
            if isinstance(analysis, DayAnalysis):
                prompt = f"""Describe this calendar day in vivid, visual terms (2-3 sentences):
                
Day: {analysis.day_name}, {analysis.date}
Events: {analysis.event_count}
Calendar utilization: {analysis.capacity_percentage:.0f}%
Stress level: {analysis.stress_level.value}
Description: {analysis.description}

Be specific, use visual metaphors, mention busy vs free times."""
            
            elif isinstance(analysis, WeekAnalysis):
                busiest = analysis.busiest_day.day_name if analysis.busiest_day else "Unknown"
                freest = analysis.freest_day.day_name if analysis.freest_day else "Unknown"
                prompt = f"""Describe this calendar week visually (3-4 sentences):

Week {analysis.week_number}: {analysis.start_date} to {analysis.end_date}
Average daily load: {analysis.average_daily_load:.0f}%
Busiest day: {busiest}
Freest day: {freest}
Total free hours: {analysis.total_free_hours:.1f}

Paint a picture of the week's rhythm. Is it intense? Varied? Balanced?"""
            
            elif isinstance(analysis, MonthAnalysis):
                prompt = f"""Describe this month's calendar pattern visually (4-5 sentences):

Month: {analysis.month}/{analysis.year}
Average daily utilization: {analysis.average_daily_load:.0f}%
Stress level: {analysis.overall_stress.value}
Stress trend: {analysis.stress_trend}
Busiest day: {analysis.busiest_day.day_name if analysis.busiest_day else 'Unknown'}

Describe the month's overall rhythm, patterns, and intensity."""
            
            else:
                return "Unable to describe analysis."
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            return response['choices'][0]['message']['content'].strip()
        
        except Exception as e:
            print(f"[WARN] GPT description failed: {e}")
            return self._generate_description_rules(analysis)
    
    def _generate_description_rules(self, analysis: Any) -> str:
        """Generate description using rules."""
        if isinstance(analysis, DayAnalysis):
            return analysis.description
        
        elif isinstance(analysis, WeekAnalysis):
            intensity = "high" if analysis.average_daily_load > 70 else "moderate"
            return (f"Week {analysis.week_number} has {intensity} intensity. "
                   f"{analysis.busiest_day.day_name if analysis.busiest_day else 'A day'} "
                   f"is the busiest. You have approximately "
                   f"{analysis.total_free_hours:.1f} free hours to work with.")
        
        elif isinstance(analysis, MonthAnalysis):
            return (f"This month averages {analysis.average_daily_load:.0f}% calendar "
                   f"utilization with a {analysis.stress_trend} stress trend. "
                   f"{analysis.busiest_day.day_name if analysis.busiest_day else 'Peak days'} "
                   f"are your busiest.")
        
        return "Calendar analysis available."
    
    def get_availability_score(self, analysis: DayAnalysis) -> float:
        """Get 0-100 availability score (100 = completely free)."""
        return 100 - analysis.capacity_percentage
    
    def get_stress_recommendations(self, analysis: MonthAnalysis) -> List[str]:
        """Get recommendations based on stress level."""
        recommendations = []
        
        if analysis.overall_stress == StressLevel.CRITICAL:
            recommendations.extend([
                "Block at least 2 hours daily for focused work",
                "Consider deferring or delegating tasks",
                "Schedule recovery time this weekend",
                "Negotiate deadlines with stakeholders"
            ])
        elif analysis.overall_stress == StressLevel.HIGH:
            recommendations.extend([
                "Add 15-minute buffers between meetings",
                "Block 1.5 hours for deep work daily",
                "Schedule short breaks every 2 hours",
                "Review which meetings are essential"
            ])
        elif analysis.overall_stress == StressLevel.MODERATE:
            recommendations.extend([
                "Maintain current pace",
                "Schedule 1 hour of focus time daily",
                "Ensure 30-minute lunch break",
                "Plan one afternoon off this week"
            ])
        else:  # LOW
            recommendations.extend([
                "You have plenty of capacity",
                "Ideal time for strategic planning",
                "Consider scheduling time for professional development",
                "Use free time for relationship building"
            ])
        
        return recommendations


# ============================================================================
# Quick Helpers
# ============================================================================

def quick_day_analysis(events: List[Dict], date: str) -> str:
    """Quick analysis of a day."""
    analyzer = VisualCalendarAnalyzer(use_gpt=False)
    analysis = analyzer.analyze_day(events, date)
    return analyzer.generate_visual_description(analysis)


def quick_stress_check(month_analysis: MonthAnalysis) -> Dict[str, Any]:
    """Quick stress assessment."""
    analyzer = VisualCalendarAnalyzer(use_gpt=False)
    return {
        'stress_level': month_analysis.overall_stress.value,
        'utilization': f"{month_analysis.average_daily_load:.0f}%",
        'trend': month_analysis.stress_trend,
        'recommendations': analyzer.get_stress_recommendations(month_analysis)
    }
