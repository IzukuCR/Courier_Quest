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
