from typing import List, Optional
from ..services.data_manager import DataManager
from ..core.order import Order


class JobsInventory:
    def __init__(self, weather_start_iso: Optional[str]):
        self._orders: List[Order] = []
        self._selected_index: int = 0
        self._scroll_offset: int = 0  # Top visible item index
        self._visible_count: int = 3  # How many jobs to show at once
        self._load_orders(weather_start_iso)

    def _load_orders(self, weather_start_iso: Optional[str]) -> None:
        dm = DataManager.get_instance()
        jobs_data = dm.load_jobs()
        orders: List[Order] = []

        # jobs_data can be a list directly or a dict with "jobs" key
        if jobs_data:
            if isinstance(jobs_data, list):
                # It's a direct list of jobs
                jobs_list = jobs_data
            elif isinstance(jobs_data, dict) and "jobs" in jobs_data:
                # It's a dict with "jobs" key
                jobs_list = jobs_data["jobs"]
            else:
                jobs_list = []

            print(f"JobsInventory: Loading {len(jobs_list)} jobs from data")

            for job in jobs_list:
                release_time = int(job.get("release_time", 0))
                o = Order(
                    id=job.get("id"),
                    pickup=job.get("pickup"),
                    dropoff=job.get("dropoff"),
                    payout=float(job.get("payout", 0)),
                    deadline_iso=job.get("deadline"),
                    weight=float(job.get("weight", 0)),
                    priority=int(job.get("priority", 0)),
                    release_time=release_time,
                )
                # align to weather start_time
                o.set_deadline_from_start(weather_start_iso)
                orders.append(o)
                print(
                    f"  Loaded order {o.id}: priority={o.priority}, payout={o.payout}, release_time={release_time}s, state={o.state}")

        # Sort orders by priority (descending) and then by payout (descending)
        # Higher priority jobs appear first, and within same priority, higher paying jobs first
        orders.sort(key=lambda order: (-order.priority, -order.payout))

        self._orders = orders
        print(f"JobsInventory: Loaded and sorted {len(self._orders)} orders")

    def all(self) -> List[Order]:
        return self._orders

    def selectable(self, t: float) -> List[Order]:
        """
        Get orders that are available for selection based on:
        1. State is "available"
        2. Not expired
        3. Release time has passed (game elapsed time >= order release time)

        Args:
            t: Current game time remaining (countdown from 600s)
        """
        # Calculate elapsed game time (time from the start of the game)
        from .game import Game
        game = Game()
        elapsed_game_time = game._game_time_limit_s - t

        available_orders = []

        for o in self._orders:
            if o.state == "available" and not o.is_expired(t):
                # Check if release time has passed
                order_release_time = getattr(o, 'release_time', 0)

                if elapsed_game_time >= order_release_time:
                    # Order is available - check if it just became available
                    if not hasattr(o, '_was_released') or not o._was_released:
                        print(
                            f"Order {o.id} is now available at elapsed time {elapsed_game_time:.1f}s (release time: {order_release_time}s)")
                        o._was_released = True

                    # Add to available orders
                    available_orders.append(o)
                else:
                    # Order is not yet available
                    if not hasattr(o, '_was_released'):
                        o._was_released = False

                    # Debug: How much time until order becomes available (less frequent)
                    time_until_release = order_release_time - elapsed_game_time
                    if hasattr(o, '_last_debug_time') and elapsed_game_time - o._last_debug_time > 30:
                        print(
                            f"Order {o.id} will be available in {time_until_release:.1f}s")
                        o._last_debug_time = elapsed_game_time
                    elif not hasattr(o, '_last_debug_time'):
                        o._last_debug_time = elapsed_game_time

        # Sort available orders by priority (descending) and payout (descending)
        available_orders.sort(
            key=lambda order: (-order.priority, -order.payout))

        return available_orders

    def get_visible_orders(self, t: float) -> List[Order]:
        """Get currently visible orders based on scroll offset"""
        selectable_orders = self.selectable(t)
        start_idx = self._scroll_offset
        end_idx = start_idx + self._visible_count
        return selectable_orders[start_idx:end_idx]

    def get_scroll_info(self, t: float) -> dict:
        """Get scrolling information for UI"""
        selectable_orders = self.selectable(t)
        total_orders = len(selectable_orders)

        return {
            "total_orders": total_orders,
            "visible_count": self._visible_count,
            "scroll_offset": self._scroll_offset,
            "can_scroll_up": self._scroll_offset > 0,
            "can_scroll_down": self._scroll_offset + self._visible_count < total_orders,
            "selected_index": self._selected_index,
            "selected_visible_index": self._selected_index - self._scroll_offset
        }

    def _ensure_selected_visible(self, t: float):
        """Ensure the selected item is visible by adjusting scroll offset"""
        selectable_orders = self.selectable(t)
        if not selectable_orders or self._selected_index < 0:
            return

        # Clamp selected index to valid range
        self._selected_index = min(
            self._selected_index, len(selectable_orders) - 1)

        # If selected item is above visible area, scroll up
        if self._selected_index < self._scroll_offset:
            self._scroll_offset = self._selected_index

        # If selected item is below visible area, scroll down
        elif self._selected_index >= self._scroll_offset + self._visible_count:
            self._scroll_offset = self._selected_index - self._visible_count + 1

        # Ensure scroll offset doesn't go out of bounds
        max_scroll = max(0, len(selectable_orders) - self._visible_count)
        self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))

    def cycle_selection(self, t: float) -> Optional[Order]:
        selectable_orders = self.selectable(t)
        if not selectable_orders:
            print("JobsInventory: No selectable orders available")
            return None

        # Ensure selected index is valid
        if self._selected_index >= len(selectable_orders):
            self._selected_index = 0

        # Move to next item
        self._selected_index = (self._selected_index +
                                1) % len(selectable_orders)

        # Ensure the selected item is visible
        self._ensure_selected_visible(t)

        selected_order = selectable_orders[self._selected_index]
        print(f"JobsInventory: Selected order {selected_order.id}")
        return selected_order

    def cycle_selection_prev(self, t: float) -> Optional[Order]:
        selectable_orders = self.selectable(t)
        if not selectable_orders:
            return None

        # Move to previous item
        self._selected_index = (self._selected_index -
                                1) % len(selectable_orders)

        # Ensure the selected item is visible
        self._ensure_selected_visible(t)

        return selectable_orders[self._selected_index]

    def get_selected(self, t: float) -> Optional[Order]:
        selectable_orders = self.selectable(t)
        if not selectable_orders:
            return None

        # Ensure index is valid
        if self._selected_index >= len(selectable_orders):
            self._selected_index = 0

        if self._selected_index < len(selectable_orders):
            return selectable_orders[self._selected_index]

        return None

    def scroll_up(self, t: float) -> bool:
        """Manual scroll up"""
        if self._scroll_offset > 0:
            self._scroll_offset -= 1
            return True
        return False

    def scroll_down(self, t: float) -> bool:
        """Manual scroll down"""
        selectable_orders = self.selectable(t)
        max_scroll = max(0, len(selectable_orders) - self._visible_count)

        if self._scroll_offset < max_scroll:
            self._scroll_offset += 1
            return True
        return False

    def mark_expired(self, t: float) -> None:
        for o in self._orders:
            if o.is_expired(t):
                o.state = "expired"

    def reset_for_new_game(self):
        """Reset all tracking variables for a new game"""
        print("JobsInventory: Resetting for new game...")

        # Reset selection and scroll
        self._selected_index = 0
        self._scroll_offset = 0

        # Reset all order states and tracking
        for order in self._orders:
            order.state = "available"
            order.accepted_at = None
            order.picked_at = None
            order.delivered_at = None

            # Reset release tracking flags
            order_release_time = getattr(order, 'release_time', 0)

            if order_release_time == 0:
                # Orders with release_time = 0 should be immediately available
                order._was_released = True
                print(
                    f"  Reset order {order.id} - IMMEDIATELY AVAILABLE (release_time: 0s)")
            else:
                # Orders with release_time > 0 need to wait
                order._was_released = False
                print(
                    f"  Reset order {order.id} - will be available in {order_release_time}s")

            # Clean up debug timing
            if hasattr(order, '_last_debug_time'):
                delattr(order, '_last_debug_time')

        print(
            f"JobsInventory: Reset complete - {len(self._orders)} orders loaded")
        order.picked_at = None
        order.delivered_at = None

        # Reset release tracking flags
        order_release_time = getattr(order, 'release_time', 0)

        if order_release_time == 0:
            # Orders with release_time = 0 should be immediately available
            order._was_released = True
            print(
                f"  Reset order {order.id} - IMMEDIATELY AVAILABLE (release_time: 0s)")
        else:
            # Orders with release_time > 0 need to wait
            order._was_released = False
            print(
                f"  Reset order {order.id} - will be available in {order_release_time}s")
            # Clean up debug timing
            if hasattr(order, '_last_debug_time'):
                delattr(order, '_last_debug_time')

        print(
            f"JobsInventory: Reset complete - {len(self._orders)} orders loaded")
