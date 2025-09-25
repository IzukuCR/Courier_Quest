import arcade
from ..game.game import Game


class Interface(arcade.Window):
    def __init__(self, title="Courier Quest"):

        self.game = Game()
        self.city = self.game.get_city()
        self.matrix = self.city.tiles
        self.cell_size = 32

        # Calculate window size based on matrix dimensions
        if self.matrix and len(self.matrix) > 0:
            matrix_width = len(self.matrix[0])  # Number of columns
            matrix_height = len(self.matrix)    # Number of rows

            window_width = matrix_width * self.cell_size
            window_height = matrix_height * self.cell_size

            # Limit maximum size in case the matrix is too large
            max_width = 1200
            max_height = 900

            if window_width > max_width or window_height > max_height:
                # If too large, adjust cell size
                scale_x = max_width / window_width
                scale_y = max_height / window_height
                scale = min(scale_x, scale_y)

                self.cell_size = int(self.cell_size * scale)
                window_width = matrix_width * self.cell_size
                window_height = matrix_height * self.cell_size
        else:
            window_width = 800
            window_height = 600

        # initialize the window
        super().__init__(window_width, window_height, title)

        # Debug: show dimensions
        if self.matrix and len(self.matrix) > 0:
            print(f"Matrix dimensions: {matrix_width}x{matrix_height}")
            print(f"Window size: {window_width}x{window_height}")
            print(f"Cell size: {self.cell_size}")
            print(f"First row sample: {self.matrix[0][:10]}")

        # Colors for the 3 types of tiles
        self.colors = {
            "C": arcade.color.GRAY,          # Road
            "P": arcade.color.FOREST_GREEN,  # Park
            "B": arcade.color.BROWN,         # Building
        }

    def on_draw(self):
        self.clear()

        if not self.matrix:
            arcade.draw_text("No map data available",
                             self.width//2, self.height//2,
                             arcade.color.RED, 16, anchor_x="center")
            return

        for row_idx, row in enumerate(self.matrix):
            for col_idx, cell in enumerate(row):
                # Calcular posición del rectángulo
                left = col_idx * self.cell_size
                right = left + self.cell_size
                top = self.height - row_idx * self.cell_size
                bottom = top - self.cell_size

                color = self.colors.get(cell, arcade.color.WHITE)

                arcade.draw_lrbt_rectangle_filled(
                    left, right, bottom, top, color)

                center_x = left + self.cell_size / 2
                center_y = bottom + self.cell_size / 2
                arcade.draw_text(str(cell),
                                 center_x, center_y,
                                 arcade.color.BLACK, 10,
                                 anchor_x="center", anchor_y="center")
