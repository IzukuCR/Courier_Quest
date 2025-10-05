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
        # Allow accepting any available order
        return o.state == "available"

    def accept(self, o: Order, t: float) -> bool:
        if not self.can_accept(o):
            print(
                f"PlayerInventory: Cannot accept {o.id} - state is {o.state}")
            return False

        print(f"PlayerInventory: Accepting order {o.id}")
        o.state = "accepted"
        o.accepted_at = t

        if self.active is None:
            self.active = o
            print(f"PlayerInventory: Set {o.id} as active order")

        if o not in self.accepted:
            self.accepted.append(o)
            print(
                f"PlayerInventory: Added {o.id} to accepted list (total: {len(self.accepted)})")

        return True

    def set_active(self, o: Optional[Order]) -> None:
        self.active = o

    def on_player_step(self, px: int, py: int, game_time_s: float) -> Optional[str]:
        if not self.active:
            return None

        if self.active.is_expired(game_time_s) and self.active.state not in ("delivered", "cancelled"):
            self.active.state = "expired"
            return f"{self.active.id} expired."

        # Pickup
        if self.active.state == "accepted" and self.active.at_pickup(px, py):
            if self.carried_weight() + self.active.weight <= self.capacity_weight:
                self.active.state = "carrying"
                self.active.picked_at = game_time_s
                return f"{self.active.id}: picked up."
            else:
                return "Overweight! You can't pick up yet."

        # Dropoff
        if self.active.state == "carrying" and self.active.at_dropoff(px, py):
            self.active.state = "delivered"
            self.active.delivered_at = game_time_s
            if self.active in self.accepted:
                self.accepted.remove(self.active)
            done = self.active
            self.active = None

            # Clear undo history and reset idle time on delivery
            from .game import Game
            game = Game()
            player = game.get_player()
            if player and hasattr(player, 'clear_undo_on_delivery'):
                player.clear_undo_on_delivery()
                # Reset idle time on delivery (player was "active")
                if hasattr(player, 'idle_time'):
                    player.idle_time = 0.0

            return f"{done.id} delivered (+{done.payout:.0f})."

        return None

    def next_active(self) -> Optional[Order]:
        """Select next active order among accepted ones."""
        if not self.accepted:
            return self.active
        if self.active not in self.accepted:
            self.active = self.accepted[0]
            return self.active
        idx = self.accepted.index(self.active)
        idx = (idx + 1) % len(self.accepted)
        self.active = self.accepted[idx]
        return self.active

    def prev_active(self) -> Optional[Order]:
        """Select previous active order among accepted ones."""
        if not self.accepted:
            return self.active
        if self.active not in self.accepted:
            self.active = self.accepted[-1]
            return self.active
        idx = self.accepted.index(self.active)
        idx = (idx - 1) % len(self.accepted)
        self.active = self.accepted[idx]
        return self.active
