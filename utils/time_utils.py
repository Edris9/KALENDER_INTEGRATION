from datetime import datetime

ARBETSDAG_START = 9   # 09:00
ARBETSDAG_SLUT = 17   # 17:00

def get_free_slots(events):
    """
    Beräknar lediga tider baserat på upptagna händelser under en arbetsdag (09:00 - 17:00).
    Löser felet med offset-naive och offset-aware genom att normalisera tidszoner.
    """
    free_slots = []
    
    # Gruppera händelser per dag
    events_by_date = {}
    for event in events:
        start_str = event.get("start")
        slut_str = event.get("slut")
        
        if not start_str or not slut_str or "T" not in start_str:
            continue
            
        try:
            # Ersätt 'Z' med UTC-offset och skapa datetime-objekt
            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            slut_dt = datetime.fromisoformat(slut_str.replace('Z', '+00:00'))
            
            # Gör objekten "naive" (ta bort tidszonsinfo) för att kunna jämföra med lokala tider
            start_dt = start_dt.replace(tzinfo=None)
            slut_dt = slut_dt.replace(tzinfo=None)
            
            date_key = str(start_dt.date())
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append((start_dt, slut_dt))
        except (ValueError, TypeError):
            continue

    for date_str, daily_events in events_by_date.items():
        daily_events.sort()
        
        # Skapa ramar för arbetsdagen (dessa är naive som standard)
        day_start = datetime.fromisoformat(f"{date_str}T09:00:00")
        day_end = datetime.fromisoformat(f"{date_str}T17:00:00")
        
        current_time = day_start
        
        for start, slut in daily_events:
            # Nu är både 'start' och 'current_time' naive, så jämförelsen fungerar
            if start > current_time:
                gap_start = max(current_time, day_start)
                gap_end = min(start, day_end)
                
                if gap_end > gap_start:
                    free_slots.append({
                        "start": gap_start.strftime("%Y-%m-%d %H:%M"),
                        "slut": gap_end.strftime("%Y-%m-%d %H:%M")
                    })
            
            if slut > current_time:
                current_time = slut
        
        if current_time < day_end:
            free_slots.append({
                "start": current_time.strftime("%Y-%m-%d %H:%M"),
                "slut": day_end.strftime("%Y-%m-%d %H:%M")
            })
            
    return free_slots