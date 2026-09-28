from datetime import datetime, date

def calculate_hours(entries):
    totals = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    dummy_date = date.today()
    for entry in entries:
        start = datetime.combine(dummy_date, entry.start_time)
        end = datetime.combine(dummy_date, entry.end_time)
        delta = (end - start).total_seconds() / 3600.0
        totals[entry.duty_status] += delta
    return totals

def check_hos_compliance(entries):
    totals = calculate_hours(entries)
    driving = totals[3]
    on_duty = totals[3] + totals[4]
    off_duty = totals[1]
    sleeper = totals[2]

    violations = []
    if driving > 11.0:
        violations.append(f"11-Hour Driving Limit Exceeded: {round(driving, 2)} hrs")
    if on_duty > 14.0:
        violations.append(f"14-Hour On-Duty Limit Exceeded: {round(on_duty, 2)} hrs")

    return {
        "driving_hours": round(driving, 2),
        "on_duty_hours": round(on_duty, 2),
        "off_duty_hours": round(off_duty, 2),
        "sleeper_hours": round(sleeper, 2),
        "driving_remaining": round(max(0, 11.0 - driving), 2),
        "on_duty_remaining": round(max(0, 14.0 - on_duty), 2),
        "is_compliant": len(violations) == 0,
        "violations": violations
    }
