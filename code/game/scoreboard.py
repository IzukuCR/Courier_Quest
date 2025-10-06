class Scoreboard:
    def __init__(self, name=""):
        self.score = 0
        self.player_name = name

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
