from ..services.data_manager import DataManager
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

        # Check if coordinates are valid
        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            return self.tiles[y][x]  # Return the tile at (x, y)
        return None

    def get_surface_weight(self, x, y):

        tile_type = self.get_tile(x, y)  # Get the tile type at (x, y)
        if tile_type and tile_type in self.legend:  # Check if tile type exists in legend
            tile_info = self.legend[tile_type]  # Get the tile info from legend
            # Default weight is 1.0 if not specified, else return the specified weight
            return tile_info.get("surface_weight", 1.0)
        return 1.0

    def is_blocked(self, x, y):

        tile_type = self.get_tile(x, y)  # Get the tile type at (x, y)
        if tile_type and tile_type in self.legend:  # Check if tile type exists in legend
            tile_info = self.legend[tile_type]  # Get the tile info from legend
            # Default is False (not blocked) if not specified, else return the specified blocked status
            return tile_info.get("blocked", False)
        return True  # Out of bounds or unknown tile type is considered blocked

    def get_walkable_tiles(self):
        walkable = []  # List to store walkable tile positions
        for y in range(len(self.tiles)):  # Iterate over rows
            for x in range(len(self.tiles[y])):  # Iterate over columns
                if not self.is_blocked(x, y):  # If the tile is not blocked
                    # Add the (x, y) position to the list
                    walkable.append((x, y))
        return walkable  # Returns list of tuples

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
        data_manager = DataManager().get_instance()
        city_data = data_manager.load_city()
        if city_data is not None:
            return cls(city_data)
        else:
            raise ValueError("City Class: City data could not be loaded.")
