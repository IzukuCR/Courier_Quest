from typing import List, Optional
from ..services.data_manager import DataManager
from ..core.order import Order


class JobsInventory:
    def __init__(self, weather_start_iso: Optional[str]):
        self._orders: List[Order] = []
        self._selected_index: int = 0
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
                o.set_deadline_from_start(weather_start_iso)  # align to weather start_time
                orders.append(o)
        self._orders = orders

    def all(self) -> List[Order]:
        return self._orders

    def selectable(self, t: float) -> List[Order]:
        return [o for o in self._orders if o.is_available_to_accept(t)]

    def cycle_selection(self, t: float) -> Optional[Order]:
        opts = self.selectable(t)
        if not opts:
            return None
        self._selected_index = (self._selected_index + 1) % len(opts)
        return opts[self._selected_index]

    def get_selected(self, t: float) -> Optional[Order]:
        opts = self.selectable(t)
        if not opts:
            return None
        self._selected_index %= len(opts)
        return opts[self._selected_index]

    def mark_expired(self, t: float) -> None:
        for o in self._orders:
            if o.is_expired(t):
                o.state = "expired"
