from datetime import datetime, timedelta
import math

def generate_schedule(distance_miles, duration_hours, start_time, current_cycle_hours):
    # Constants
    MAX_DRIVING = 11.0
    MAX_DUTY = 14.0
    BREAK_AFTER = 8.0
    BREAK_DUR = 0.5
    REST_DUR = 10.0
    CYCLE_LIMIT = 70.0
    FUEL_INTERVAL = 900.0
    PICKUP_DUR = 1.0
    DROPOFF_DUR = 1.0
    
    schedule = []
    
    def add_segment(status, dur_hrs, location, reason, miles=0):
        nonlocal current_time
        schedule.append({
            "status": status,
            "start": current_time.isoformat(),
            "end": (current_time + timedelta(hours=dur_hrs)).isoformat(),
            "location": location,
            "miles": miles,
            "reason": reason,
            "duration": dur_hrs
        })
        current_time += timedelta(hours=dur_hrs)

    current_time = start_time
    remaining_drive_hours = duration_hours
    remaining_miles = distance_miles
    avg_speed = remaining_miles / remaining_drive_hours if remaining_drive_hours > 0 else 60.0
    miles_since_fuel = 0.0
    
    # State tracking
    driving_today = 0.0
    duty_today = PICKUP_DUR
    driving_since_break = 0.0
    cycle_used = current_cycle_hours + PICKUP_DUR

    # Pickup
    add_segment("ON DUTY", PICKUP_DUR, "Origin", "Pickup")
    
    while remaining_drive_hours > 0:
        # Determine constraints
        max_possible_drive = min(
            remaining_drive_hours,
            MAX_DRIVING - driving_today,
            MAX_DUTY - duty_today,
            BREAK_AFTER - driving_since_break,
            CYCLE_LIMIT - cycle_used
        )
        
        # Check Fuel Constraint
        miles_to_fuel = FUEL_INTERVAL - miles_since_fuel
        hours_to_fuel = miles_to_fuel / avg_speed
        
        if hours_to_fuel <= max_possible_drive:
            # Need to fuel first
            drive_chunk = max(0, hours_to_fuel)
            if drive_chunk > 0:
                miles_chunk = drive_chunk * avg_speed
                add_segment("DRIVING", drive_chunk, "En Route", "Driving", miles_chunk)
                driving_today += drive_chunk
                duty_today += drive_chunk
                driving_since_break += drive_chunk
                cycle_used += drive_chunk
                remaining_drive_hours -= drive_chunk
                remaining_miles -= miles_chunk
                miles_since_fuel += miles_chunk
                
            # Fuel
            fuel_dur = 0.5
            add_segment("ON DUTY", fuel_dur, "En Route", "Fuel Stop")
            duty_today += fuel_dur
            cycle_used += fuel_dur
            miles_since_fuel = 0
            driving_since_break = 0 # 30 min on-duty counts as break
            continue
            
        if max_possible_drive <= 0:
            # Must rest or restart
            if cycle_used >= CYCLE_LIMIT:
                add_segment("OFF DUTY", 34.0, "Rest Stop", "34-Hour Restart")
                cycle_used = 0
                driving_today = 0
                duty_today = 0
                driving_since_break = 0
            else:
                add_segment("SLEEPER BERTH", REST_DUR, "Rest Stop", "10-Hour Rest")
                driving_today = 0
                duty_today = 0
                driving_since_break = 0
            continue
            
        if max_possible_drive == (BREAK_AFTER - driving_since_break):
            # Hit 8 hour break rule
            drive_chunk = max_possible_drive
            miles_chunk = drive_chunk * avg_speed
            add_segment("DRIVING", drive_chunk, "En Route", "Driving", miles_chunk)
            driving_today += drive_chunk
            duty_today += drive_chunk
            driving_since_break += drive_chunk
            cycle_used += drive_chunk
            remaining_drive_hours -= drive_chunk
            remaining_miles -= miles_chunk
            miles_since_fuel += miles_chunk
            
            # Take break
            add_segment("OFF DUTY", BREAK_DUR, "Rest Stop", "30-Minute Break")
            driving_since_break = 0
            continue
            
        # Normal driving chunk
        drive_chunk = max_possible_drive
        miles_chunk = drive_chunk * avg_speed
        add_segment("DRIVING", drive_chunk, "En Route", "Driving", miles_chunk)
        driving_today += drive_chunk
        duty_today += drive_chunk
        driving_since_break += drive_chunk
        cycle_used += drive_chunk
        remaining_drive_hours -= drive_chunk
        remaining_miles -= miles_chunk
        miles_since_fuel += miles_chunk

    # Dropoff
    add_segment("ON DUTY", DROPOFF_DUR, "Destination", "Dropoff")
    
    return schedule

def split_days(schedule):
    # Process schedule into EXACT 24 hour days, splitting overnight segments
    if not schedule:
        return []
        
    start_dt = datetime.fromisoformat(schedule[0]["start"])
    current_day = start_dt.date()
    
    days = []
    current_day_segments = []
    
    # Pad start of first day
    midnight = datetime.combine(current_day, datetime.min.time())
    if start_dt > midnight:
        gap = (start_dt - midnight).total_seconds() / 3600.0
        current_day_segments.append({
            "status": "OFF DUTY",
            "start": midnight.isoformat(),
            "end": start_dt.isoformat(),
            "location": "Origin",
            "miles": 0,
            "reason": "Off Duty",
            "duration": gap
        })
        
    for seg in schedule:
        s_start = datetime.fromisoformat(seg["start"])
        s_end = datetime.fromisoformat(seg["end"])
        
        while s_start.date() > current_day:
            # We skipped a whole day? Pad current day to end
            day_end = datetime.combine(current_day, datetime.max.time()) + timedelta(seconds=1)
            last_dt = datetime.fromisoformat(current_day_segments[-1]["end"]) if current_day_segments else datetime.combine(current_day, datetime.min.time())
            if last_dt < day_end:
                gap = (day_end - last_dt).total_seconds() / 3600.0
                current_day_segments.append({
                    "status": "OFF DUTY",
                    "start": last_dt.isoformat(),
                    "end": day_end.isoformat(),
                    "location": "System",
                    "miles": 0,
                    "reason": "Padding",
                    "duration": gap
                })
            days.append({"date": current_day.isoformat(), "segments": current_day_segments})
            current_day += timedelta(days=1)
            current_day_segments = []
            
        if s_end.date() > current_day:
            # Segment crosses midnight
            day_end = datetime.combine(current_day, datetime.max.time()) + timedelta(seconds=1)
            dur1 = (day_end - s_start).total_seconds() / 3600.0
            dur2 = (s_end - day_end).total_seconds() / 3600.0
            ratio = dur1 / (dur1 + dur2) if (dur1+dur2)>0 else 0
            
            # Add part 1
            current_day_segments.append({
                "status": seg["status"],
                "start": s_start.isoformat(),
                "end": day_end.isoformat(),
                "location": seg["location"],
                "miles": seg["miles"] * ratio,
                "reason": seg["reason"],
                "duration": dur1
            })
            days.append({"date": current_day.isoformat(), "segments": current_day_segments})
            
            # Prepare next day
            current_day += timedelta(days=1)
            current_day_segments = [{
                "status": seg["status"],
                "start": day_end.isoformat(),
                "end": s_end.isoformat(),
                "location": seg["location"],
                "miles": seg["miles"] * (1 - ratio),
                "reason": seg["reason"],
                "duration": dur2
            }]
        else:
            current_day_segments.append(seg)
            
    # Pad end of last day
    if current_day_segments:
        s_end = datetime.fromisoformat(current_day_segments[-1]["end"])
        day_end = datetime.combine(current_day, datetime.max.time()) + timedelta(seconds=1)
        if s_end < day_end:
            gap = (day_end - s_end).total_seconds() / 3600.0
            current_day_segments.append({
                "status": "OFF DUTY",
                "start": s_end.isoformat(),
                "end": day_end.isoformat(),
                "location": "Destination",
                "miles": 0,
                "reason": "Off Duty",
                "duration": gap
            })
        days.append({"date": current_day.isoformat(), "segments": current_day_segments})
        
    return days
