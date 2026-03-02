from dataclasses import dataclass

@dataclass
class Booking:
    titel: str
    start_tid: str
    slut_tid: str
    deltagare_email: str
    
    def validate(self):
        if not self.titel:
            return "Titel saknas"
        if not self.start_tid:
            return "Starttid saknas"
        if not self.slut_tid:
            return "Sluttid saknas"
        if not self.deltagare_email:
            return "Email saknas"
        if "@" not in self.deltagare_email:
            return "Ogiltig email"
        return None