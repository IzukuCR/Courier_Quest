from core.order import Order
from services.data_manager import DataManager


class Inventory:
    def __init__(self):
        self.orders = self.load_orders()

    def load_orders(self):
        data_manager = DataManager()
        jobs_data = data_manager.load_jobs()
        orders = []
        if jobs_data and "jobs" in jobs_data:
            for job in jobs_data["jobs"]:
                order = Order(
                    _id=job.get("id"),
                    pickup=job.get("pickup"),
                    dropoff=job.get("dropoff"),
                    payout=job.get("payout"),
                    deadline=job.get("deadline"),
                    weight=job.get("weight"),
                    priority=job.get("priority"),
                    release_time=job.get("release_time")
                )
                orders.append(order)
        return orders

    def __iter__(self):
        return iter(self.orders)

    def __len__(self):
        return len(self.orders)

    def __getitem__(self, idx):
        return self.orders[idx]
