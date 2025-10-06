from typing import List, Optional
from ..core.order import Order


class PlayerInventory:
    def __init__(self, capacity_weight: float = 8.0):
        self.capacity_weight = float(capacity_weight)
        self.accepted: List[Order] = []
        self.active: Optional[Order] = None
        # Add a flag to track if debug has been printed already
        self._debug_printed = False

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

        if self.active is None:
            self.active = o
            print(f"PlayerInventory: Set {o.id} as active order")

        if o not in self.accepted:
            self.accepted.append(o)
            print(
                f"PlayerInventory: Added {o.id} to accepted list (total: {len(self.accepted)})")

        # After accepting an order, reset the debug print flag
        self._debug_printed = False

        # Fix deadline to be more reasonable (60-120s based on priority)
        if hasattr(o, 'deadline_s') and o.deadline_s:
            # If deadline is too long, adjust it to be more reasonable
            elapsed_game_time = 0
            from .game import Game
            game = Game()
            elapsed_game_time = game._game_time_limit_s - game.get_game_time()

            if o.deadline_s - elapsed_game_time > 120:
                # Set deadlines based on priority:
                # Priority 0 = 120s, Priority 1 = 90s, Priority 2+ = 60s
                if o.priority == 0:
                    base_time = 120
                elif o.priority == 1:
                    base_time = 90  # Exactly 90 seconds for Priority 1
                else:
                    base_time = 60  # 60 seconds for Priority 2+

                new_deadline = elapsed_game_time + base_time
                print(
                    f"Fixing deadline for {o.id}: was {o.deadline_s}, now {new_deadline}")
                o.deadline_s = new_deadline

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

        print(
            f"Pickup check: Player({px}, {py}) vs Pickup({pickup_x}, {pickup_y}), distance={distance}, adjacent={is_adjacent}")
        return is_adjacent

    def is_adjacent_to_dropoff(self, px: int, py: int, order) -> bool:
        """Check if player is at or adjacent to dropoff location"""
        if not order.dropoff:
            return False

        dropoff_x, dropoff_y = order.dropoff[0], order.dropoff[1]

        # Check if player is at dropoff location or adjacent (within 1 tile)
        distance = max(abs(px - dropoff_x), abs(py - dropoff_y))
        is_adjacent = distance <= 1

        print(
            f"Dropoff check: Player({px}, {py}) vs Dropoff({dropoff_x}, {dropoff_y}), distance={distance}, adjacent={is_adjacent}")
        return is_adjacent

    def on_player_step(self, px: int, py: int, game_time_s: float) -> Optional[str]:
        if not self.active:
            print(
                f"PlayerInventory: No active order at player position ({px}, {py})")
            return None

        # Get Game instance and player for reputation updates
        from .game import Game
        game = Game()
        player = game.get_player()

        print(
            f"PlayerInventory: Player at ({px}, {py}), active order: {self.active.id}, state: {self.active.state}")
        print(
            f"PlayerInventory: Order pickup: {self.active.pickup}, dropoff: {self.active.dropoff}")

        # Check for expiration
        if self.active.is_expired(game_time_s) and self.active.state not in ("delivered", "cancelled"):
            self.active.state = "expired"

            # Update player reputation for lost/expired package
            if player:
                print(
                    f"Player lost package {self.active.id} - applying reputation penalty")
                rep_result = player.lose_package()
                print(
                    f"After loss: Player reputation = {player.reputation:.1f}")

                # Check for game over due to low reputation
                if player.is_game_over_by_reputation():
                    game._is_playing = False  # End game when reputation < 20

            return f"Priority {self.active.priority} job expired."

        # Pickup - use adjacent check instead of exact position
        if self.active.state == "accepted" and self.is_adjacent_to_pickup(px, py, self.active):
            print(
                f"PlayerInventory: Player is at/near pickup location for {self.active.id}")
            if self.carried_weight() + self.active.weight <= self.capacity_weight:
                self.active.state = "carrying"
                self.active.picked_at = game_time_s
                print(
                    f"PlayerInventory: Successfully picked up {self.active.id}")
                return f"Priority {self.active.priority} package picked up."
            else:
                print(
                    f"PlayerInventory: Cannot pick up {self.active.id} - overweight")
                return "Overweight! You can't pick up yet."
        elif self.active.state == "accepted":
            print(
                f"PlayerInventory: Player not near pickup location. Player: ({px}, {py}), Pickup: {self.active.pickup}")

        # Dropoff - use adjacent check instead of exact position
        if self.active.state == "carrying" and self.is_adjacent_to_dropoff(px, py, self.active):
            print(
                f"PlayerInventory: Player is at/near dropoff location for {self.active.id}")
            # Calculate elapsed game time for reputation system
            elapsed_game_time = game._game_time_limit_s - game_time_s
            # This should already be in elapsed time format
            deadline_elapsed = self.active.deadline_s

            if self.active in self.accepted:
                self.accepted.remove(self.active)
            done = self.active
            self.active = None

            # Clear undo history and reset idle time on delivery
            if player and hasattr(player, 'clear_undo_on_delivery'):
                player.clear_undo_on_delivery()
                # Reset idle time on delivery (player was "active")
                if hasattr(player, 'idle_time'):
                    player.idle_time = 0.0

            # Get base payout before any multipliers
            base_payout = done.payout

            # Calculate if delivery was early, on time, or late - print once per order
            if deadline_elapsed and elapsed_game_time is not None and not self._debug_printed:
                time_diff = deadline_elapsed - elapsed_game_time
                print(
                    f"Debug - Delivery timing: deadline_elapsed={deadline_elapsed:.1f}, elapsed_game_time={elapsed_game_time:.1f}, diff={time_diff:.1f}s")
                self._debug_printed = True  # Only print once

            # Update reputation based on delivery timing
            if player:
                # Log before update
                old_rep = player.reputation
                print(f"Before delivery: Player reputation = {old_rep:.1f}")

                # Pass elapsed game time values to reputation system
                rep_result = player.update_reputation_delivery(
                    elapsed_game_time, deadline_elapsed)

                # Log after update
                print(
                    f"After delivery: Player reputation = {player.reputation:.1f}, change = {player.reputation - old_rep:.1f}")

                # Apply payment multiplier based on reputation
                payment_multiplier = player.get_payment_multiplier()
                done.payout *= payment_multiplier

                # Check for game over due to low reputation
                if player.is_game_over_by_reputation():
                    game._is_playing = False  # End game when reputation < 20
                    return f"GAME OVER: Reputation too low (<20)!"

                # Add reputation change information to message
                reputation_msg = rep_result.get("message", "")

                # Prepare payout message with multiplier info if applicable
                payout_msg = f"+${done.payout:.0f}"
                if payment_multiplier > 1.0:
                    payout_msg += f" (includes +5% excellence bonus)"

            # Add to scoreboard
            if hasattr(game, '_scoreboard'):
                game._scoreboard.add_score(int(done.payout))

            # Return detailed delivery message with reputation effects
            if player and payment_multiplier > 1.0:
                return f"Priority {done.priority} job completed! {payout_msg}\n{reputation_msg}"
            else:
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
            # Apply reputation penalty
            if player:
                rep_result = player.cancel_order()
                reputation_msg = rep_result.get("message", "")

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

            return f"Order {target_order.id} cancelled! {reputation_msg}"

        return f"Cannot cancel order in state: {target_order.state}"

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
