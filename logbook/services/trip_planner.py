from datetime import datetime, timedelta

def generate_schedule(legs, start_time, current_cycle_hours):
    # Constants
    MAX_DRIVING = 11.0
    MAX_DUTY = 14.0
    BREAK_AFTER = 8.0
    BREAK_DUR = 0.5
    REST_DUR = 10.0
    CYCLE_LIMIT = 70.0
    FUEL_INTERVAL = 1000.0
    PICKUP_DUR = 1.0
    DROPOFF_DUR = 1.0
    
    schedule = []
    current_time = start_time
    
    def add_segment(status, dur_hrs, location, reason, miles=0, stop_type=None):
        nonlocal current_time
        seg = {
            "status": status,
            "start": current_time.isoformat(),
            "end": (current_time + timedelta(hours=dur_hrs)).isoformat(),
            "location": location,
            "miles": miles,
            "reason": reason,
            "duration": dur_hrs
        }
        if stop_type:
            seg["stop_type"] = stop_type
        schedule.append(seg)
        current_time += timedelta(hours=dur_hrs)

    # State tracking
    driving_today = 0.0
    duty_today = 0.0
    driving_since_break = 0.0
    cycle_used = current_cycle_hours
    miles_since_fuel = 0.0
    
    for leg in legs:
        remaining_drive_hours = leg["duration_hours"]
        remaining_miles = leg["distance_miles"]
        avg_speed = remaining_miles / remaining_drive_hours if remaining_drive_hours > 0 else 60.0
        
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
            hours_to_fuel = miles_to_fuel / avg_speed if avg_speed > 0 else float('inf')
            
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
                # Ensure we have duty/cycle for fuel
                while MAX_DUTY - duty_today < fuel_dur or CYCLE_LIMIT - cycle_used < fuel_dur:
                    if cycle_used >= CYCLE_LIMIT:
                        add_segment("OFF DUTY", 34.0, "Rest Stop", "34-Hour Restart", stop_type="REST")
                        cycle_used = 0
                        driving_today = 0
                        duty_today = 0
                        driving_since_break = 0
                    else:
                        add_segment("SLEEPER BERTH", REST_DUR, "Rest Stop", "10-Hour Rest", stop_type="REST")
                        driving_today = 0
                        duty_today = 0
                        driving_since_break = 0
                        
                add_segment("ON DUTY", fuel_dur, "En Route", "Fuel Stop", stop_type="FUEL")
                duty_today += fuel_dur
                cycle_used += fuel_dur
                miles_since_fuel = 0
                driving_since_break = 0 # 30 min on-duty counts as break
                continue
                
            if max_possible_drive <= 0:
                # Must rest or restart
                if cycle_used >= CYCLE_LIMIT:
                    add_segment("OFF DUTY", 34.0, "Rest Stop", "34-Hour Restart", stop_type="REST")
                    cycle_used = 0
                    driving_today = 0
                    duty_today = 0
                    driving_since_break = 0
                else:
                    add_segment("SLEEPER BERTH", REST_DUR, "Rest Stop", "10-Hour Rest", stop_type="REST")
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
                add_segment("OFF DUTY", BREAK_DUR, "Rest Stop", "30-Minute Break", stop_type="BREAK")
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

        # After each leg, do the required service
        if leg["name"] == "current_to_pickup":
            while MAX_DUTY - duty_today < PICKUP_DUR or CYCLE_LIMIT - cycle_used < PICKUP_DUR:
                if cycle_used >= CYCLE_LIMIT:
                    add_segment("OFF DUTY", 34.0, "Rest Stop", "34-Hour Restart", stop_type="REST")
                    cycle_used = 0
                    driving_today = 0
                    duty_today = 0
                    driving_since_break = 0
                else:
                    add_segment("SLEEPER BERTH", REST_DUR, "Rest Stop", "10-Hour Rest", stop_type="REST")
                    driving_today = 0
                    duty_today = 0
                    driving_since_break = 0
                    
            add_segment("ON DUTY", PICKUP_DUR, leg["end_location"], "Pickup", stop_type="PICKUP")
            duty_today += PICKUP_DUR
            cycle_used += PICKUP_DUR
            driving_since_break = 0 # Pickup takes 1 hr (>= 30m), resets break
            
        elif leg["name"] == "pickup_to_dropoff":
            while MAX_DUTY - duty_today < DROPOFF_DUR or CYCLE_LIMIT - cycle_used < DROPOFF_DUR:
                if cycle_used >= CYCLE_LIMIT:
                    add_segment("OFF DUTY", 34.0, "Rest Stop", "34-Hour Restart", stop_type="REST")
                    cycle_used = 0
                    driving_today = 0
                    duty_today = 0
                    driving_since_break = 0
                else:
                    add_segment("SLEEPER BERTH", REST_DUR, "Rest Stop", "10-Hour Rest", stop_type="REST")
                    driving_today = 0
                    duty_today = 0
                    driving_since_break = 0

            add_segment("ON DUTY", DROPOFF_DUR, leg["end_location"], "Dropoff", stop_type="DROPOFF")
            duty_today += DROPOFF_DUR
            cycle_used += DROPOFF_DUR
            driving_since_break = 0

    return schedule

def split_days(schedule):
    if not schedule:
        return []
        
    start_dt = datetime.fromisoformat(schedule[0]["start"])
    current_day = start_dt.date()
    
    days = []
    current_day_segments = []
    
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
            day_end = datetime.combine(current_day + timedelta(days=1), datetime.min.time())
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
            day_end = datetime.combine(current_day + timedelta(days=1), datetime.min.time())
            dur1 = (day_end - s_start).total_seconds() / 3600.0
            dur2 = (s_end - day_end).total_seconds() / 3600.0
            ratio = dur1 / (dur1 + dur2) if (dur1+dur2)>0 else 0
            
            part1 = {
                "status": seg["status"],
                "start": s_start.isoformat(),
                "end": day_end.isoformat(),
                "location": seg["location"],
                "miles": seg["miles"] * ratio,
                "reason": seg["reason"],
                "duration": dur1
            }
            if "stop_type" in seg: part1["stop_type"] = seg["stop_type"]
            current_day_segments.append(part1)
            days.append({"date": current_day.isoformat(), "segments": current_day_segments})
            
            current_day += timedelta(days=1)
            part2 = {
                "status": seg["status"],
                "start": day_end.isoformat(),
                "end": s_end.isoformat(),
                "location": seg["location"],
                "miles": seg["miles"] * (1 - ratio),
                "reason": seg["reason"],
                "duration": dur2
            }
            if "stop_type" in seg: part2["stop_type"] = seg["stop_type"]
            current_day_segments = [part2]
        else:
            current_day_segments.append(seg)
            
    if current_day_segments:
        s_end = datetime.fromisoformat(current_day_segments[-1]["end"])
        day_end = datetime.combine(current_day + timedelta(days=1), datetime.min.time())
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
