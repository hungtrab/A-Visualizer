import pygame
import math
from queue import PriorityQueue
from time import sleep
import json
import os
import csv
import time
import random
import tracemalloc
from collections import deque
import multiprocessing as mp
from datetime import datetime

SLEEP = 0

# App config
PANEL_WIDTH = 250
GRID_WIDTH = 800
WIDTH = GRID_WIDTH + PANEL_WIDTH
WIN = pygame.display.set_mode((WIDTH, GRID_WIDTH))
pygame.display.set_caption("A* Pathfinding Visualization")
pygame.font.init()
FONT = pygame.font.SysFont('Arial', 16)
FONT_SMALL = pygame.font.SysFont('Arial', 14)

# Color config
RED = (255, 0, 0)       # Closed
GREEN = (0, 255, 0)     # Open
BLUE = (0, 255, 0)      # Additional
YELLOW = (255, 255, 0)  # Additional
WHITE = (255, 255, 255) # Blank
BLACK = (0, 0, 0)       # Barrier
PURPLE = (128, 0, 128)  # Shortest path
ORANGE = (255, 165, 0)  # Start
TURQUOISE = (64, 224, 208) # End
GREY = (128, 128, 128)  # Grid
PANEL_BG = (240, 240, 240)
BUTTON_COLOR = (100, 100, 250)
BUTTON_HOVER = (150, 150, 255)

# Color themes
COLOR_THEMES = {
    "Default": {
        "closed": RED, "open": GREEN, "path": PURPLE,
        "start": ORANGE, "end": TURQUOISE, "barrier": BLACK
    },
    "Blue": {
        "closed": (100, 150, 255), "open": (200, 230, 255), "path": (0, 0, 200),
        "start": (0, 100, 255), "end": (0, 200, 255), "barrier": (0, 0, 50)
    },
    "Green": {
        "closed": (255, 100, 100), "open": (100, 255, 100), "path": (0, 150, 0),
        "start": (255, 200, 0), "end": (0, 255, 150), "barrier": (50, 50, 50)
    }
}

CURRENT_THEME = "Default"

class InputBox:
    """Simple input box for getting user input in pygame"""
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = BLACK
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if event.unicode.isdigit() and len(self.text) < 3:
                        self.text += event.unicode
                self.txt_surface = FONT.render(self.text, True, self.color)
        return None

    def draw(self, win):
        pygame.draw.rect(win, WHITE, self.rect)
        pygame.draw.rect(win, self.color, self.rect, 2)
        win.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))

def show_grid_size_dialog(win):
    """Show a dialog to get grid size input from user"""
    input_text = ""
    running = True
    clock = pygame.time.Clock()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_RETURN:
                    if input_text.isdigit():
                        size = int(input_text)
                        if 10 <= size <= 200:
                            return size
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.unicode.isdigit() and len(input_text) < 3:
                    input_text += event.unicode
        
        # Draw dialog
        dialog_rect = pygame.Rect(WIDTH // 2 - 150, GRID_WIDTH // 2 - 75, 300, 150)
        pygame.draw.rect(win, WHITE, dialog_rect)
        pygame.draw.rect(win, BLACK, dialog_rect, 3)
        
        title = FONT.render("Enter Grid Size (10-200):", True, BLACK)
        win.blit(title, (dialog_rect.x + 20, dialog_rect.y + 20))
        
        # Input field
        input_rect = pygame.Rect(dialog_rect.x + 75, dialog_rect.y + 60, 150, 35)
        pygame.draw.rect(win, (220, 220, 220), input_rect)
        pygame.draw.rect(win, BLACK, input_rect, 2)
        
        input_surface = FONT.render(input_text, True, BLACK)
        win.blit(input_surface, (input_rect.x + 10, input_rect.y + 8))
        
        hint = FONT_SMALL.render("Press ENTER to confirm, ESC to cancel", True, GREY)
        win.blit(hint, (dialog_rect.x + 25, dialog_rect.y + 110))
        
        pygame.display.update()
        clock.tick(30)
    
    return None

def show_file_browser(win, start_path="."):
    """Simple file browser using pygame instead of tkinter"""
    current_path = os.path.abspath(start_path)
    selected_file = None
    scroll_offset = 0
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # Get list of files and directories
        try:
            items = ["..."] + sorted(os.listdir(current_path))
            # Filter to show only directories and .json files
            filtered_items = ["..."]
            for item in items[1:]:
                full_path = os.path.join(current_path, item)
                if os.path.isdir(full_path) or item.endswith('.json'):
                    filtered_items.append(item)
            items = filtered_items
        except PermissionError:
            items = ["..."]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_y = event.pos[1]
                    mouse_x = event.pos[0]
                    
                    # Check if click is in file list area
                    list_start_y = 80
                    item_height = 25
                    
                    if 50 < mouse_x < WIDTH - 50:
                        idx = (mouse_y - list_start_y + scroll_offset) // item_height
                        if 0 <= idx < len(items):
                            item = items[idx]
                            if item == "...":
                                current_path = os.path.dirname(current_path)
                                scroll_offset = 0
                            else:
                                full_path = os.path.join(current_path, item)
                                if os.path.isdir(full_path):
                                    current_path = full_path
                                    scroll_offset = 0
                                elif item.endswith('.json'):
                                    return full_path
                elif event.button == 4:  # Scroll up
                    scroll_offset = max(0, scroll_offset - 25)
                elif event.button == 5:  # Scroll down
                    scroll_offset = min(max(0, len(items) * 25 - 400), scroll_offset + 25)
        
        # Draw file browser
        win.fill(WHITE)
        
        # Title
        title = FONT.render("Select a maze file (.json)", True, BLACK)
        win.blit(title, (50, 20))
        
        # Current path
        path_text = FONT_SMALL.render(f"Path: {current_path[:60]}...", True, GREY) if len(current_path) > 60 else FONT_SMALL.render(f"Path: {current_path}", True, GREY)
        win.blit(path_text, (50, 50))
        
        # File list
        list_start_y = 80
        item_height = 25
        visible_items = (GRID_WIDTH - list_start_y - 50) // item_height
        
        for i, item in enumerate(items):
            y_pos = list_start_y + i * item_height - scroll_offset
            if list_start_y <= y_pos < GRID_WIDTH - 50:
                full_path = os.path.join(current_path, item) if item != "..." else ""
                
                if item == "...":
                    color = BLUE
                    display_text = "📁 .. (Parent Directory)"
                elif os.path.isdir(full_path):
                    color = (0, 0, 150)
                    display_text = f"📁 {item}"
                else:
                    color = BLACK
                    display_text = f"📄 {item}"
                
                item_surface = FONT_SMALL.render(display_text, True, color)
                win.blit(item_surface, (60, y_pos))
        
        # Instructions
        hint = FONT_SMALL.render("Click to select file, scroll to navigate, ESC to cancel", True, GREY)
        win.blit(hint, (50, GRID_WIDTH - 30))
        
        pygame.display.update()
        clock.tick(30)
    
    return None

class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False

    def draw(self, win):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(win, color, self.rect)
        pygame.draw.rect(win, BLACK, self.rect, 2)
        text_surface = FONT_SMALL.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        win.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.action()
        return None

class Spot:
    def __init__(self, row, col, width, total_rows):
        self.row = row
        self.col = col
        self.x = row * width
        self.y = col * width
        self.color = WHITE
        self.neighbors = []
        self.width = width
        self.total_rows = total_rows

    def get_pos(self):
        return self.row, self.col

    # State check 
    def is_closed(self):
        return self.color == COLOR_THEMES[CURRENT_THEME]["closed"]
    def is_open(self):
        return self.color == COLOR_THEMES[CURRENT_THEME]["open"]
    def is_barrier(self):
        return self.color == COLOR_THEMES[CURRENT_THEME]["barrier"]
    def is_start(self):
        return self.color == COLOR_THEMES[CURRENT_THEME]["start"]
    def is_end(self):
        return self.color == COLOR_THEMES[CURRENT_THEME]["end"]

    # Color set
    def reset(self):
        self.color = WHITE
    def make_start(self):
        self.color = COLOR_THEMES[CURRENT_THEME]["start"]
    def make_closed(self):
        self.color = COLOR_THEMES[CURRENT_THEME]["closed"]
    def make_open(self):
        self.color = COLOR_THEMES[CURRENT_THEME]["open"]
    def make_barrier(self):
        self.color = COLOR_THEMES[CURRENT_THEME]["barrier"]
    def make_end(self):
        self.color = COLOR_THEMES[CURRENT_THEME]["end"]
    def make_path(self):
        self.color = COLOR_THEMES[CURRENT_THEME]["path"]

    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.width))

    def update_neighbors(self, grid):
        self.neighbors = []

        if self.row < self.total_rows - 1 and not grid[self.row + 1][self.col].is_barrier(): # Down
            self.neighbors.append(grid[self.row + 1][self.col])
            
        if self.row > 0 and not grid[self.row - 1][self.col].is_barrier(): # Up
            self.neighbors.append(grid[self.row - 1][self.col])

        if self.col < self.total_rows - 1 and not grid[self.row][self.col + 1].is_barrier(): # Right
            self.neighbors.append(grid[self.row][self.col + 1])

        if self.col > 0 and not grid[self.row][self.col - 1].is_barrier(): # Left
            self.neighbors.append(grid[self.row][self.col - 1])

# Heuristic functions
HEURISTIC = "euclidean"

def h_euclidean(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def h_manhattan(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)

def h(p1, p2):
    if HEURISTIC == "manhattan":
        return h_manhattan(p1, p2)
    else:
        return h_euclidean(p1, p2)

# Reconstruct path from end to start
def reconstruct_path(came_from, current, draw):
    while current in came_from:
        current = came_from[current]
        current.make_path()
        draw()

# Main A* algorithm
def algorithm(draw, grid, start, end, visualize=True):
    count = 0
    open_set = PriorityQueue() # open_set stores: (F-score, count, node)
    open_set_dict = {start}
    open_set.put((0, count, start)) # count to tiebreaker
    came_from = {}
    
    # G-score: distance from Start -> current node (Default is infinity)
    g_score = {spot: float("inf") for row in grid for spot in row}
    g_score[start] = 0
    
    # F-score: G-score + H-score (Default is infinity)
    f_score = {spot: float("inf") for row in grid for spot in row}
    f_score[start] = h(start.get_pos(), end.get_pos())
    
    nodes_explored = 0

    while not open_set.empty():
        if visualize:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()

        # Get node with lowest F-score
        current = open_set.get()[2]
        open_set_dict.remove(current)
        nodes_explored += 1

        if current == end:
            path_length = 0
            if visualize:
                reconstruct_path(came_from, end, draw)
                end.make_end()
            else:
                # Count path length
                temp = end
                while temp in came_from:
                    path_length += 1
                    temp = came_from[temp]
            return True, g_score[end], nodes_explored

        for neighbor in current.neighbors:
            temp_g_score = g_score[current] + 1 # Assume each step has a cost of 1

            if temp_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + h(neighbor.get_pos(), end.get_pos())
                
                if neighbor not in open_set_dict:
                    count += 1
                    open_set.put((f_score[neighbor], count, neighbor))
                    open_set_dict.add(neighbor)
                    if visualize:
                        neighbor.make_open()

        if visualize:
            draw()
            sleep(SLEEP)
            if current != start:
                current.make_closed()

    return False, float('inf'), nodes_explored

# Create grid
def make_grid(rows, width):
    grid = []
    gap = width // rows
    for i in range(rows):
        grid.append([])
        for j in range(rows):
            spot = Spot(i, j, gap, rows)
            grid[i].append(spot)
    return grid

# Draw grid lines
def draw_grid(win, rows, width):
    gap = width // rows
    for i in range(rows):
        pygame.draw.line(win, GREY, (0, i * gap), (width, i * gap))
        for j in range(rows):
            pygame.draw.line(win, GREY, (j * gap, 0), (j * gap, width))

# Render (for algorithm visualization - includes display update)
def draw(win, grid, rows, width):
    win.fill(WHITE)
    for row in grid:
        for spot in row:
            spot.draw(win)
    draw_grid(win, rows, width)
    pygame.display.update()

# Render without update (for main loop to avoid flashing)
def draw_no_update(win, grid, rows, width):
    win.fill(WHITE)
    for row in grid:
        for spot in row:
            spot.draw(win)
    draw_grid(win, rows, width)

# Get mouse click position
def get_clicked_pos(pos, rows, width):
    gap = width // rows
    y, x = pos
    row = y // gap
    col = x // gap
    return row, col

# Save maze to file
def save_maze(grid, start, end, filename):
    maze_data = {
        "rows": len(grid),
        "start": start.get_pos() if start else None,
        "end": end.get_pos() if end else None,
        "barriers": []
    }
    
    for row in grid:
        for spot in row:
            if spot.is_barrier():
                maze_data["barriers"].append(spot.get_pos())
    
    with open(filename, 'w') as f:
        json.dump(maze_data, f, indent=2)
    print(f"Maze saved to {filename}")

# Load maze from file
def load_maze(filename, rows):
    if not os.path.exists(filename):
        print(f"File {filename} not found")
        return None, None, None
    
    try:
        with open(filename, 'r') as f:
            maze_data = json.load(f)
        
        # Validate JSON structure
        if not all(key in maze_data for key in ["rows", "start", "end", "barriers"]):
            print(f"Error: JSON structure doesn't match. Required keys: rows, start, end, barriers")
            return None, None, None
        
        grid = make_grid(rows, GRID_WIDTH)
        
        start = None
        end = None
        
        if maze_data["start"]:
            r, c = maze_data["start"]
            if r < rows and c < rows:
                start = grid[r][c]
                start.make_start()
        
        if maze_data["end"]:
            r, c = maze_data["end"]
            if r < rows and c < rows:
                end = grid[r][c]
                end.make_end()
        
        for r, c in maze_data["barriers"]:
            if r < rows and c < rows:
                grid[r][c].make_barrier()
        
        return grid, start, end
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {filename}")
        return None, None, None
    except Exception as e:
        print(f"Error loading maze: {e}")
        return None, None, None

# Generate random maze
def generate_random_maze(grid, density=0.3, seed=None):
    if seed is not None:
        random.seed(seed)
    
    for row in grid:
        for spot in row:
            if random.random() < density:
                spot.make_barrier()

# BFS for exact solution (for benchmarking correctness)
def bfs_shortest_path(grid, start, end):
    queue = deque([(start, 0)])
    visited = {start}
    
    while queue:
        current, dist = queue.popleft()
        
        if current == end:
            return dist
        
        for neighbor in current.neighbors:
            if neighbor not in visited and not neighbor.is_barrier():
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    
    return float('inf')

# Draw configuration panel
def draw_panel(win, buttons, rows, heuristic):
    # Draw panel background
    panel_rect = pygame.Rect(GRID_WIDTH, 0, PANEL_WIDTH, GRID_WIDTH)
    pygame.draw.rect(win, PANEL_BG, panel_rect)
    pygame.draw.line(win, BLACK, (GRID_WIDTH, 0), (GRID_WIDTH, GRID_WIDTH), 2)
    
    # Draw title
    title = FONT.render("Configuration", True, BLACK)
    win.blit(title, (GRID_WIDTH + 10, 10))
    
    # Draw current settings
    y_offset = 50
    settings_text = [
        f"Grid Size: {rows}x{rows}",
        f"Heuristic: {heuristic}",
        f"Theme: {CURRENT_THEME}"
    ]
    
    for text in settings_text:
        surface = FONT_SMALL.render(text, True, BLACK)
        win.blit(surface, (GRID_WIDTH + 10, y_offset))
        y_offset += 25
    
    # Draw buttons
    for button in buttons:
        button.draw(win)
    
    # Draw instructions
    y_offset = 550
    instructions = [
        "Left Click: Draw",
        "Right Click: Erase",
        "SPACE: Run A*",
        "C: Clear Grid"
    ]
    
    for text in instructions:
        surface = FONT_SMALL.render(text, True, BLACK)
        win.blit(surface, (GRID_WIDTH + 10, y_offset))
        y_offset += 20

# Last run results storage
last_run_result = {
    "success": None,
    "cost": None,
    "time": None,
    "nodes": None
}

def save_screenshot(win, filename=None):
    """Save a screenshot of the current window"""
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")
    
    if filename is None:
        filename = f"screenshots/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    pygame.image.save(win, filename)
    print(f"Screenshot saved: {filename}")
    return filename

def draw_result_overlay(win, success, cost, exec_time, nodes):
    """Draw result overlay on the panel"""
    # Draw result box
    result_rect = pygame.Rect(GRID_WIDTH + 10, 620, 230, 170)
    pygame.draw.rect(win, WHITE, result_rect)
    pygame.draw.rect(win, BLACK, result_rect, 2)
    
    title = FONT.render("Last Run Result", True, BLACK)
    win.blit(title, (GRID_WIDTH + 20, 625))
    
    if success is not None:
        status_color = GREEN if success else RED
        status_text = "SUCCESS" if success else "NO PATH"
        
        results = [
            (f"Status: {status_text}", status_color),
            (f"Path Cost: {cost:.1f}" if cost != float('inf') else "Path Cost: N/A", BLACK),
            (f"Time: {exec_time:.4f}s", BLACK),
            (f"Nodes Explored: {nodes}", BLACK),
        ]
        
        y_offset = 655
        for text, color in results:
            surface = FONT_SMALL.render(text, True, color)
            win.blit(surface, (GRID_WIDTH + 20, y_offset))
            y_offset += 22

# Run benchmarkon for parallel benchmark (runs in separate process)
def benchmark_worker(task_queue, result_queue, grid_width):
    """Worker process for running benchmark tests"""
    while True:
        task = task_queue.get()
        if task is None:  # Poison pill
            break
        
        filepath, heuristic_type, rows = task
        maze_file = os.path.basename(filepath)
        
        # Need to initialize pygame in this process for grid creation
        # But we won't display - just compute
        
        # Load maze data directly
        try:
            with open(filepath, 'r') as f:
                maze_data = json.load(f)
        except:
            result_queue.put(None)
            continue
        
        # Create grid
        gap = grid_width // rows
        grid = []
        for i in range(rows):
            grid.append([])
            for j in range(rows):
                # Simple spot representation for computation
                grid[i].append({"row": i, "col": j, "is_barrier": False, "neighbors": []})
        
        # Set barriers
        for r, c in maze_data.get("barriers", []):
            if r < rows and c < rows:
                grid[r][c]["is_barrier"] = True
        
        # Get start and end
        start_pos = maze_data.get("start")
        end_pos = maze_data.get("end")
        
        if not start_pos or not end_pos:
            result_queue.put(None)
            continue
        
        sr, sc = start_pos
        er, ec = end_pos
        
        # Update neighbors
        for i in range(rows):
            for j in range(rows):
                if grid[i][j]["is_barrier"]:
                    continue
                neighbors = []
                if i < rows - 1 and not grid[i+1][j]["is_barrier"]:
                    neighbors.append((i+1, j))
                if i > 0 and not grid[i-1][j]["is_barrier"]:
                    neighbors.append((i-1, j))
                if j < rows - 1 and not grid[i][j+1]["is_barrier"]:
                    neighbors.append((i, j+1))
                if j > 0 and not grid[i][j-1]["is_barrier"]:
                    neighbors.append((i, j-1))
                grid[i][j]["neighbors"] = neighbors
        
        # Heuristic functions
        def h_calc(p1, p2):
            if heuristic_type == "manhattan":
                return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
            else:
                return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
        # BFS for exact cost
        from collections import deque
        queue = deque([((sr, sc), 0)])
        visited = {(sr, sc)}
        exact_cost = float('inf')
        while queue:
            (cr, cc), dist = queue.popleft()
            if (cr, cc) == (er, ec):
                exact_cost = dist
                break
            for nr, nc in grid[cr][cc]["neighbors"]:
                if (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), dist + 1))
        
        # A* algorithm
        tracemalloc.start()
        start_time = time.time()
        
        open_set = [(0, 0, (sr, sc))]
        open_set_dict = {(sr, sc)}
        came_from = {}
        g_score = {(i, j): float('inf') for i in range(rows) for j in range(rows)}
        g_score[(sr, sc)] = 0
        f_score = {(i, j): float('inf') for i in range(rows) for j in range(rows)}
        f_score[(sr, sc)] = h_calc((sr, sc), (er, ec))
        
        nodes_explored = 0
        success = False
        cost = float('inf')
        count = 0
        
        import heapq
        heapq.heapify(open_set)
        
        while open_set:
            _, _, current = heapq.heappop(open_set)
            if current in open_set_dict:
                open_set_dict.remove(current)
            nodes_explored += 1
            
            if current == (er, ec):
                success = True
                cost = g_score[current]
                break
            
            cr, cc = current
            for neighbor in grid[cr][cc]["neighbors"]:
                temp_g = g_score[current] + 1
                if temp_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = temp_g
                    f_score[neighbor] = temp_g + h_calc(neighbor, (er, ec))
                    if neighbor not in open_set_dict:
                        count += 1
                        heapq.heappush(open_set, (f_score[neighbor], count, neighbor))
                        open_set_dict.add(neighbor)
        
        end_time = time.time()
        current_mem, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        running_time = end_time - start_time
        memory_used = peak / 1024 / 1024
        correct = (cost == exact_cost) if success else (exact_cost == float('inf'))
        
        result = {
            "maze_file": maze_file,
            "heuristic": heuristic_type,
            "success": success,
            "cost": cost,
            "exact_cost": exact_cost,
            "correct": correct,
            "nodes_explored": nodes_explored,
            "running_time": running_time,
            "memory_mb": memory_used
        }
        
        result_queue.put(result)

# Run benchmark (sequential)
def run_benchmark(test_folder="test_mazes", visualize=False, win=None, rows=50):
    if not os.path.exists(test_folder):
        print(f"Test folder {test_folder} not found")
        return
    
    results = []
    
    # Get all maze files
    maze_files = [f for f in os.listdir(test_folder) if f.endswith('.json')]
    
    for maze_file in maze_files:
        filepath = os.path.join(test_folder, maze_file)
        print(f"\nTesting {maze_file}...")
        
        for heuristic_type in ["euclidean", "manhattan"]:
            global HEURISTIC
            HEURISTIC = heuristic_type
            
            # Load maze
            grid, start, end = load_maze(filepath, rows)
            
            if not grid or not start or not end:
                print(f"Failed to load {maze_file}")
                continue
            
            # Update neighbors
            for row in grid:
                for spot in row:
                    spot.update_neighbors(grid)
            
            # Get exact solution with BFS
            exact_cost = bfs_shortest_path(grid, start, end)
            
            # Run A* with memory and time tracking
            tracemalloc.start()
            start_time = time.time()
            
            if visualize and win:
                # Visualize the benchmark run
                def draw_func():
                    draw(win, grid, rows, GRID_WIDTH)
                    draw_panel_benchmark(win, maze_file, heuristic_type)
                    pygame.display.update()
                
                success, cost, nodes_explored = algorithm(draw_func, grid, start, end, visualize=True)
            else:
                success, cost, nodes_explored = algorithm(None, grid, start, end, visualize=False)
            
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            running_time = end_time - start_time
            memory_used = peak / 1024 / 1024  # Convert to MB
            
            # Check correctness
            correct = (cost == exact_cost) if success else False
            
            result = {
                "maze_file": maze_file,
                "heuristic": heuristic_type,
                "success": success,
                "cost": cost,
                "exact_cost": exact_cost,
                "correct": correct,
                "nodes_explored": nodes_explored,
                "running_time": running_time,
                "memory_mb": memory_used
            }
            
            results.append(result)
            print(f"  {heuristic_type}: Cost={cost}, Time={running_time:.4f}s, Nodes={nodes_explored}, Correct={correct}")
            
            if visualize and win:
                # Save screenshot after each test
                screenshot_name = f"screenshots/benchmark_{maze_file}_{heuristic_type}.png"
                save_screenshot(win, screenshot_name)
                sleep(1)  # Pause between tests when visualizing
    
    # Save results to CSV
    if results:
        output_file = "benchmark_results.csv"
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults saved to {output_file}")
    
    return results

# Run parallel benchmark (4 processes at a time)
def run_benchmark_parallel(test_folder="test_mazes", rows=50, batch_size=4):
    if not os.path.exists(test_folder):
        print(f"Test folder {test_folder} not found")
        return
    
    # Get all maze files
    maze_files = [f for f in os.listdir(test_folder) if f.endswith('.json')]
    
    # Create task list
    tasks = []
    for maze_file in maze_files:
        filepath = os.path.join(test_folder, maze_file)
        for heuristic_type in ["euclidean", "manhattan"]:
            tasks.append((filepath, heuristic_type, rows))
    
    results = []
    
    # Process in batches of batch_size
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        print(f"\nProcessing batch {i // batch_size + 1}/{(len(tasks) + batch_size - 1) // batch_size}...")
        
        # Create queues
        task_queue = mp.Queue()
        result_queue = mp.Queue()
        
        # Start workers
        workers = []
        for _ in range(len(batch)):
            p = mp.Process(target=benchmark_worker, args=(task_queue, result_queue, GRID_WIDTH))
            p.start()
            workers.append(p)
        
        # Add tasks
        for task in batch:
            task_queue.put(task)
        
        # Add poison pills
        for _ in range(len(batch)):
            task_queue.put(None)
        
        # Collect results
        for _ in range(len(batch)):
            result = result_queue.get()
            if result:
                results.append(result)
                print(f"  {result['maze_file']} ({result['heuristic']}): Cost={result['cost']}, Time={result['running_time']:.4f}s")
        
        # Wait for workers to finish
        for p in workers:
            p.join()
    
    # Save results to CSV
    if results:
        output_file = "benchmark_results.csv"
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults saved to {output_file}")
    
    return results

# Visual parallel benchmark with 4 simultaneous displays
def run_benchmark_visual_parallel(test_folder="test_mazes", rows=50, batch_size=4):
    if not os.path.exists(test_folder):
        print(f"Test folder {test_folder} not found")
        return
    
    # Create screenshots folder
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")
    
    # Get all maze files
    maze_files = [f for f in os.listdir(test_folder) if f.endswith('.json')]
    
    # Create task list (only with one heuristic per batch for visual clarity)
    tasks = []
    for maze_file in maze_files:
        filepath = os.path.join(test_folder, maze_file)
        for heuristic_type in ["euclidean", "manhattan"]:
            tasks.append((filepath, heuristic_type, rows))
    
    results = []
    
    # Calculate grid layout for 4 simultaneous views
    cell_width = GRID_WIDTH // 2
    cell_height = GRID_WIDTH // 2
    
    # Process in batches
    for batch_idx in range(0, len(tasks), batch_size):
        batch = tasks[batch_idx:batch_idx + batch_size]
        print(f"\nProcessing visual batch {batch_idx // batch_size + 1}/{(len(tasks) + batch_size - 1) // batch_size}...")
        
        # Load all mazes for this batch
        batch_data = []
        for filepath, heuristic_type, r in batch:
            grid, start, end = load_maze(filepath, r)
            if grid and start and end:
                for row in grid:
                    for spot in row:
                        spot.update_neighbors(grid)
                batch_data.append({
                    "grid": grid,
                    "start": start,
                    "end": end,
                    "filepath": filepath,
                    "heuristic": heuristic_type,
                    "done": False,
                    "result": None,
                    "start_time": time.time()
                })
        
        if not batch_data:
            continue
        
        # Run all algorithms in batch simultaneously (step by step)
        # Initialize algorithm states
        for data in batch_data:
            global HEURISTIC
            HEURISTIC = data["heuristic"]
            
            data["open_set"] = PriorityQueue()
            data["open_set_dict"] = {data["start"]}
            data["open_set"].put((0, 0, data["start"]))
            data["came_from"] = {}
            data["g_score"] = {spot: float("inf") for row in data["grid"] for spot in row}
            data["g_score"][data["start"]] = 0
            data["f_score"] = {spot: float("inf") for row in data["grid"] for spot in row}
            data["f_score"][data["start"]] = h(data["start"].get_pos(), data["end"].get_pos())
            data["nodes_explored"] = 0
            data["count"] = 0
            data["heuristic_func"] = h_manhattan if data["heuristic"] == "manhattan" else h_euclidean
        
        # Run until all done
        all_done = False
        while not all_done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return results
            
            all_done = True
            
            for idx, data in enumerate(batch_data):
                if data["done"]:
                    continue
                
                all_done = False
                
                # Take one step of A*
                if data["open_set"].empty():
                    data["done"] = True
                    data["result"] = {"success": False, "cost": float('inf'), "nodes": data["nodes_explored"]}
                    data["end_time"] = time.time()
                    continue
                
                current = data["open_set"].get()[2]
                if current in data["open_set_dict"]:
                    data["open_set_dict"].remove(current)
                data["nodes_explored"] += 1
                
                if current == data["end"]:
                    # Reconstruct path
                    temp = data["end"]
                    while temp in data["came_from"]:
                        temp = data["came_from"][temp]
                        temp.make_path()
                    data["end"].make_end()
                    data["done"] = True
                    data["result"] = {
                        "success": True,
                        "cost": data["g_score"][data["end"]],
                        "nodes": data["nodes_explored"]
                    }
                    data["end_time"] = time.time()
                    continue
                
                hfunc = data["heuristic_func"]
                for neighbor in current.neighbors:
                    temp_g = data["g_score"][current] + 1
                    if temp_g < data["g_score"][neighbor]:
                        data["came_from"][neighbor] = current
                        data["g_score"][neighbor] = temp_g
                        data["f_score"][neighbor] = temp_g + hfunc(neighbor.get_pos(), data["end"].get_pos())
                        if neighbor not in data["open_set_dict"]:
                            data["count"] += 1
                            data["open_set"].put((data["f_score"][neighbor], data["count"], neighbor))
                            data["open_set_dict"].add(neighbor)
                            neighbor.make_open()
                
                if current != data["start"]:
                    current.make_closed()
            
            # Draw all grids in a 2x2 layout
            WIN.fill(WHITE)
            
            for idx, data in enumerate(batch_data):
                x_offset = (idx % 2) * cell_width
                y_offset = (idx // 2) * cell_height
                
                # Draw mini grid
                for row in data["grid"]:
                    for spot in row:
                        # Scale spot position
                        scaled_x = x_offset + (spot.x * cell_width // GRID_WIDTH)
                        scaled_y = y_offset + (spot.y * cell_height // GRID_WIDTH)
                        scaled_size = max(1, spot.width * cell_width // GRID_WIDTH)
                        pygame.draw.rect(WIN, spot.color, (scaled_x, scaled_y, scaled_size, scaled_size))
                
                # Draw label
                label = FONT_SMALL.render(f"{os.path.basename(data['filepath'])} - {data['heuristic']}", True, BLACK)
                WIN.blit(label, (x_offset + 5, y_offset + 5))
                
                if data["done"] and data["result"]:
                    status = "OK" if data["result"]["success"] else "FAIL"
                    exec_time = data["end_time"] - data["start_time"]
                    info = FONT_SMALL.render(f"{status} | Cost: {data['result']['cost']:.0f} | Time: {exec_time:.3f}s", True, 
                                             GREEN if data["result"]["success"] else RED)
                    WIN.blit(info, (x_offset + 5, y_offset + 25))
            
            # Draw panel
            panel_rect = pygame.Rect(GRID_WIDTH, 0, PANEL_WIDTH, GRID_WIDTH)
            pygame.draw.rect(WIN, PANEL_BG, panel_rect)
            pygame.draw.line(WIN, BLACK, (GRID_WIDTH, 0), (GRID_WIDTH, GRID_WIDTH), 2)
            
            title = FONT.render("Parallel Benchmark", True, BLACK)
            WIN.blit(title, (GRID_WIDTH + 10, 10))
            
            batch_info = FONT_SMALL.render(f"Batch {batch_idx // batch_size + 1}/{(len(tasks) + batch_size - 1) // batch_size}", True, BLACK)
            WIN.blit(batch_info, (GRID_WIDTH + 10, 40))
            
            pygame.display.update()
        
        # Save screenshot of completed batch
        screenshot_name = f"screenshots/batch_{batch_idx // batch_size + 1}.png"
        save_screenshot(WIN, screenshot_name)
        
        # Collect results
        for data in batch_data:
            if data["result"]:
                exec_time = data["end_time"] - data["start_time"]
                result = {
                    "maze_file": os.path.basename(data["filepath"]),
                    "heuristic": data["heuristic"],
                    "success": data["result"]["success"],
                    "cost": data["result"]["cost"],
                    "nodes_explored": data["result"]["nodes"],
                    "running_time": exec_time
                }
                results.append(result)
        
        sleep(2)  # Pause to view results
    
    # Save results to CSV
    if results:
        output_file = "benchmark_results.csv"
        fieldnames = ["maze_file", "heuristic", "success", "cost", "nodes_explored", "running_time"]
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults saved to {output_file}")
    
    return results

# Draw panel for benchmark mode
def draw_panel_benchmark(win, maze_name, heuristic, exec_time=None, result=None):
    panel_rect = pygame.Rect(GRID_WIDTH, 0, PANEL_WIDTH, GRID_WIDTH)
    pygame.draw.rect(win, PANEL_BG, panel_rect)
    pygame.draw.line(win, BLACK, (GRID_WIDTH, 0), (GRID_WIDTH, GRID_WIDTH), 2)
    
    title = FONT.render("Benchmark Mode", True, BLACK)
    win.blit(title, (GRID_WIDTH + 10, 10))
    
    info_text = [
        f"Maze: {maze_name}",
        f"Heuristic: {heuristic}",
        "",
        "Running..." if result is None else "Complete!"
    ]
    
    y_offset = 50
    for text in info_text:
        surface = FONT_SMALL.render(text, True, BLACK)
        win.blit(surface, (GRID_WIDTH + 10, y_offset))
        y_offset += 25
    
    if result is not None:
        y_offset += 20
        result_text = [
            f"Status: {'SUCCESS' if result.get('success') else 'FAILED'}",
            f"Cost: {result.get('cost', 'N/A')}",
            f"Nodes: {result.get('nodes_explored', 'N/A')}",
            f"Time: {exec_time:.4f}s" if exec_time else ""
        ]
        for text in result_text:
            color = GREEN if result.get('success') else RED
            surface = FONT_SMALL.render(text, True, color if "Status" in text else BLACK)
            win.blit(surface, (GRID_WIDTH + 10, y_offset))
            y_offset += 25

def main(win, width):
    global CURRENT_THEME, HEURISTIC
    
    ROWS = 50
    grid = make_grid(ROWS, GRID_WIDTH)

    start = None
    end = None
    run = True
    
    # Create buttons
    def cycle_theme():
        global CURRENT_THEME
        themes = list(COLOR_THEMES.keys())
        current_idx = themes.index(CURRENT_THEME)
        CURRENT_THEME = themes[(current_idx + 1) % len(themes)]
        # Recolor existing spots
        nonlocal start, end
        if start:
            start.make_start()
        if end:
            end.make_end()
        for row in grid:
            for spot in row:
                if spot.is_barrier():
                    spot.make_barrier()
    
    def toggle_heuristic():
        global HEURISTIC
        HEURISTIC = "manhattan" if HEURISTIC == "euclidean" else "euclidean"
    
    def change_grid_size():
        nonlocal ROWS, grid, start, end
        # Show input dialog
        new_size = show_grid_size_dialog(win)
        if new_size:
            ROWS = new_size
            grid = make_grid(ROWS, GRID_WIDTH)
            start = None
            end = None
            print(f"Grid size changed to {ROWS}x{ROWS}")
    
    def generate_maze():
        nonlocal start, end
        start = None
        end = None
        for row in grid:
            for spot in row:
                spot.reset()
        seed = random.randint(0, 10000)
        generate_random_maze(grid, density=0.25, seed=seed)
        print(f"Generated maze with seed: {seed}")
    
    def save_current_maze():
        filename = f"maze_{int(time.time())}.json"
        save_maze(grid, start, end, filename)
    
    def load_maze_file():
        nonlocal grid, start, end, ROWS
        # Use pygame-based file browser
        filename = show_file_browser(win)
        
        if filename:
            result = load_maze(filename, ROWS)
            if result[0]:
                grid, start, end = result
                print(f"Loaded {filename}")
            else:
                print(f"Failed to load {filename} - check JSON structure")
    
    def run_benchmark_mode():
        print("\n=== Running Benchmark Mode (No Visualization) ===")
        run_benchmark(visualize=False)
        print("=== Benchmark Complete ===\n")
    
    def run_benchmark_visualized():
        print("\n=== Running Benchmark Mode (With Visualization) ===")
        run_benchmark(visualize=True, win=win, rows=ROWS)
        print("=== Benchmark Complete ===\n")
    
    def run_benchmark_parallel_mode():
        print("\n=== Running Parallel Benchmark (4 at a time) ===")
        run_benchmark_parallel(rows=ROWS, batch_size=4)
        print("=== Benchmark Complete ===\n")
    
    def run_benchmark_visual_parallel_mode():
        print("\n=== Running Visual Parallel Benchmark (4 at a time) ===")
        run_benchmark_visual_parallel(rows=ROWS, batch_size=4)
        print("=== Benchmark Complete ===\n")
    
    buttons = [
        Button(GRID_WIDTH + 10, 150, 230, 30, "Change Color Theme", cycle_theme),
        Button(GRID_WIDTH + 10, 185, 230, 30, "Toggle Heuristic", toggle_heuristic),
        Button(GRID_WIDTH + 10, 220, 230, 30, "Change Grid Size", change_grid_size),
        Button(GRID_WIDTH + 10, 255, 230, 30, "Generate Random Maze", generate_maze),
        Button(GRID_WIDTH + 10, 290, 230, 30, "Save Maze", save_current_maze),
        Button(GRID_WIDTH + 10, 325, 230, 30, "Load Maze", load_maze_file),
        Button(GRID_WIDTH + 10, 365, 230, 30, "Benchmark (Fast)", run_benchmark_mode),
        Button(GRID_WIDTH + 10, 400, 230, 30, "Benchmark (Visual)", run_benchmark_visualized),
        Button(GRID_WIDTH + 10, 435, 230, 30, "Benchmark (Parallel)", run_benchmark_parallel_mode),
        Button(GRID_WIDTH + 10, 470, 230, 30, "Benchmark (4x Visual)", run_benchmark_visual_parallel_mode),
    ]
    
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            # Handle buttons
            for button in buttons:
                button.handle_event(event)

            # Handle left mouse button (Draw)
            if pygame.mouse.get_pressed()[0]: 
                pos = pygame.mouse.get_pos()
                # Only process if click is in grid area
                if pos[0] < GRID_WIDTH:
                    row, col = get_clicked_pos(pos, ROWS, GRID_WIDTH)
                    if row >= ROWS or col >= ROWS:
                        continue
                    spot = grid[row][col]

                    if not start and spot != end:
                        start = spot
                        start.make_start()
                    elif not end and spot != start:
                        end = spot
                        end.make_end()
                    elif spot != end and spot != start:
                        spot.make_barrier()

            # Handle right mouse button (Erase)
            elif pygame.mouse.get_pressed()[2]: 
                pos = pygame.mouse.get_pos()
                if pos[0] < GRID_WIDTH:
                    row, col = get_clicked_pos(pos, ROWS, GRID_WIDTH)
                    spot = grid[row][col]
                    spot.reset()
                    if spot == start:
                        start = None
                    elif spot == end:
                        end = None

            # Handle keyboard
            if event.type == pygame.KEYDOWN:
                # Press SPACE to run algorithm
                if event.key == pygame.K_SPACE and start and end:
                    for row in grid:
                        for spot in row:
                            spot.update_neighbors(grid)
                    
                    # Time the algorithm
                    start_time = time.time()
                    success, cost, nodes = algorithm(lambda: draw(win, grid, ROWS, GRID_WIDTH), grid, start, end, visualize=True)
                    exec_time = time.time() - start_time
                    
                    # Store results
                    last_run_result["success"] = success
                    last_run_result["cost"] = cost
                    last_run_result["time"] = exec_time
                    last_run_result["nodes"] = nodes
                    
                    print(f"\nResult: {'Success' if success else 'No Path'} | Cost: {cost} | Time: {exec_time:.4f}s | Nodes: {nodes}")
                    
                    # Save screenshot
                    draw_no_update(win, grid, ROWS, GRID_WIDTH)
                    draw_panel(win, buttons, ROWS, HEURISTIC)
                    draw_result_overlay(win, success, cost, exec_time, nodes)
                    pygame.display.update()
                    save_screenshot(win)

                # Press C to clear the grid
                if event.key == pygame.K_c:
                    start = None
                    end = None
                    grid = make_grid(ROWS, GRID_WIDTH)
        
        # Draw everything once per frame at the end of the loop
        draw_no_update(win, grid, ROWS, GRID_WIDTH)
        draw_panel(win, buttons, ROWS, HEURISTIC)
        draw_result_overlay(win, last_run_result["success"], last_run_result["cost"], 
                           last_run_result["time"], last_run_result["nodes"])
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main(WIN, WIDTH)
