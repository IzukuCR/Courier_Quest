"""
Undo system module for player movement.

This module lets players undo their last few moves if they make
a mistake. It costs stamina to use, so you can't use it too much.
The system uses a queue to remember the last positions.
"""

from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class PositionSnapshot:
    """
    Stores a player's position at one point in time.
    
    This is just a simple way to remember where the player
    was so we can move them back there if they want to undo.
    """
    x: int
    y: int

    def __str__(self):
        return f"Position({self.x}, {self.y})"


class UndoSystem:
    """
    Handles the undo functionality for player movement.
    
    This class keeps track of the player's recent positions
    and lets them go back to a previous position by spending
    stamina. It uses a queue system (FIFO).
    """
    def __init__(self, max_undo_steps: int = 8, stamina_cost_per_undo: float = 10.0):
        """
        Create a new undo system.
        
        Args:
            max_undo_steps: Maximum number of moves to remember
            stamina_cost_per_undo: How much stamina it costs to undo once
        """
        self.position_history: List[PositionSnapshot] = []
        self.max_steps = max_undo_steps
        self.stamina_cost = stamina_cost_per_undo

    def save_position(self, x: int, y: int) -> None:
        """
        Save player position before a move.
        
        This creates a snapshot of where the player is and adds it
        to the history list. If we have too many positions saved,
        it removes the oldest one to save memory.
        
        Args:
            x: Player's x coordinate
            y: Player's y coordinate
        """
        try:
            # Create a snapshot of current position
            snapshot = PositionSnapshot(x=x, y=y)
            self.position_history.append(snapshot)

            # Keep only the most recent moves (FIFO queue)
            if len(self.position_history) > self.max_steps:
                self.position_history.pop(0)  # Remove oldest

            print(
                f"UndoSystem: Position saved at ({x}, {y}) - {len(self.position_history)} moves in history")

        except Exception as e:
            print(f"UndoSystem: Error saving position: {e}")

    def can_undo(self) -> bool:
        """Check if undo is possible (has history)"""
        return len(self.position_history) > 0

    def undo_last_move(self) -> Tuple[bool, int, int]:
        """
        Undo last move and return success status with previous position
        Returns: (success, previous_x, previous_y)
        """
        if not self.can_undo():
            return False, 0, 0

        try:
            # Get and remove last position
            previous_position = self.position_history.pop()

            print(f"UndoSystem: Undoing to {previous_position}")
            return True, previous_position.x, previous_position.y

        except Exception as e:
            print(f"UndoSystem: Error during undo: {e}")
            return False, 0, 0

    def clear_history_on_delivery(self):
        """Clear all undo history when a delivery is made"""
        self.position_history.clear()
        print("UndoSystem: History cleared due to delivery")

    def get_stamina_cost(self) -> float:
        """Get stamina cost for one undo"""
        return self.stamina_cost

    def get_undo_count_available(self) -> int:
        """Get number of undos available"""
        return len(self.position_history)

    def get_info(self) -> dict:
        """Get undo system information for UI display"""
        return {
            "can_undo": self.can_undo(),
            "undo_count": len(self.position_history),
            "max_undos": self.max_steps,
            "stamina_cost": self.stamina_cost,
            "last_position": str(self.position_history[-1]) if self.position_history else "None"
        }
