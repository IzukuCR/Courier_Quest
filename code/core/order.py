from datetime import datetime
from typing import List


class Order:
    def __init__(self, _id: str, pickup: List[int], dropoff: List[int], payout: float,
                 deadline: str, weight: float, priority: int, release_time: int):
        self.id = _id
        self.pickup = pickup
        self.dropoff = dropoff
        self.payout = payout
        self.deadline = datetime.fromisoformat(deadline)
        self.weight = weight
        self.priority = priority
        self.release_time = release_time
