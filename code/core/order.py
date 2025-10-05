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
