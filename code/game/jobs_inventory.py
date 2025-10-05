from typing import List, Optional
from ..services.data_manager import DataManager
from ..core.order import Order


class JobsInventory:
    def __init__(self, weather_start_iso: Optional[str]):
        self._orders: List[Order] = []
        self._selected_index: int = 0
        self._scroll_offset: int = 0  # New: for scrolling through orders
        self._orders_per_page: int = 8  # New: orders shown per page
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
                o = Order(
                    id=job.get("id"),
                    pickup=job.get("pickup"),
                    dropoff=job.get("dropoff"),
                    payout=float(job.get("payout", 0)),
                    deadline_iso=job.get("deadline"),
                    weight=float(job.get("weight", 0)),
                    priority=int(job.get("priority", 0)),
                    release_time=int(job.get("release_time", 0)),
                )
                # align to weather start_time
                o.set_deadline_from_start(weather_start_iso)
                orders.append(o)
                print(
                    f"  Loaded order {o.id}: priority={o.priority}, payout={o.payout}, state={o.state}")

        # Sort orders by priority (descending) and then by payout (descending)
        # Higher priority jobs appear first, and within same priority, higher paying jobs first
        orders.sort(key=lambda order: (-order.priority, -order.payout))

        self._orders = orders
        print(f"JobsInventory: Loaded and sorted {len(self._orders)} orders")

    def all(self) -> List[Order]:
        return self._orders

    def selectable(self, t: float) -> List[Order]:
        # Show all available orders, not just unreleased ones
        available_orders = [
            o for o in self._orders if o.state == "available" and not o.is_expired(t)]

        return available_orders

    def get_selectable_page(self, t: float) -> List[Order]:
        """Get current page of selectable orders"""
        selectable_orders = self.selectable(t)
        start_idx = self._scroll_offset
        end_idx = start_idx + self._orders_per_page
        return selectable_orders[start_idx:end_idx]

    def get_scroll_info(self, t: float) -> dict:
        """Get scrolling information for UI"""
        selectable_orders = self.selectable(t)
        total_orders = len(selectable_orders)
        total_pages = (total_orders + self._orders_per_page -
                       1) // self._orders_per_page
        current_page = (self._scroll_offset // self._orders_per_page) + 1

        return {
            "current_page": current_page,
            "total_pages": total_pages,
            "total_orders": total_orders,
            "orders_per_page": self._orders_per_page,
            "scroll_offset": self._scroll_offset,
            "can_scroll_up": self._scroll_offset > 0,
            "can_scroll_down": self._scroll_offset + self._orders_per_page < total_orders
        }

    def scroll_up(self, t: float) -> bool:
        """Scroll up one page"""
        if self._scroll_offset > 0:
            self._scroll_offset = max(
                0, self._scroll_offset - self._orders_per_page)
            self._selected_index = 0  # Reset selection to first item
            return True
        return False

    def scroll_down(self, t: float) -> bool:
        """Scroll down one page"""
        selectable_orders = self.selectable(t)
        max_offset = max(0, len(selectable_orders) - self._orders_per_page)

        if self._scroll_offset < max_offset:
            self._scroll_offset = min(
                max_offset, self._scroll_offset + self._orders_per_page)
            self._selected_index = 0  # Reset selection to first item
            return True
        return False

    def cycle_selection(self, t: float) -> Optional[Order]:
        page_orders = self.get_selectable_page(t)
        if not page_orders:
            return None
        self._selected_index = (self._selected_index + 1) % len(page_orders)
        return page_orders[self._selected_index]

    def get_selected(self, t: float) -> Optional[Order]:
        page_orders = self.get_selectable_page(t)
        if not page_orders:
            return None
        self._selected_index = min(self._selected_index, len(page_orders) - 1)
        return page_orders[self._selected_index]

    def mark_expired(self, t: float) -> None:
        for o in self._orders:
            if o.is_expired(t):
                o.state = "expired"

    def cycle_selection_prev(self, t: float) -> Optional[Order]:
        page_orders = self.get_selectable_page(t)
        if not page_orders:
            return None
        # Adjust index backwards
        if self._selected_index <= 0:
            self._selected_index = len(page_orders) - 1
        else:
            self._selected_index -= 1
        return page_orders[self._selected_index]
        return None
        # Adjust index backwards
        if self._selected_index <= 0:
            self._selected_index = len(page_orders) - 1
        else:
            self._selected_index -= 1
        return page_orders[self._selected_index]
