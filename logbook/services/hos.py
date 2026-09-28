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
    if total_on_duty > 14.0:
        violations.append(f"14-Hour Duty Window Exceeded: Logged {round(total_on_duty, 2)} hrs on duty")
    if driving > 8.0:
        # Assuming no 30 min break recorded in this simple check
        violations.append("8-Hour Break Limit: Driving exceeded 8 hours without 30-min break")

    return {
        "driving_hours": round(driving, 2),
        "on_duty_hours": round(total_on_duty, 2),
        "off_duty_hours": round(off_duty, 2),
        "sleeper_hours": round(sleeper, 2),
        "driving_remaining": round(max(0, 11.0 - driving), 2),
        "on_duty_remaining": round(max(0, 14.0 - total_on_duty), 2),
        "is_compliant": len(violations) == 0,
        "violations": violations
    }
