# Simple test to debug pickup issues

# Test Order.at_pickup method
class TestOrder:
    def __init__(self, pickup_pos):
        self.pickup = pickup_pos
        self.id = "TEST-001"

    def at_pickup(self, x, y):
        """Check if player is at pickup location"""
        result = self.pickup and self.pickup[0] == x and self.pickup[1] == y
        print(
            f"Order.at_pickup({x}, {y}) - pickup: {self.pickup}, result: {result}")
        return result


# Test the method
if __name__ == "__main__":
    # Test order with pickup at (5, 3)
    order = TestOrder([5, 3])

    # Test different positions
    print("Testing pickup detection:")
    print(f"Player at (5, 3): {order.at_pickup(5, 3)}")  # Should be True
    print(f"Player at (4, 3): {order.at_pickup(4, 3)}")  # Should be False
    print(f"Player at (5, 4): {order.at_pickup(5, 4)}")  # Should be False
