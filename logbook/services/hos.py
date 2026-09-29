from datetime import datetime, date, timedelta

def calculate_hours(entries):
    totals = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    dummy_date = date.today()
    for entry in entries:
        start = datetime.combine(dummy_date, entry.start_time)
        end = datetime.combine(dummy_date, entry.end_time)
        if end < start:
            # Midnight crossing
            end += timedelta(days=1)
        
        delta = (end - start).total_seconds() / 3600.0
        if delta < 0:
            delta = 0
            
        totals[entry.duty_status] += delta
    return totals

def check_hos_compliance(entries):
    totals = calculate_hours(entries)
    driving = totals[3]
    on_duty_not_driving = totals[4]
    off_duty = totals[1]
    sleeper = totals[2]
    
    total_on_duty = driving + on_duty_not_driving

    violations = []
    if driving > 11.0:
        violations.append(f"11-Hour Driving Limit Exceeded: Logged {round(driving, 2)} hrs")
        
    ordered_entries = sorted(entries, key=lambda x: x.start_time)
    dummy_date = date.today()
    
    driving_since_break = 0.0
    elapsed_window = 0.0
    shift_active = False
    continuous_non_driving = 0.0
    
    for entry in ordered_entries:
        start = datetime.combine(dummy_date, entry.start_time)
        end = datetime.combine(dummy_date, entry.end_time)
        if end < start:
            end += timedelta(days=1)
        dur = (end - start).total_seconds() / 3600.0
        
        if entry.duty_status in (3, 4):
            if not shift_active:
                shift_active = True
                elapsed_window = dur
            else:
                elapsed_window += dur
        else: # OFF DUTY or SLEEPER BERTH
            if shift_active:
                if dur >= 10.0:
                    shift_active = False
                    elapsed_window = 0.0
                else:
                    elapsed_window += dur
        
        if elapsed_window > 14.0:
            if not any(v.startswith("14-Hour Duty Window Exceeded") for v in violations):
                violations.append(f"14-Hour Duty Window Exceeded: Elapsed window reached {round(elapsed_window, 2)} hrs")
                
        # Break rule logic
        if entry.duty_status == 3: # Driving
            continuous_non_driving = 0.0
            if driving_since_break + dur > 8.0:
                if not any(v.startswith("8-Hour Break Limit") for v in violations):
                    violations.append("8-Hour Break Limit: Driving exceeded 8 hours without 30-min break")
            driving_since_break += dur
        else:
            continuous_non_driving += dur
            if continuous_non_driving >= 0.5:
                driving_since_break = 0.0

    return {
        "driving_hours": round(driving, 2),
        "on_duty_hours": round(total_on_duty, 2),
        "off_duty_hours": round(off_duty, 2),
        "sleeper_hours": round(sleeper, 2),
        "driving_remaining": round(max(0, 11.0 - driving), 2),
        "on_duty_remaining": round(max(0, 14.0 - elapsed_window if shift_active else 14.0), 2),
        "is_compliant": len(violations) == 0,
        "violations": violations
    }
