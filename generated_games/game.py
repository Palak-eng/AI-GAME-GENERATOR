
import pygame

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
CELL_SIZE = 30
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50
TRAY_OFFSET_Y = 50 # Offset for the tray area below the main grid

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
LIGHT_BLUE = (173, 216, 230)

# Bright and distinct colors for bricks
BLUE = (0, 100, 255)
GREEN = (0, 200, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
LIME = (50, 205, 50)
GOLD = (255, 215, 0)

# --- Brick Shapes (relative coordinates, (0,0) is always top-left of the bounding box) ---
BRICK_SHAPES = {
    "1x1": [(0,0)],
    "1x2": [(0,0), (0,1)],
    "2x1": [(0,0), (1,0)],
    "I3": [(0,0), (0,1), (0,2)], # 1x3 vertical
    "I3_H": [(0,0), (1,0), (2,0)], # 3x1 horizontal
    "L3_corner": [(0,0), (1,0), (0,1)], # L-tromino, top-left anchor
    "O4": [(0,0), (1,0), (0,1), (1,1)], # 2x2 square
    "I4": [(0,0), (0,1), (0,2), (0,3)], # 1x4 vertical bar
    "I4_H": [(0,0), (1,0), (2,0), (3,0)], # 4x1 horizontal bar
    "L4_basic": [(0,0), (0,1), (0,2), (1,2)], # L, facing right, bottom-left hook
    "L4_basic_R": [(0,0), (1,0), (2,0), (0,1)], # L, facing left, top-right hook
    "T4_basic": [(0,0), (1,0), (2,0), (1,1)], # T-shape
    "S4_basic": [(0,1), (1,1), (1,0), (2,0)], # S-shape
    "Z4_basic": [(0,0), (1,0), (1,1), (2,1)], # Z-shape
    "P5": [(0,0), (1,0), (0,1), (1,1), (0,2)], # P-pentomino
    "F5": [(1,0), (2,0), (0,1), (1,1), (1,2)], # F-pentomino, base (1,0)
    "L5": [(0,0), (0,1), (0,2), (0,3), (1,3)], # L-pentomino
    "T5": [(0,0), (1,0), (2,0), (1,1), (1,2)], # T-pentomino
    "U5": [(0,0), (2,0), (0,1), (1,1), (2,1)], # U-pentomino
    "V5": [(0,0), (0,1), (0,2), (1,2), (2,2)], # V-pentomino
    "W5": [(0,0), (0,1), (1,1), (1,2), (2,2)], # W-pentomino
    "X5": [(1,0), (0,1), (1,1), (2,1), (1,2)], # X-pentomino
    "Y5": [(0,0), (1,0), (2,0), (3,0), (1,1)], # Y-pentomino
    "Z5": [(0,0), (1,0), (1,1), (1,2), (2,2)], # Z-pentomino
}

# --- Level Data ---
# Each level defines the grid dimensions and the bricks required to fill it.
# The total area of bricks must exactly match the grid area.
LEVELS = [
    # Level 1: 2x2 grid (4 cells)
    {
        "grid_dim": (2, 2),
        "bricks": [("O4", BLUE)]
    },
    # Level 2: 3x2 grid (6 cells)
    {
        "grid_dim": (3, 2),
        "bricks": [("I3_H", RED), ("I3", GREEN)] # 3+3=6
    },
    # Level 3: 3x3 grid (9 cells)
    {
        "grid_dim": (3, 3),
        "bricks": [("O4", BLUE), ("L3_corner", GREEN), ("1x2", RED)] # 4+3+2 = 9
    },
    # Level 4: 4x2 grid (8 cells)
    {
        "grid_dim": (4, 2),
        "bricks": [("I4_H", PURPLE), ("I4_H", ORANGE)] # 4+4=8
    },
    # Level 5: 4x3 grid (12 cells)
    {
        "grid_dim": (4, 3),
        "bricks": [("O4", BLUE), ("O4", RED), ("O4", GREEN)] # 4+4+4=12
    },
    # Level 6: 4x4 grid (16 cells)
    {
        "grid_dim": (4, 4),
        "bricks": [("L4_basic", BLUE), ("L4_basic_R", RED), ("T4_basic", GREEN), ("S4_basic", ORANGE)] # 4+4+4+4=16
    },
    # Level 7: 5x3 grid (15 cells)
    {
        "grid_dim": (5, 3),
        "bricks": [("P5", BLUE), ("V5", RED), ("T5", GREEN)] # 5+5+5=15
    },
    # Level 8: 5x4 grid (20 cells)
    {
        "grid_dim": (5, 4),
        "bricks": [("L5", BLUE), ("F5", RED), ("U5", GREEN), ("Y5", ORANGE)] # 5+5+5+5=20
    },
    # Level 9: 6x4 grid (24 cells)
    {
        "grid_dim": (6, 4),
        "bricks": [("L4_basic", CYAN), ("Z5", BLUE), ("W5", RED), ("X5", GREEN), ("Y5", ORANGE)] # 4+5+5+5+5 = 24
    },
    # Level 10: 6x5 grid (30 cells)
    {
        "grid_dim": (6, 5),
        "bricks": [("P5", BLUE), ("F5", RED), ("L5", GREEN), ("T5", ORANGE), ("U5", PURPLE), ("V5", CYAN)] # 5x6 = 30
    },
]

class Brick:
    """Represents a single draggable and placable brick."""
    def __init__(self, shape_name, color, initial_tray_pos):
        self.shape_name = shape_name
        self.shape = BRICK_SHAPES[shape_name] # List of (dx, dy) relative coordinates
        self.color = color
        
        self.x, self.y = initial_tray_pos # Current pixel position of the (0,0) shape coordinate
        self.original_tray_x, self.original_tray_y = initial_tray_pos # Pixel position to return to if not placed
        
        self.grid_x, self.grid_y = -1, -1 # Grid position if placed
        self.is_placed = False # True if snapped to the main grid
        self.is_dragging = False # True if currently being dragged by the mouse
        self.offset_x, self.offset_y = 0, 0 # Mouse offset from brick's (x,y) for smooth dragging

    def draw(self, screen):
        """Draws the brick on the screen."""
        for dx, dy in self.shape:
            rect_x = self.x + dx * CELL_SIZE
            rect_y = self.y + dy * CELL_SIZE
            pygame.draw.rect(screen, self.color, (rect_x, rect_y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (rect_x, rect_y, CELL_SIZE, CELL_SIZE), 1) # Border

    def contains_point(self, px, py):
        """Checks if a pixel point (px, py) is within any of the brick's cells."""
        for dx, dy in self.shape:
            cell_left = self.x + dx * CELL_SIZE
            cell_top = self.y + dy * CELL_SIZE
            cell_rect = pygame.Rect(cell_left, cell_top, CELL_SIZE, CELL_SIZE)
            if cell_rect.collidepoint(px, py):
                return True
        return False

    def get_pixel_bounding_box(self):
        """Calculates the minimal bounding box of the brick in pixel coordinates."""
        min_dx = min(s[0] for s in self.shape)
        max_dx = max(s[0] for s in self.shape)
        min_dy = min(s[1] for s in self.shape)
        max_dy = max(s[1] for s in self.shape)
        
        width = (max_dx - min_dx + 1) * CELL_SIZE
        height = (max_dy - min_dy + 1) * CELL_SIZE
        
        # The true top-left pixel of the brick's visible bounding box
        true_x = self.x + min_dx * CELL_SIZE
        true_y = self.y + min_dy * CELL_SIZE
        
        return pygame.Rect(true_x, true_y, width, height)


class Game:
    """Main game class managing levels, bricks, and game loop."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Brick Grid Puzzle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)

        self.current_level_idx = 0
        self.current_grid_width = 0
        self.current_grid_height = 0
        self.grid = [] # 2D list representing the main game grid (0 = empty, 1 = filled)
        self.bricks = [] # List of Brick objects for the current level
        self.dragging_brick = None # Reference to the brick currently being dragged

        self.game_state = "PLAYING" # States: "PLAYING", "LEVEL_COMPLETE", "GAME_WON"

        self.load_level(self.current_level_idx)
    
    def load_level(self, level_idx):
        """Loads a new level based on its index."""
        if level_idx >= len(LEVELS):
            self.game_state = "GAME_WON"
            return

        self.current_level_idx = level_idx
        level_data = LEVELS[level_idx]
        self.current_grid_width, self.current_grid_height = level_data["grid_dim"]
        
        self.grid = [[0 for _ in range(self.current_grid_width)] for _ in range(self.current_grid_height)]
        self.bricks = []
        self.dragging_brick = None
        self.game_state = "PLAYING"

        # Position bricks in the tray area below the main grid
        tray_start_x = GRID_OFFSET_X
        # Calculate the y-position for the tray, considering max grid height
        tray_y = GRID_OFFSET_Y + self.current_grid_height * CELL_SIZE + TRAY_OFFSET_Y
        current_tray_x = tray_start_x
        
        tray_row_height = 0 # Keeps track of the tallest brick in the current tray row
        for shape_name, color in level_data["bricks"]:
            brick_shape_data = BRICK_SHAPES[shape_name]
            
            # Find the actual width and height of the brick's visual bounding box in cells
            min_dx = min(s[0] for s in brick_shape_data)
            max_dx = max(s[0] for s in brick_shape_data)
            min_dy = min(s[1] for s in brick_shape_data)
            max_dy = max(s[1] for s in brick_shape_data)
            
            brick_width_cells = (max_dx - min_dx + 1)
            brick_height_cells = (max_dy - min_dy + 1)

            # Check if placing this brick at current_tray_x would exceed screen width
            # (current_tray_x represents the pixel position of the (0,0) coordinate of the shape)
            if current_tray_x + brick_width_cells * CELL_SIZE > SCREEN_WIDTH - GRID_OFFSET_X:
                # Move to the next row in the tray
                current_tray_x = tray_start_x
                tray_y += (tray_row_height * CELL_SIZE) + CELL_SIZE # Move down by max height of previous row + spacing
                tray_row_height = 0 # Reset row height

            initial_brick_pos = (current_tray_x, tray_y)
            brick = Brick(shape_name, color, initial_brick_pos)
            self.bricks.append(brick)

            # Update for the next brick placement in the tray
            current_tray_x += (brick_width_cells * CELL_SIZE) + CELL_SIZE # Move cursor right for next brick
            tray_row_height = max(tray_row_height, brick_height_cells) # Update max height for current row

    def can_place_brick(self, brick, target_grid_x, target_grid_y):
        """Checks if a brick can be legally placed at the given grid coordinates."""
        for dx, dy in brick.shape:
            gx, gy = target_grid_x + dx, target_grid_y + dy
            
            # Check bounds: Ensure all parts of the brick are within the grid
            if not (0 <= gx < self.current_grid_width and 0 <= gy < self.current_grid_height):
                return False
            
            # Check overlap: Ensure target cells are empty
            if self.grid[gy][gx] != 0: # 0 means empty
                return False
        return True

    def place_brick_on_grid(self, brick):
        """Places a brick onto the internal grid state."""
        for dx, dy in brick.shape:
            gx, gy = brick.grid_x + dx, brick.grid_y + dy
            if 0 <= gx < self.current_grid_width and 0 <= gy < self.current_grid_height:
                self.grid[gy][gx] = 1 # Mark cell as filled

    def remove_brick_from_grid(self, brick):
        """Removes a brick from the internal grid state."""
        if brick.is_placed: # Only remove if it was actually placed on the grid
            for dx, dy in brick.shape:
                gx, gy = brick.grid_x + dx, brick.grid_y + dy
                if 0 <= gx < self.current_grid_width and 0 <= gy < self.current_grid_height:
                    self.grid[gy][gx] = 0 # Mark cell as empty

    def check_level_complete(self):
        """Checks if all cells in the grid are filled."""
        for row in self.grid:
            for cell in row:
                if cell == 0:
                    return False # Found an empty cell
        return True # All cells are filled

    def run(self):
        """Main game loop."""
        running = True
        while running:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.game_state == "PLAYING":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1: # Left click
                            for brick in self.bricks:
                                if brick.contains_point(mouse_x, mouse_y):
                                    self.dragging_brick = brick
                                    self.dragging_brick.is_dragging = True
                                    self.dragging_brick.offset_x = mouse_x - self.dragging_brick.x
                                    self.dragging_brick.offset_y = mouse_y - self.dragging_brick.y
                                    # If picking up a previously placed brick, remove it from the grid temporarily
                                    if self.dragging_brick.is_placed:
                                        self.remove_brick_from_grid(self.dragging_brick)
                                        self.dragging_brick.is_placed = False
                                    break # Only drag one brick at a time
                    
                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1 and self.dragging_brick:
                            self.dragging_brick.is_dragging = False
                            
                            # Calculate the potential grid position for the brick's (0,0) coordinate
                            snap_x_px = mouse_x - self.dragging_brick.offset_x
                            snap_y_px = mouse_y - self.dragging_brick.offset_y

                            target_grid_x = (snap_x_px - GRID_OFFSET_X) // CELL_SIZE
                            target_grid_y = (snap_y_px - GRID_OFFSET_Y) // CELL_SIZE
                            
                            if self.can_place_brick(self.dragging_brick, target_grid_x, target_grid_y):
                                # Snap successful: Update brick's grid and pixel positions, then place on grid
                                self.dragging_brick.grid_x = target_grid_x
                                self.dragging_brick.grid_y = target_grid_y
                                self.place_brick_on_grid(self.dragging_brick)
                                self.dragging_brick.is_placed = True
                                
                                # Snap brick's pixel drawing position to align with the grid
                                self.dragging_brick.x = GRID_OFFSET_X + self.dragging_brick.grid_x * CELL_SIZE
                                self.dragging_brick.y = GRID_OFFSET_Y + self.dragging_brick.grid_y * CELL_SIZE
                                
                                # Check for level completion after successful placement
                                if self.check_level_complete():
                                    self.game_state = "LEVEL_COMPLETE"
                            else:
                                # Snap failed: Return brick to its original tray position
                                self.dragging_brick.x = self.dragging_brick.original_tray_x
                                self.dragging_brick.y = self.dragging_brick.original_tray_y
                                self.dragging_brick.is_placed = False # Ensure it's marked as not placed
                            
                            self.dragging_brick = None # No brick is being dragged anymore

                    elif event.type == pygame.MOUSEMOTION:
                        if self.dragging_brick:
                            self.dragging_brick.x = mouse_x - self.dragging_brick.offset_x
                            self.dragging_brick.y = mouse_y - self.dragging_brick.offset_y
                
                elif self.game_state == "LEVEL_COMPLETE":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self.load_level(self.current_level_idx + 1)
                    elif event.type == pygame.MOUSEBUTTONDOWN: # Click anywhere to advance
                        self.load_level(self.current_level_idx + 1)

                elif self.game_state == "GAME_WON":
                    if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                        running = False # Exit game after winning message
            
            # --- Drawing ---
            self.screen.fill(LIGHT_BLUE)

            # Draw grid background and borders
            grid_pixel_width = self.current_grid_width * CELL_SIZE
            grid_pixel_height = self.current_grid_height * CELL_SIZE
            pygame.draw.rect(self.screen, DARK_GRAY, (GRID_OFFSET_X - 2, GRID_OFFSET_Y - 2, 
                                                       grid_pixel_width + 4, grid_pixel_height + 4), 2) # Outer border

            for y in range(self.current_grid_height):
                for x in range(self.current_grid_width):
                    rect = pygame.Rect(GRID_OFFSET_X + x * CELL_SIZE, GRID_OFFSET_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    if self.grid[y][x] == 0:
                        pygame.draw.rect(self.screen, GRAY, rect) # Empty cell background
                    pygame.draw.rect(self.screen, BLACK, rect, 1) # Cell borders

            # Draw bricks (drawing dragging_brick last ensures it's on top)
            for brick in self.bricks:
                if brick != self.dragging_brick:
                    brick.draw(self.screen)
            if self.dragging_brick:
                self.dragging_brick.draw(self.screen)
            
            # Draw UI / Messages
            level_text = self.font.render(f"Level: {self.current_level_idx + 1}/{len(LEVELS)}", True, BLACK)
            self.screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 20, 20))

            if self.game_state == "LEVEL_COMPLETE":
                message_text = self.font.render("Level Complete! Press SPACE or click to continue...", True, BLACK)
                message_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                pygame.draw.rect(self.screen, WHITE, message_rect.inflate(20,20))
                pygame.draw.rect(self.screen, DARK_GRAY, message_rect.inflate(20,20), 2)
                self.screen.blit(message_text, message_rect)
            elif self.game_state == "GAME_WON":
                message_text = self.font.render("Congratulations! You completed all levels!", True, BLACK)
                message_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                pygame.draw.rect(self.screen, WHITE, message_rect.inflate(20,20))
                pygame.draw.rect(self.screen, DARK_GRAY, message_rect.inflate(20,20), 2)
                self.screen.blit(message_text, message_rect)

            pygame.display.flip()
            self.clock.tick(60) # Cap frame rate at 60 FPS

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
