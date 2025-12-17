# A* Pathfinding Visualization

An interactive A* pathfinding algorithm visualizer with configuration panel and benchmarking capabilities.

## Features

### Main Visualization
- **Interactive Grid**: Draw start point, end point, and barriers
- **Real-time Visualization**: Watch A* algorithm explore the grid
- **Color-coded States**:
  - Orange/Start color: Start point
  - Turquoise/End color: End point
  - Black/Barrier color: Obstacles
  - Green/Open color: Nodes in open set
  - Red/Closed color: Explored nodes
  - Purple/Path color: Final shortest path

### Configuration Panel
Located on the left side with the following options:

1. **Change Color Theme**: Cycle through different color schemes (Default, Blue, Green)
2. **Toggle Heuristic**: Switch between Euclidean and Manhattan distance heuristics
3. **Change Grid Size**: Toggle between 25x25, 50x50, 75x75, and 100x100 grids
4. **Generate Random Maze**: Create a random maze with barriers (prints seed for reproducibility)
5. **Save Maze**: Save current maze configuration to a JSON file
6. **Load Maze**: Load the most recently saved maze file
7. **Run Benchmark**: Execute benchmark mode on test mazes

### Benchmarking Mode
- Runs multiple mazes from the `test_mazes` folder
- Tests both Manhattan and Euclidean heuristics
- Captures metrics:
  - Running time
  - Path cost
  - Nodes explored
  - Memory usage (MB)
  - Correctness (verified against BFS optimal solution)
- Outputs results to `benchmark_results.csv`

## Controls

- **Left Click**: Place start (first click), end (second click), or draw barriers
- **Right Click**: Erase cells
- **SPACE**: Run A* algorithm
- **C**: Clear the entire grid

## Usage

### Running the Visualizer
```bash
python a_sao.py
```

### Creating Test Mazes
Save maze files in the `test_mazes` folder with this JSON format:
```json
{
  "rows": 50,
  "start": [5, 5],
  "end": [45, 45],
  "barriers": [[10, 10], [10, 11], [10, 12]]
}
```

### Running Benchmarks
1. Prepare maze files in `test_mazes/` folder
2. Click "Run Benchmark" button in the UI, or
3. Run from command line (modify code to call `run_benchmark()` directly)
4. Results saved to `benchmark_results.csv`

## Requirements
- pygame
- Python 3.6+

## Sample Test Mazes
Three sample mazes are included:
- `maze_simple.json`: Simple maze with scattered barriers
- `maze_corridor.json`: Corridor-style maze
- `maze_complex.json`: Complex maze with multiple wall patterns
