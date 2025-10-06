"""
Player inventory module for managing accepted delivery orders.

This module handles the orders that the player has accepted.
It keeps track of which packages they're carrying, where they
need to go, and makes sure they don't carry too much weight.
"""

from typing import List, Optional
from ..core.order import Order


class PlayerInventory:
    """
    Manages the player's accepted delivery orders.
    
    This class handles the orders that the player has accepted
    and is working on. It tracks weight limits and helps with
    navigation to pickup and dropoff points.
    """
    def __init__(self, capacity_weight: float = 8.0):
        """
        Create a new player inventory.
        
        Args:
            capacity_weight: Maximum weight the player can carry
        """
        self.capacity_weight = float(capacity_weight)
        self.accepted: List[Order] = []
        self.active: Optional[Order] = None
        # Add a flag to track if debug has been printed already
        self._debug_printed = False

    def carried_weight(self) -> float:
        """
        Calculate total weight of packages being carried.
        
        This goes through all accepted orders and adds up the weight
        of packages that are currently being carried (picked up but
        not delivered yet).
        
        Returns:
            Total weight as a float
        """
        w = 0.0
        # Add up weight from all accepted orders being carried
        for o in self.accepted:
            if o.state == "carrying":
                w += o.weight
        # Also check active order if it's not in accepted list
        if self.active and self.active.state == "carrying" and self.active not in self.accepted:
            w += self.active.weight
        return w

    def can_accept(self, o: Order) -> bool:
        """
        Check if the player can accept a new order.
        
        Args:
            o: The order to check
            
        Returns:
            True if the order can be accepted, False otherwise
        """
        # Allow accepting any available order
        return o.state == "available"

    def accept(self, o: Order, t: float) -> bool:
        if not o:
            print("PlayerInventory: Cannot accept - order is None")
            return False

        if not self.can_accept(o):
            print(
                f"PlayerInventory: Cannot accept {o.id} - state is {o.state}")
            return False

        print(f"PlayerInventory: Accepting order {o.id}")
        o.state = "accepted"
        o.accepted_at = t

        # Get current game time for deadline calculation
        from .game import Game
        game = Game()
        elapsed_game_time = game._game_time_limit_s - game.get_game_time()

        # Set deadlines based on priority - ALWAYS calculate from CURRENT time
        # Priority 0 = 120s, Priority 1 = 90s, Priority 2+ = 60s
        if o.priority == 0:
            base_time = 120
        elif o.priority == 1:
            base_time = 90
        else:
            base_time = 60  # Priority 2+

        # Set deadline to current elapsed time + allowed time
        o.deadline_s = elapsed_game_time + base_time
        print(
            f"Setting deadline for {o.id}: current game time={elapsed_game_time:.1f}, deadline={o.deadline_s:.1f}")

        if self.active is None:
            self.active = o
            print(f"PlayerInventory: Set {o.id} as active order")

        if o not in self.accepted:
            self.accepted.append(o)
            print(
                f"PlayerInventory: Added {o.id} to accepted list (total: {len(self.accepted)})")

        # After accepting an order, reset the debug print flag
        self._debug_printed = False

        return True

    def set_active(self, o: Optional[Order]) -> None:
        self.active = o

    def is_adjacent_to_pickup(self, px: int, py: int, order) -> bool:
        """Check if player is at or adjacent to pickup location"""
        if not order.pickup:
            return False

        pickup_x, pickup_y = order.pickup[0], order.pickup[1]

        # Check if player is at pickup location or adjacent (within 1 tile)
        distance = max(abs(px - pickup_x), abs(py - pickup_y))
        is_adjacent = distance <= 1

        return is_adjacent

    def is_adjacent_to_dropoff(self, px: int, py: int, order) -> bool:
        """Check if player is at or adjacent to dropoff location"""
        if not order.dropoff:
            return False

        dropoff_x, dropoff_y = order.dropoff[0], order.dropoff[1]

        # Check if player is at dropoff location or adjacent (within 1 tile)
        distance = max(abs(px - dropoff_x), abs(py - dropoff_y))
        is_adjacent = distance <= 1

        return is_adjacent

    def on_player_step(self, px: int, py: int, game_time_s: float) -> Optional[str]:
        if not self.active:
            return None

        from .game import Game
        game = Game()
        player = game.get_player()

        # Calculate elapsed game time and deadline info once
        elapsed_game_time = game._game_time_limit_s - game_time_s
        deadline_elapsed = getattr(self.active, 'deadline_s', 0)

        # Track if we're in overtime (past deadline) but DON'T prevent actions
        is_overtime = deadline_elapsed and elapsed_game_time > deadline_elapsed
        overtime_seconds = max(0, elapsed_game_time -
                               deadline_elapsed) if is_overtime else 0

        # Track overtime status but don't block actions
        # Make sure we only mark as passed once, even after loading a saved game
        if is_overtime and not hasattr(self.active, '_deadline_passed'):
            print(
                f"DEBUG: Order {self.active.id} is in overtime (+{overtime_seconds:.1f}s)")
            self.active._deadline_passed = True

        # SIMPLIFIED PICKUP LOGIC - work regardless of deadline
        if self.active.state == "accepted" and self.is_adjacent_to_pickup(px, py, self.active):
            print(f"DEBUG: Player at pickup location for {self.active.id}")

            # Simple weight check - no deadline check
            if self.carried_weight() + self.active.weight <= self.capacity_weight:
                print(f"DEBUG: Weight OK, changing state to carrying")
                # This is the critical part - update the state to carrying
                self.active.state = "carrying"
                self.active.picked_at = game_time_s

                # Show overtime message if needed
                if is_overtime:
                    msg = f"Priority {self.active.priority} package picked up! ({overtime_seconds:.0f}s overtime)"
                else:
                    msg = f"Priority {self.active.priority} package picked up!"

                return msg
            else:
                return "Overweight! You can't pick up yet."

        # SIMPLIFIED DROPOFF LOGIC - work regardless of deadline
        if self.active.state == "carrying" and self.is_adjacent_to_dropoff(px, py, self.active):
            print(f"DEBUG: Player at dropoff location for {self.active.id}")

            # Calculate overtime for UI and penalties
            elapsed_game_time = game._game_time_limit_s - game_time_s
            deadline_elapsed = getattr(self.active, 'deadline_s', 0)
            overtime_seconds = max(0, elapsed_game_time - deadline_elapsed)
            is_late = overtime_seconds > 0

            if is_late:
                print(
                    f"DEBUG: Late delivery, overtime = {overtime_seconds:.1f}s")

            # Process delivery (standard logic)
            if self.active in self.accepted:
                self.accepted.remove(self.active)
            done = self.active
            self.active = None

            # Clear undo history and reset idle time
            if player and hasattr(player, 'clear_undo_on_delivery'):
                player.clear_undo_on_delivery()
                if hasattr(player, 'idle_time'):
                    player.idle_time = 0.0

            # Initialize variables with default values
            payment_multiplier = 1.0
            reputation_msg = ""

            # Get base payout
            base_payout = done.payout

            # Update reputation based on timing
            if player:
                old_rep = player.reputation
                print(
                    f"DEBUG: Updating reputation for delivery. Overtime = {overtime_seconds:.1f}s")

                # Apply reputation change
                rep_result = player.update_reputation_delivery(
                    elapsed_game_time, deadline_elapsed,
                    overtime_seconds=overtime_seconds)

                print(
                    f"DEBUG: Reputation change: {player.reputation - old_rep:.1f}")

                # Apply payment multiplier
                payment_multiplier = player.get_payment_multiplier()
                done.payout *= payment_multiplier

                # Check for game over
                if player.is_game_over_by_reputation():
                    game._is_playing = False
                    return f"GAME OVER: Reputation too low (<20)!"

                # Format message
                reputation_msg = rep_result.get("message", "")

            # Prepare payout message
            payout_msg = f"+${done.payout:.0f}"
            if payment_multiplier > 1.0:
                payout_msg += f" (includes +5% excellence bonus)"

            # Update scoreboard
            if hasattr(game, '_scoreboard'):
                game._scoreboard.add_score(int(done.payout))

            # Return success message - MUST be inside the dropoff block
            return f"Priority {done.priority} job completed! {payout_msg}\n{reputation_msg}"

        return None

    def cancel_order(self, order_id=None) -> Optional[str]:
        """Cancel the active order or a specific order by ID with reputation penalty"""
        from .game import Game
        game = Game()
        player = game.get_player()

        # Determine which order to cancel
        target_order = None
        if order_id:
            # Find order by ID
            for order in self.accepted:
                if order.id == order_id:
                    target_order = order
                    break
        else:
            # Cancel active order
            target_order = self.active

        if not target_order:
            return "No order to cancel"

        if target_order.state in ("accepted", "carrying"):
            order_name = target_order.id
            order_priority = target_order.priority

            # Apply reputation penalty
            if player:
                # Log before update
                old_rep = player.reputation
                print(
                    f"Before order discard: Player reputation = {old_rep:.1f}")

                rep_result = player.cancel_order()
                reputation_msg = rep_result.get("message", "")

                # Log after update
                print(
                    f"After order discard: Player reputation = {player.reputation:.1f}, change = {player.reputation - old_rep:.1f}")

                # Check for game over due to low reputation
                if player.is_game_over_by_reputation():
                    game._is_playing = False  # End game when reputation < 20
                    return f"GAME OVER: Reputation too low (<20)!"

            # Update order state
            target_order.state = "cancelled"

            # Remove from accepted list
            if target_order in self.accepted:
                self.accepted.remove(target_order)

            # Clear active if it's the cancelled order
            if self.active == target_order:
                self.active = None
                # Select next order as active if available
                if self.accepted:
                    self.active = self.accepted[0]
                    next_message = f" | Next active: {self.active.id}"
                else:
                    next_message = " | No more orders"
            else:
                next_message = ""

            return f"Order {order_name} (Priority {order_priority}) discarded! {reputation_msg}{next_message}"

        return f"Cannot discard order in state: {target_order.state}"

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

    def reset_for_new_game(self):
        """Reset inventory for a new game"""
        print("PlayerInventory: Resetting for new game...")
        self.accepted.clear()
        self.active = None
        self._debug_printed = False
        print("PlayerInventory: Reset complete")
