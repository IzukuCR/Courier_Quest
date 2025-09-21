from services.data_manager import DataManager
from pathlib import Path


class City:
    def __init__(self, city_data):
        self.name = city_data.get("name", "Unknown")
        self.version = city_data.get("version", "1.0")
        self.width = city_data.get("width", 0)
        self.height = city_data.get("height", 0)
        self.tiles = city_data.get("tiles", [])
        self.legend = city_data.get("legend", {})
        self.goal = city_data.get("goal", 0)

    def get_tile(self, x, y):

        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            return self.tiles[y][x]
        return None

    def get_surface_weight(self, x, y):
        """
        Get surface weight for tile at coordinates.

        Args:
            x (int): X coordinate
            y (int): Y coordinate

        Returns:
            float: Surface weight (1.0 = normal speed)
        """
        tile_type = self.get_tile(x, y)
        if tile_type:
            tile_info = self.get_tile_info(tile_type)
            return tile_info.get("surface_weight", 1.0)
        return 1.0

    def is_blocked(self, x, y):
        """
        Check if tile at coordinates is blocked.

        Args:
            x (int): X coordinate
            y (int): Y coordinate

        Returns:
            bool: True if tile is blocked
        """
        tile_type = self.get_tile(x, y)
        if tile_type:
            tile_info = self.get_tile_info(tile_type)
            return tile_info.get("blocked", False)
        return True  # Out of bounds = blocked

    def get_walkable_tiles(self):
        walkable = []
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                if not self.is_blocked(x, y):
                    walkable.append((x, y))
        return walkable

    def get_tile_count_by_type(self):
        """
        Count tiles by type.

        Returns:
            dict: Dictionary with tile type counts
        """
        counts = {}
        for row in self.tiles:
            for tile in row:
                counts[tile] = counts.get(tile, 0) + 1
        return counts

    def is_valid_position(self, x, y):

        return 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y])

    def __str__(self):
        if not self.tiles:
            return "<Empty city map>"

        result = []
        result.append(
            f"City: {self.name} ({self.width}x{self.height}) - Goal: {self.goal}")
        result.append("")

        # Map rows with more spacing between characters
        for row in self.tiles:
            row_str = ""
            for tile in row:
                if isinstance(tile, list):
                    # Take first character of each element in the tile list
                    cell_content = "".join(str(item)[0] for item in tile)
                else:
                    cell_content = str(tile)[0]  # Just first character

                # Add spaces between each character to make it more square
                row_str += cell_content + "  "  # Two spaces between each character

            result.append(row_str)

        return "\n".join(result)

    def __repr__(self):
        # Detailed representation of the City object.
        return f"City(version='{self.version}', size={self.width}x{self.height}, tiles={len(self.tiles)})"

    @classmethod
    def from_data_manager(cls):
        # Create a City instance using data loaded from DataManager.
        data_manager = DataManager()
        city_data = data_manager.load_map()
        if city_data is not None:
            return cls(city_data)
        else:
            raise ValueError("City data could not be loaded.")
