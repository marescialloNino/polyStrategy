from dataclasses import dataclass
from datetime import datetime

@dataclass
class Order:
    """Simple class to represent an order"""
    id: str
    size: float
    price: float
    side: str
    token: str
    status: str = "pending"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow() 