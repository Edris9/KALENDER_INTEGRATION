from datetime import datetime, timezone

ARBETSDAG_START = 9   # 09:00
ARBETSDAG_SLUT = 17   # 17:00

def get_free_slots(events):
    free_slots = []
    
    for event in events:
        if not event["start"] or not event["slut"]:
            continue
            
        start = datetime.fromisoformat(event["start"])
        slut = datetime.fromisoformat(event["slut"])
        
        # Kolla om det finns tid innan händelsen
        if start.hour > ARBETSDAG_START:
            free_slots.append({
                "start": f"{start.date()} 09:00",
                "slut": f"{start.date()} {start.hour}:00"
            })
        
        # Kolla om det finns tid efter händelsen
        if slut.hour < ARBETSDAG_SLUT:
            free_slots.append({
                "start": f"{slut.date()} {slut.hour}:00",
                "slut": f"{slut.date()} 17:00"
            })
    
    return free_slots