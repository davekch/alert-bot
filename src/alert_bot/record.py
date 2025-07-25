from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Record:
    subject: str
    body: str
    timestamp: datetime

    def as_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d
