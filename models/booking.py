from dataclasses import dataclass

@dataclass
class Booking:
    titel: str
    start_tid: str
    end_tid: str
    deltagare_email: str
    
    def validate(self):
        if not self.titel:
            return "Titel missing"
        if not self.start_tid:
            return "Starttid missing"
        if not self.end_tid:
            return "endtid missing"
        if not self.deltagare_email:
            return "Email missing"
        if "@" not in self.deltagare_email:
            return "Invalid email"
        return None