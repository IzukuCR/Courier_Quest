from typing import List, Optional
from ..core.order import Order


class PlayerInventory:
    def __init__(self, capacity_weight: float = 8.0):
        self.capacity_weight = float(capacity_weight)
        self.accepted: List[Order] = []
        self.active: Optional[Order] = None

    def carried_weight(self) -> float:
        w = 0.0
        for o in self.accepted:
            if o.state == "carrying":
                w += o.weight
        if self.active and self.active.state == "carrying" and self.active not in self.accepted:
            w += self.active.weight
        return w

    def can_accept(self, o: Order) -> bool:
        return o.state == "available"

    def accept(self, o: Order, t: float) -> bool:
        if not self.can_accept(o):
            return False
        o.state = "accepted"
        o.accepted_at = t
        if self.active is None:
            self.active = o
        if o not in self.accepted:
            self.accepted.append(o)
        return True

    def set_active(self, o: Optional[Order]) -> None:
        self.active = o

    def on_player_step(self, px: int, py: int, t: float) -> Optional[str]:
        if not self.active:
            return None

        if self.active.is_expired(t) and self.active.state not in ("delivered", "cancelled"):
            self.active.state = "expired"
            return f"{self.active.id} expired."

        # Pickup
        if self.active.state == "accepted" and self.active.at_pickup(px, py):
            if self.carried_weight() + self.active.weight <= self.capacity_weight:
                self.active.state = "carrying"
                self.active.picked_at = t
                return f"{self.active.id}: picked up."
            else:
                return "Overweight! You can't pick up yet."

        # Dropoff
        if self.active.state == "carrying" and self.active.at_dropoff(px, py):
            self.active.state = "delivered"
            self.active.delivered_at = t
            if self.active in self.accepted:
                self.accepted.remove(self.active)
            done = self.active
            self.active = None
            return f"{done.id} delivered (+{done.payout:.0f})."

        return None
