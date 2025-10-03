"""City module for managing city data and navigation."""

from ..services.data_manager import DataManager
from pathlib import Path


class City:
    """Represents a city with tiles, legend, and navigation capabilities."""

    def __init__(self, city_data):
        """Initialize a City instance with city data.
        
        Args:
            city_data (dict): Dictionary containing city information including
                             name, version, dimensions, tiles, legend, and goal.
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

    def get_surface_weight(self, x, y):
        """Get the surface weight for movement at specified coordinates.
        
        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
            
        Returns:
            float: Surface weight for movement (default 1.0).
        """
        tile_type = self.get_tile(x, y)
        if tile_type and tile_type in self.legend:
            tile_info = self.legend[tile_type]
            return tile_info.get("surface_weight", 1.0)
        return 1.0

    def is_blocked(self, x, y):
        """Check if the tile at specified coordinates is blocked.
        
        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
            
        Returns:
            bool: True if blocked, False if walkable.
        """
        tile_type = self.get_tile(x, y)
        if tile_type and tile_type in self.legend:
            tile_info = self.legend[tile_type]
            return tile_info.get("blocked", False)
        return True  # Out of bounds or unknown tile type is blocked

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

    def is_valid_position(self, x, y):
        """Check if the coordinates are within the city bounds.
        
        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
            
        Returns:
            bool: True if position is valid, False otherwise.
        """
        return 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y])

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
