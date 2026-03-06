from datetime import datetime, timedelta

WORKDAY_START = 9
WORKDAY_END = 17
SLOT_DURATION = 1  # timmar

def split_into_slots(start, end):
    slots = []
    current = start
    while current + timedelta(hours=SLOT_DURATION) <= end:
        slots.append({
            "Start": current.strftime("%Y-%m-%d %H:%M"),
            "End": (current + timedelta(hours=SLOT_DURATION)).strftime("%Y-%m-%d %H:%M")
        })
        current += timedelta(hours=SLOT_DURATION)
    return slots

def get_free_slots(events):
    free_slots = []
    today = datetime.now().date()
    
    all_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)]
    
    events_by_date = {}
    for event in events:
        start_str = event.get("Start")
        slut_str = event.get("End")
        
        if not start_str or not slut_str or "T" not in start_str:
            continue
            
        try:
            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00')).replace(tzinfo=None)
            slut_dt = datetime.fromisoformat(slut_str.replace('Z', '+00:00')).replace(tzinfo=None)
            
            if start_dt.date() < today:
                continue
            if (slut_dt - start_dt).days > 1:
                continue
            
            date_key = str(start_dt.date())
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append((start_dt, slut_dt))
        except (ValueError, TypeError):
            continue

    for date_str in all_dates:
        daily_events = events_by_date.get(date_str, [])
        daily_events.sort()
        
        day_start = datetime.fromisoformat(f"{date_str}T09:00:00")
        day_end = datetime.fromisoformat(f"{date_str}T17:00:00")
        current_time = day_start
        
        for start, slut in daily_events:
            if start > current_time:
                free_slots.extend(split_into_slots(current_time, start))
            if slut > current_time:
                current_time = slut
        
        if current_time < day_end:
            free_slots.extend(split_into_slots(current_time, day_end))
            
    return free_slots