"""Order module for managing delivery orders and their states."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional

OrderState = Literal[
    "available", "accepted", "carrying", "delivered", "expired", "cancelled"
]


@dataclass
class Order:
    """Represents a delivery order with pickup/dropoff locations and timing.

    Attributes:
        id: Unique identifier for the order.
        pickup: Pickup location as [x, y] coordinates.
        dropoff: Dropoff location as [x, y] coordinates.
        payout: Payment amount for completing the order.
        deadline_iso: Deadline in ISO format string.
        weight: Weight of the package.
        priority: Priority level of the order.
        release_time: Time when the order becomes available.
        state: Current state of the order.
        accepted_at: Timestamp when order was accepted.
        picked_at: Timestamp when package was picked up.
        delivered_at: Timestamp when package was delivered.
        deadline_s: Deadline in seconds from game start.
    """
    id: str
    pickup: List[int]  # [x, y] coordinates
    dropoff: List[int]  # [x, y] coordinates
    payout: float
    deadline_iso: str
    weight: float
    priority: int
    release_time: int
    state: OrderState = "available"
    accepted_at: Optional[float] = None
    picked_at: Optional[float] = None
    delivered_at: Optional[float] = None
    deadline_s: Optional[float] = None  # seconds from game start

    def set_deadline_from_start(self, start_dt_iso: Optional[str]) -> None:
        """Set the deadline in seconds from the game start time.

        Args:
            start_dt_iso: Game start time in ISO format, or None.
        """
        try:
            if not start_dt_iso:
                # If no start time, set deadline far in the future
                self.deadline_s = 3600.0  # 1 hour from now
                return
            start_dt = datetime.fromisoformat(
                start_dt_iso.replace('Z', '+00:00'))
            ddl_dt = datetime.fromisoformat(
                self.deadline_iso.replace('Z', '+00:00'))
            self.deadline_s = max(0.0, (ddl_dt - start_dt).total_seconds())

            # If deadline is too short, extend it
            if self.deadline_s < 300:  # Less than 5 minutes
                self.deadline_s = 600.0  # Set to 10 minutes

        except Exception as e:
            print(f"Error setting deadline for {self.id}: {e}")
            # Fallback to 10 minutes
            self.deadline_s = 600.0

        # Debug information about deadline calculation
        if hasattr(self, 'deadline_s'):
            print(
                f"Order {self.id}: Setting deadline - current value={self.deadline_s}")

        # If the deadline is already extremely large, adjust it to something reasonable
        if hasattr(self, 'deadline_s') and self.deadline_s and self.deadline_s > 300:
            # Adjust it to be between 60-180 seconds based on priority
            # Higher priority = tighter deadline
            # Priority 1=150s, 2=120s, 3=90s, etc.
            base_time = 180 - (self.priority * 30)
            self.deadline_s = max(60, base_time)
            print(
                f"Order {self.id}: Adjusted deadline to {self.deadline_s}s (was too high)")

    def is_released(self, t: float) -> bool:
        """Check if the order has been released and is available.

        Args:
            t: Current game time in seconds.

        Returns:
            bool: True if order is released, False otherwise.
        """
        return t >= float(self.release_time)

    def is_available_to_accept(self, t: float) -> bool:
        """Check if the order is available to be accepted.

        Args:
            t: Current game time in seconds.

        Returns:
            bool: True if order can be accepted, False otherwise.
        """
        # Make orders available immediately instead of waiting for release time
        return self.state == "available" and not self.is_expired(t)

    def is_expired(self, t: float) -> bool:
        """Check if the order has expired based on deadline.

        Args:
            t: Current game time in seconds.

        Returns:
            bool: True if order has expired, False otherwise.
        """
        if self.deadline_s is None:
            return False  # No deadline means never expires

        # For countdown timer (t starts at max and counts down)
        # Calculate elapsed time from start
        from ..game.game import Game
        try:
            game = Game()
            elapsed_time = game._game_time_limit_s - t
            is_expired = elapsed_time > self.deadline_s and self.state not in (
                "delivered", "cancelled")

            return is_expired
        except:
            return False  # Default to not expired if we can't calculate

    def at_pickup(self, x: int, y: int) -> bool:
        """Check if player is at or adjacent to the pickup location.

        Args:
            x: Player's X coordinate.
            y: Player's Y coordinate.

        Returns:
            bool: True if player can interact with pickup, False otherwise.
        """
        pickup_x, pickup_y = self.pickup[0], self.pickup[1]
        return abs(x - pickup_x) <= 1 and abs(y - pickup_y) <= 1

    def at_dropoff(self, x: int, y: int) -> bool:
        """Check if player is at or adjacent to the dropoff location.

        Args:
            x: Player's X coordinate.
            y: Player's Y coordinate.

        Returns:
            bool: True if player can interact with dropoff, False otherwise.
        """
        dropoff_x, dropoff_y = self.dropoff[0], self.dropoff[1]
        return abs(x - dropoff_x) <= 1 and abs(y - dropoff_y) <= 1

    def __init__(self, id=None, pickup=None, dropoff=None, payout=0.0, deadline_iso=None,
                 weight=1.0, priority=0, release_time=0):
        self.id = id
        self.pickup = pickup
        self.dropoff = dropoff
        self.payout = payout
        self.weight = weight
        self.priority = priority
        self.state = "available"
        self.deadline_s = None
        self.release_time = release_time

        self.accepted_at = None
        self.picked_at = None
        self.delivered_at = None

        # Store the ISO deadline for reference
        self.deadline_iso = deadline_iso

        # Initialize with reasonable default deadline if none provided
        if not deadline_iso:
            # Default to 2 minutes from now for testing
            self.deadline_s = 120

    def set_deadline_from_start(self, start_iso=None):
        """
        Set a reasonable deadline based on priority rather than using ISO dates.
        For a game with a 10-minute timer, we want shorter deadlines.
        """
        # Store original deadline for reference
        original_deadline = self.deadline_s

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

    def is_expired(self, current_game_time):
        """Check if order is expired based on game time"""
        if self.state in ["delivered", "expired", "cancelled"]:
            return True

        # If no deadline, can't expire
        if not self.deadline_s:
            return False

        # Calculate elapsed game time (assuming 600s total game time)
        from ..game.game import Game
        game = Game()
        elapsed_game_time = game._game_time_limit_s - current_game_time

        # Order is expired if current time exceeds deadline
        return elapsed_game_time > self.deadline_s

    def at_pickup(self, x, y):
        """Check if player is at pickup location"""
        return self.pickup and self.pickup[0] == x and self.pickup[1] == y

    def at_dropoff(self, x, y):
        """Check if player is at dropoff location"""
        return self.dropoff and self.dropoff[0] == x and self.dropoff[1] == y
