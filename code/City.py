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
        """
        Get tile at specific coordinates.

        Args:
            x (int): X coordinate
            y (int): Y coordinate

        Returns:
            str: Tile type character or None if out of bounds
        """
        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            return self.tiles[y][x]
        return None

    def get_tile_info(self, tile_type):
        """
        Get information about a specific tile type.

        Args:
            tile_type (str): Tile type character

        Returns:
            dict: Tile information from legend
        """
        return self.legend.get(tile_type, {})

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
        """
        Check if position is within city bounds.

        Args:
            x (int): X coordinate
            y (int): Y coordinate

        Returns:
            bool: True if position is valid
        """
        return 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y])

    def get_neighbors(self, x, y, include_diagonal=False):
        """
        Get neighboring tile coordinates.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            include_diagonal (bool): Include diagonal neighbors

        Returns:
            list: List of valid neighbor coordinates
        """
        neighbors = []

        # Cardinal directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Add diagonal directions if requested
        if include_diagonal:
            directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                neighbors.append((nx, ny))

        return neighbors

    def __str__(self):
        # String representation of the City object.
        return f"City v{self.version} ({self.width}x{self.height}) - Goal: {self.goal}"

    def __repr__(self):
        # Detailed representation of the City object.
        return f"City(version='{self.version}', size={self.width}x{self.height}, tiles={len(self.tiles)})"
