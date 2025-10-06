from ..services.data_manager import DataManager


class Scoreboard:
    def __init__(self, name=""):
        self.score = 0
        self.player_name = name
        self.stats = {
            "total_earnings": 0,
            "reputation": 70,
            "orders_completed": 0,
            "orders_canceled": 0,
            "on_time_deliveries": 0,
            "late_deliveries": 0,
            "lost_packages": 0,
            "distance_traveled": 0
        }

    def set_player_name(self, name):
        self.player_name = name

    def add_score(self, points):
        self.score += points

    def get_score(self):
        return self.score

    def reset_score(self):
        """Reset score to 0"""
        self.score = 0

    def get_player_name(self):
        return self.player_name

    def get_final_score(self, money, reputation, successful_deliveries, late_deliveries, lost_packages):
        """Calculate final score based on player performance"""
        # Base score from money and reputation
        base_score = money + (reputation * 10)

        # Bonuses for successful deliveries
        delivery_bonus = successful_deliveries * 50

        # Penalties for poor performance
        late_penalty = late_deliveries * 25
        lost_penalty = lost_packages * 50

        # Calculate final score
        final_score = base_score + delivery_bonus - late_penalty - lost_penalty

        # Never return negative score
        return max(0, final_score)

    def calculate_performance_rank(self, final_score):
        """Calculate performance rank based on final score"""
        if final_score >= 2000:
            return "S"  # Excellent
        elif final_score >= 1500:
            return "A"  # Very Good
        elif final_score >= 1000:
            return "B"  # Good
        elif final_score >= 500:
            return "C"  # Average
        else:
            return "D"  # Below Average

    def update_stats(self, stat_name: str, value):
        """Update a specific statistic"""
        if stat_name in self.stats:
            self.stats[stat_name] = value

    def save_score(self):
        """Save the current score with stats to persistent storage"""
        dm = DataManager.get_instance()
        return dm.save_score(self.player_name, self.score, self.stats)

    @staticmethod
    def get_all_scores() -> list:
        """Get all saved scores"""
        dm = DataManager.get_instance()
        return dm.load_scores()

    @staticmethod
    def get_high_scores(limit: int = 10) -> list:
        """Get top N high scores"""
        dm = DataManager.get_instance()
        return dm.get_high_scores(limit)

    def get_stats(self) -> dict:
        """Get current game statistics"""
        return self.stats
