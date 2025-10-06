"""
Order module for managing delivery orders and their states.

This module contains the Order class which represents a single delivery
job in the game. Each order has pickup and dropoff locations, payment
amount, and deadline information.
"""

from typing import List, Optional, Tuple


class Order:
    """
    Represents a delivery order in the game.
    
    This class stores all the information about a delivery job,
    like where to pick it up, where to drop it off, how much
    money you get, and when it needs to be delivered.
    """

    def __init__(self, id: str, pickup: Tuple[int, int], dropoff: Tuple[int, int],
                 payout: float = 0.0, deadline_iso: str = None, weight: float = 0.0,
                 priority: int = 0, release_time: float = 0.0):
        """
        Create a new delivery order.
        
        Args:
            id: Unique identifier for this order
            pickup: (x, y) coordinates where to pick up the package
            dropoff: (x, y) coordinates where to deliver the package
            payout: How much money you get for completing this order
            deadline_iso: When the order expires (in ISO format)
            weight: How heavy the package is
            priority: How important this order is (higher = more important)
            release_time: When this order becomes available
        """
        self.id: str = id
        self.pickup: Tuple[int, int] = pickup
        self.dropoff: Tuple[int, int] = dropoff
        self.payout: float = float(payout)
        self.deadline_iso: Optional[str] = deadline_iso
        self.weight: float = float(weight)
        self.priority: int = int(priority)
        # available, accepted, carrying, delivered, expired, cancelled
        self.state: str = "available"
        self.release_time: float = float(release_time)
        # This will be calculated when order is accepted
        self.deadline_s: Optional[float] = None
        self.accepted_at: Optional[float] = None
        self.picked_at: Optional[float] = None
        self.delivered_at: Optional[float] = None

    def set_deadline_from_start(self, start_iso=None):
        """
        Set a reasonable deadline based on priority rather than using ISO dates.
        For a game with a 10-minute timer, we want shorter deadlines.
        """
        # Store original deadline for reference
        original_deadline = getattr(self, 'deadline_s', None)

        # Set deadlines based on priority:
        # Priority 0 = 120s, Priority 1 = 90s, Priority 2+ = 60s
        if self.priority == 0:
            base_time = 120
        elif self.priority == 1:
            base_time = 90  # Exactly 90 seconds for Priority 1
        else:
            base_time = 60  # 60 seconds for Priority 2+

        # Add release time to get absolute game time
        if hasattr(self, 'release_time') and self.release_time:
            self.deadline_s = self.release_time + base_time
        else:
            self.deadline_s = base_time

        # Debug log the change but only once
        if not hasattr(self, '_deadline_debug_printed'):
            if original_deadline:
                print(
                    f"Order {self.id}: Adjusted deadline to {self.deadline_s}s (was {original_deadline}s)")
            else:
                print(f"Order {self.id}: Set deadline to {self.deadline_s}s")
            self._deadline_debug_printed = True

    def is_expired(self, t: float) -> bool:
        """
        CRITICAL: Check if order is truly expired.
        Orders in "accepted" or "carrying" state should NEVER expire regardless of deadline.

        Args:
            t: Current game time remaining (countdown from 600s)

        Returns:
            bool: True if order has fully expired and should be removed
        """
        # NEVER expire orders that are being actively handled by the player
        if self.state in ["accepted", "carrying"]:
            return False

        # Only "available" orders can expire, and only after very long periods
        if self.state == "available":
            # Calculate elapsed time since order became available
            from ..game.game import Game
            game = Game()
            elapsed_game_time = game._game_time_limit_s - t
            time_available = elapsed_game_time - self.release_time

            # Only expire if available for 10+ minutes without being accepted
            if time_available > 600:  # 10 minutes = 600 seconds
                print(
                    f"Order {self.id} genuinely expired after being available for {time_available:.1f}s")
                return True

        # Default: don't expire
        return False

    def calculate_overtime(self, current_time: float) -> float:
        """
        Calculate how much overtime has accumulated for this order.

        Args:
            current_time: Current elapsed game time

        Returns:
            float: Overtime in seconds (0 if not late)
        """
        if not self.deadline_s:
            return 0.0

        return max(0.0, current_time - self.deadline_s)

    def is_late(self, current_time: float) -> bool:
        """Check if order is currently late (past deadline)"""
        return self.calculate_overtime(current_time) > 0
