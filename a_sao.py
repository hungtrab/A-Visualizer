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
FULLSCREEN = False

# App config
PANEL_WIDTH = 250
GRID_WIDTH = 800
WIDTH = GRID_WIDTH + PANEL_WIDTH
WIN = pygame.display.set_mode((WIDTH, GRID_WIDTH), pygame.RESIZABLE)
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

# Load maze from file (auto-detects grid size from JSON)
def load_maze(filename):
    if not os.path.exists(filename):
        print(f"File {filename} not found")
        return None, None, None, None
    
    try:
        with open(filename, 'r') as f:
            maze_data = json.load(f)
        
        # Validate JSON structure
        if not all(key in maze_data for key in ["rows", "start", "end", "barriers"]):
            print(f"Error: JSON structure doesn't match. Required keys: rows, start, end, barriers")
            return None, None, None, None
        
        # Auto-detect grid size from maze file
        rows = maze_data["rows"]
        print(f"Loading maze with grid size {rows}x{rows}")
        
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
        
        return grid, start, end, rows
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {filename}")
        return None, None, None, None
    except Exception as e:
        print(f"Error loading maze: {e}")
        return None, None, None, None

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

# Run parallel benchmark (4 processes at a time, headless)
def run_benchmark_parallel(test_folder="test_mazes", batch_size=4):
    if not os.path.exists(test_folder):
        print(f"Test folder {test_folder} not found")
        return
    
    # Get all maze files and read their grid sizes
    maze_files = [f for f in os.listdir(test_folder) if f.endswith('.json')]
    
    # Create task list - read rows from each maze file
    tasks = []
    for maze_file in maze_files:
        filepath = os.path.join(test_folder, maze_file)
        try:
            with open(filepath, 'r') as f:
                maze_data = json.load(f)
            rows = maze_data.get("rows", 50)
        except:
            rows = 50
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
        output_file = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults saved to {output_file}")
    
    return results

# Visual parallel benchmark with 4 simultaneous displays
def run_benchmark_visual_parallel(win, batch_size=4):
    """Run benchmark with 4 mazes visualized simultaneously in 2x2 grid"""
    maze_folder = "test_mazes"
    if not os.path.exists(maze_folder):
        print("No test_mazes folder found!")
        return
    
    maze_files = [f for f in os.listdir(maze_folder) if f.endswith('.json')]
    if not maze_files:
        print("No maze files found!")
        return
    
    # Create test configurations (each maze with both heuristics)
    tests = []
    for maze_file in sorted(maze_files):
        tests.append((maze_file, "euclidean"))
        tests.append((maze_file, "manhattan"))
    
    results = []
    batch_size = 4
    total_batches = (len(tests) + batch_size - 1) // batch_size
    
    # Border and text settings
    BORDER_WIDTH = 4
    BORDER_COLOR = (30, 30, 30)  # Dark gray border
    TEXT_PADDING = 5
    
    for batch_idx in range(0, len(tests), batch_size):
        batch = tests[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        
        # Initialize batch data (store only maze data, not positions - those are calculated per frame)
        batch_data = []
        for i, (maze_file, heuristic) in enumerate(batch):
            filepath = os.path.join(maze_folder, maze_file)
            with open(filepath, 'r') as f:
                maze_data = json.load(f)
            
            rows = maze_data["rows"]
            
            # Create grid for this maze (gap will be calculated dynamically)
            grid = [[Spot(r, c, 1, rows) for c in range(rows)] for r in range(rows)]
            
            # Set barriers
            for (r, c) in maze_data["barriers"]:
                if 0 <= r < rows and 0 <= c < rows:
                    grid[r][c].make_barrier()
            
            # Set start and end
            sr, sc = maze_data["start"]
            er, ec = maze_data["end"]
            start = grid[sr][sc]
            end = grid[er][ec]
            start.make_start()
            end.make_end()
            
            # Update neighbors and initialize g values for all spots
            for row in grid:
                for spot in row:
                    spot.g = float('inf')
                    spot.f = float('inf')
                    spot.update_neighbors(grid)
            
            # Quadrant index (0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right)
            quadrant = i
            
            # Initialize A* data
            count = 0
            open_set = PriorityQueue()
            start.g = 0
            start.f = h(start.get_pos(), end.get_pos()) if heuristic == "euclidean" else h_manhattan(start.get_pos(), end.get_pos())
            open_set.put((start.f, count, start))
            open_set_hash = {start}
            came_from = {}
            
            batch_data.append({
                "maze_file": maze_file,
                "heuristic": heuristic,
                "grid": grid,
                "start": start,
                "end": end,
                "rows": rows,
                "quadrant": quadrant,
                "open_set": open_set,
                "open_set_hash": open_set_hash,
                "came_from": came_from,
                "count": count,
                "finished": False,
                "success": False,
                "cost": float('inf'),
                "start_time": time.time(),
                "end_time": None,
                "nodes_explored": 0
            })
        
        # Run all 4 simultaneously
        all_finished = False
        while not all_finished:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
            
            all_finished = True
            
            # Get current window size for adaptive rendering
            win_width, win_height = win.get_size()
            sub_width = win_width // 2
            sub_height = win_height // 2
            
            # Clear the entire window
            win.fill(WHITE)
            
            for data in batch_data:
                if not data["finished"]:
                    all_finished = False
                    
                    # One step of A*
                    if not data["open_set"].empty():
                        current = data["open_set"].get()[2]
                        data["open_set_hash"].discard(current)
                        data["nodes_explored"] += 1
                        
                        if current == data["end"]:
                            # Reconstruct path
                            path_length = 0
                            temp = current
                            while temp in data["came_from"]:
                                temp = data["came_from"][temp]
                                path_length += 1
                            data["cost"] = path_length
                            data["success"] = True
                            data["finished"] = True
                            data["end_time"] = time.time()
                            
                            # Mark path
                            temp = current
                            while temp in data["came_from"]:
                                temp = data["came_from"][temp]
                                if temp != data["start"]:
                                    temp.make_path()
                        else:
                            h_func = h if data["heuristic"] == "euclidean" else h_manhattan
                            for neighbor in current.neighbors:
                                temp_g = current.g + 1
                                if temp_g < neighbor.g:
                                    data["came_from"][neighbor] = current
                                    neighbor.g = temp_g
                                    neighbor.f = temp_g + h_func(neighbor.get_pos(), data["end"].get_pos())
                                    if neighbor not in data["open_set_hash"]:
                                        data["count"] += 1
                                        data["open_set"].put((neighbor.f, data["count"], neighbor))
                                        data["open_set_hash"].add(neighbor)
                                        neighbor.make_open()
                            
                            if current != data["start"]:
                                current.make_closed()
                    else:
                        data["finished"] = True
                        data["success"] = False
                        data["end_time"] = time.time()
                
                # Calculate position and gap dynamically based on current window size
                quadrant = data["quadrant"]
                pos_x = (quadrant % 2) * sub_width
                pos_y = (quadrant // 2) * sub_height
                rows = data["rows"]
                # Calculate gap to fill the entire quadrant
                gap_x = sub_width / rows
                gap_y = sub_height / rows
                gap = min(gap_x, gap_y)
                
                # Draw this maze in its quadrant (no grid lines, just filled cells)
                for row in data["grid"]:
                    for spot in row:
                        color = spot.color
                        rect = pygame.Rect(
                            pos_x + spot.col * gap,
                            pos_y + spot.row * gap,
                            gap + 1,  # +1 to prevent gaps between cells
                            gap + 1
                        )
                        pygame.draw.rect(win, color, rect)
            
            # Draw 2x2 grid borders (thick lines separating quadrants)
            # Vertical center line
            pygame.draw.line(win, BORDER_COLOR, 
                           (sub_width, 0), 
                           (sub_width, win_height), BORDER_WIDTH)
            # Horizontal center line
            pygame.draw.line(win, BORDER_COLOR, 
                           (0, sub_height), 
                           (win_width, sub_height), BORDER_WIDTH)
            
            # Draw text labels with solid background for each quadrant
            for data in batch_data:
                # Recalculate position for text
                quadrant = data["quadrant"]
                text_pos_x = (quadrant % 2) * sub_width
                text_pos_y = (quadrant // 2) * sub_height
                
                # Prepare text
                label_text = f"{data['maze_file']} - {data['heuristic']}"
                if data["finished"]:
                    if data["success"]:
                        status_text = f"OK | Cost: {data['cost']} | Time: {data['end_time'] - data['start_time']:.3f}s"
                        status_color = (0, 200, 0)  # Green
                    else:
                        status_text = f"FAIL | Cost: inf | Time: {data['end_time'] - data['start_time']:.3f}s"
                        status_color = (255, 0, 0)  # Red
                else:
                    status_text = f"Running... | Nodes: {data['nodes_explored']}"
                    status_color = (255, 165, 0)  # Orange
                
                # Render text
                label_surface = FONT_SMALL.render(label_text, True, WHITE)
                status_surface = FONT_SMALL.render(status_text, True, status_color)
                
                # Calculate text box dimensions
                text_width = max(label_surface.get_width(), status_surface.get_width()) + TEXT_PADDING * 2
                text_height = label_surface.get_height() + status_surface.get_height() + TEXT_PADDING * 3
                
                # Draw solid background for text
                text_bg_rect = pygame.Rect(
                    text_pos_x + 5,
                    text_pos_y + 5,
                    text_width,
                    text_height
                )
                pygame.draw.rect(win, (0, 0, 0), text_bg_rect)  # Black background
                pygame.draw.rect(win, BORDER_COLOR, text_bg_rect, 1)  # Border
                
                # Draw text on top of background
                win.blit(label_surface, (text_pos_x + 5 + TEXT_PADDING, text_pos_y + 5 + TEXT_PADDING))
                win.blit(status_surface, (text_pos_x + 5 + TEXT_PADDING, text_pos_y + 5 + TEXT_PADDING + label_surface.get_height() + 5))
            
            # Draw panel on the right showing batch info
            panel_rect = pygame.Rect(win_width - 160, 10, 150, 50)
            pygame.draw.rect(win, (0, 0, 0), panel_rect)
            pygame.draw.rect(win, BORDER_COLOR, panel_rect, 2)
            
            title_surface = FONT_SMALL.render("Parallel Benchmark", True, WHITE)
            batch_surface = FONT_SMALL.render(f"Batch {batch_num}/{total_batches}", True, (200, 200, 200))
            win.blit(title_surface, (panel_rect.x + 10, panel_rect.y + 8))
            win.blit(batch_surface, (panel_rect.x + 10, panel_rect.y + 28))
            
            pygame.display.update()
            pygame.time.delay(1)  # Small delay to control speed
        
        # Collect results from this batch
        for data in batch_data:
            exec_time = data["end_time"] - data["start_time"] if data["end_time"] else 0
            results.append({
                "maze_file": data["maze_file"],
                "grid_size": f"{data['rows']}x{data['rows']}",
                "heuristic": data["heuristic"],
                "success": data["success"],
                "cost": data["cost"] if data["success"] else float('inf'),
                "nodes_explored": data["nodes_explored"],
                "time": exec_time
            })
        
        # Pause before next batch
        pygame.time.delay(1500)
        
        # Take screenshot of completed batch
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/benchmark_batch_{batch_num}_{timestamp}.png"
        pygame.image.save(win, screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
    
    # Save results to CSV
    output_file = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["maze_file", "grid_size", "heuristic", "success", "cost", "nodes_explored", "time"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Benchmark complete! Results saved to {output_file}")
    return results

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
            result = load_maze(filename)
            if result[0]:
                grid, start, end, ROWS = result
                print(f"Loaded {filename} (grid size: {ROWS}x{ROWS})")
            else:
                print(f"Failed to load {filename} - check JSON structure")
    
    def run_benchmark_parallel_mode():
        print("\n=== Running Parallel Benchmark (4 at a time) ===")
        run_benchmark_parallel(batch_size=4)
        print("=== Benchmark Complete ===\n")
    
    def run_benchmark_visual_parallel_mode():
        nonlocal win
        print("\n=== Running Visual Parallel Benchmark (4 at a time) ===")
        # Get current window for benchmark
        run_benchmark_visual_parallel(win, batch_size=4)
        print("=== Benchmark Complete ===\n")
    
    def toggle_fullscreen():
        nonlocal win
        global FULLSCREEN
        FULLSCREEN = not FULLSCREEN
        if FULLSCREEN:
            win = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            print("Fullscreen mode enabled (press ESC to exit)")
        else:
            win = pygame.display.set_mode((WIDTH, GRID_WIDTH), pygame.RESIZABLE)
            print("Windowed mode")
    
    buttons = [
        Button(GRID_WIDTH + 10, 150, 230, 30, "Change Color Theme", cycle_theme),
        Button(GRID_WIDTH + 10, 185, 230, 30, "Toggle Heuristic", toggle_heuristic),
        Button(GRID_WIDTH + 10, 220, 230, 30, "Change Grid Size", change_grid_size),
        Button(GRID_WIDTH + 10, 255, 230, 30, "Generate Random Maze", generate_maze),
        Button(GRID_WIDTH + 10, 290, 230, 30, "Save Maze", save_current_maze),
        Button(GRID_WIDTH + 10, 325, 230, 30, "Load Maze", load_maze_file),
        Button(GRID_WIDTH + 10, 365, 230, 30, "Parallel (No GUI)", run_benchmark_parallel_mode),
        Button(GRID_WIDTH + 10, 400, 230, 30, "Parallel (4x Visual)", run_benchmark_visual_parallel_mode),
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
                # Press ESC to exit fullscreen
                if event.key == pygame.K_ESCAPE:
                    if FULLSCREEN:
                        FULLSCREEN = False
                        win = pygame.display.set_mode((WIDTH, GRID_WIDTH), pygame.RESIZABLE)
                        print("Exited fullscreen mode")
                
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
