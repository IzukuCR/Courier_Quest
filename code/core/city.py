"""
City module for managing city data and navigation.

This module handles the city map which is like a grid of tiles.
Each tile can be a road, building, or other type of terrain.
The player moves around this grid to deliver packages.
"""

from ..services.data_manager import DataManager
from pathlib import Path


class City:
    """
    Represents a city with tiles and navigation.

    This class manages the city map which is a 2D grid of tiles.
    It helps check if you can move to certain locations and
    calculates distances between points.
    """

    def __init__(self, city_data):
        """
        Create a new city from city data.

        Args:
            city_data: Dictionary with city info like name, tiles, and legend
        """
        self.name = city_data.get("name", "Unknown")
        self.version = city_data.get("version", "1.0")
        self.width = city_data.get("width", 0)
        self.height = city_data.get("height", 0)
        self.tiles = city_data.get("tiles", [])
        self.legend = city_data.get("legend", {})
        self.goal = city_data.get("goal", 0)

    def get_tile(self, x, y):
        """Get the tile at the specified coordinates.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.

        Returns:
            str or None: The tile type at (x, y) or None if invalid.
        """
        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            return self.tiles[y][x]
        return None

    def is_valid_position(self, x: int, y: int) -> bool:
        """
        Check if a position is within the city bounds.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            bool: True if position is valid (within bounds)
        """
        if not hasattr(self, 'tiles') or not self.tiles:
            return False

        height = len(self.tiles)
        width = len(self.tiles[0]) if height > 0 else 0

        return 0 <= x < width and 0 <= y < height

    def is_blocked(self, x: int, y: int) -> bool:
        """Check if a tile is blocked (building 'B')."""
        if not self.is_valid_position(x, y):
            return True  # Out of bounds = blocked

        tile_type = self.tiles[y][x]
        return tile_type == 'B'  # Buildings are blocked

    def get_surface_weight(self, x: int, y: int) -> float:
        """
        Get the movement cost/weight of a surface tile.

        Different surfaces have different movement costs:
        - 'C' (Road/Concrete): 1.0 (fastest)
        - 'P' (Park/Grass): 2.0 (slower)
        - 'B' (Building): inf (blocked)

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            float: Surface weight (lower = faster movement)
        """
        if not self.is_valid_position(x, y):
            return float('inf')

        tile_type = self.tiles[y][x]

        # Surface weights based on tile type
        weights = {
            'C': 1.0,   # Road - fastest
            'P': 2.0,   # Park - slower
            'B': float('inf')  # Building - blocked
        }

        return weights.get(tile_type, 2.0)  # Default to park weight

    def get_tile_speed_multiplier(self, x: int, y: int) -> float:
        """
        Get the speed multiplier for PLAYER movement on this tile.

        THIS IS FOR PLAYER MOVEMENT ONLY.
        Uses legend data if available, otherwise defaults.

        Higher multiplier = faster player movement.
        Lower multiplier = slower player movement.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            float: Speed multiplier (1.0 = normal, <1.0 = slower, >1.0 = faster)
        """
        if not self.is_valid_position(x, y):
            return 0.0  # Can't move out of bounds

        tile_type = self.tiles[y][x]

        # Try to get speed from legend first
        if tile_type and tile_type in self.legend:
            tile_info = self.legend[tile_type]
            # Legend uses "surface_weight" where LOWER = FASTER
            surface_weight = tile_info.get("surface_weight", 1.0)
            # Convert to speed multiplier: lower weight = higher speed
            # Road (0.5 weight) → 2.0 speed
            # Park (1.0 weight) → 1.0 speed
            return 1.0 / surface_weight if surface_weight > 0 else 1.0

        # Fallback if no legend data
        speed_multipliers = {
            'C': 1.0,   # Road - normal speed
            'P': 0.5,   # Park - half speed
            'B': 0.0    # Building - can't move
        }

        return speed_multipliers.get(tile_type, 1.0)

    def get_walkable_tiles(self):
        """Get all walkable tile positions in the city.

        Returns:
            list: List of (x, y) tuples representing walkable positions.
        """
        walkable = []
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                if not self.is_blocked(x, y):
                    walkable.append((x, y))
        return walkable

    def __str__(self):
        """Return a string representation of the city map.

        Returns:
            str: Visual representation of the city with tiles.
        """
        if not self.tiles:
            return "<Empty city map>"

        result = []
        header = (f"City: {self.name} ({self.width}x{self.height}) - "
                  f"Goal: {self.goal}")
        result.append(header)
        result.append("")

        # Map rows with more spacing between characters
        for row in self.tiles:
            row_str = ""
            for tile in row:
                if isinstance(tile, list):
                    # Take first character of each element in the tile list
                    cell_content = "".join(str(item)[0] for item in tile)
                else:
                    cell_content = str(tile)[0]
                row_str += cell_content + "  "
            result.append(row_str)

        return "\n".join(result)

    def __repr__(self):
        """Return a detailed representation of the City object.

        Returns:
            str: Detailed string representation for debugging.
        """
        return (f"City(version='{self.version}', "
                f"size={self.width}x{self.height}, "
                f"tiles={len(self.tiles)})")

    @classmethod
    def from_data_manager(cls):
        """Create a City instance using data loaded from DataManager.

        Returns:
            City: A new City instance with loaded data.

        Raises:
            ValueError: If city data could not be loaded.
        """
        data_manager = DataManager().get_instance()
        city_data = data_manager.load_city()
        if city_data is not None:
            return cls(city_data)
        else:
            raise ValueError("City data could not be loaded from DataManager.")
