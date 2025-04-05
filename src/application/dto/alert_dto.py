from dataclasses import dataclass

@dataclass
class AlertDTO:
    log_id: str
    threat_level: str
    timestamp: str
    source_ip: str
    details: str