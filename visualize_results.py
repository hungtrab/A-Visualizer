import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)

def load_latest_benchmark():
    """Load the most recent benchmark CSV file"""
    csv_files = glob.glob("benchmark_*.csv")
    if not csv_files:
        print("No benchmark CSV files found!")
        return None
    
    latest_file = max(csv_files, key=os.path.getctime)
    print(f"Loading: {latest_file}")
    df = pd.read_csv(latest_file)
    
    # Extract maze name and size from maze_file
    df['maze_name'] = df['maze_file'].str.replace('.json', '').str.replace('test_mazes/maze_', '')
    df['size'] = df['maze_name'].str.extract(r'(\d+)').astype(int)
    df['pattern'] = df['maze_name'].str.replace(r'^\d+_', '', regex=True)
    
    return df

def plot_heuristic_comparison(df):
    """Compare Euclidean vs Manhattan heuristics pairwise for same mazes"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Euclidean vs Manhattan Heuristic Comparison (Same Maze)', fontsize=16, fontweight='bold')
    
    # Pivot data for pairwise comparison
    df_pivot_time = df.pivot_table(values='time', index='maze_name', columns='heuristic')
    df_pivot_nodes = df.pivot_table(values='nodes_explored', index='maze_name', columns='heuristic')
    df_pivot_cost = df.pivot_table(values='cost', index='maze_name', columns='heuristic')
    
    # 1. Time comparison scatter
    axes[0, 0].scatter(df_pivot_time['euclidean'], df_pivot_time['manhattan'], alpha=0.6, s=100)
    max_time = max(df_pivot_time['euclidean'].max(), df_pivot_time['manhattan'].max())
    axes[0, 0].plot([0, max_time], [0, max_time], 'r--', label='Equal performance')
    axes[0, 0].set_xlabel('Euclidean Time (s)', fontsize=12)
    axes[0, 0].set_ylabel('Manhattan Time (s)', fontsize=12)
    axes[0, 0].set_title('Execution Time Comparison', fontsize=14)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Nodes explored comparison scatter
    axes[0, 1].scatter(df_pivot_nodes['euclidean'], df_pivot_nodes['manhattan'], alpha=0.6, s=100, color='green')
    max_nodes = max(df_pivot_nodes['euclidean'].max(), df_pivot_nodes['manhattan'].max())
    axes[0, 1].plot([0, max_nodes], [0, max_nodes], 'r--', label='Equal performance')
    axes[0, 1].set_xlabel('Euclidean Nodes Explored', fontsize=12)
    axes[0, 1].set_ylabel('Manhattan Nodes Explored', fontsize=12)
    axes[0, 1].set_title('Nodes Explored Comparison', fontsize=14)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Time difference by maze
    time_diff = df_pivot_time['manhattan'] - df_pivot_time['euclidean']
    time_diff_sorted = time_diff.sort_values()
    colors = ['red' if x < 0 else 'blue' for x in time_diff_sorted]
    axes[1, 0].barh(range(len(time_diff_sorted)), time_diff_sorted, color=colors, alpha=0.7)
    axes[1, 0].set_yticks(range(len(time_diff_sorted)))
    axes[1, 0].set_yticklabels(time_diff_sorted.index, fontsize=8)
    axes[1, 0].axvline(x=0, color='black', linestyle='-', linewidth=0.8)
    axes[1, 0].set_xlabel('Time Difference (Manhattan - Euclidean) (s)', fontsize=12)
    axes[1, 0].set_title('Time Difference by Maze\n(Blue: Manhattan slower, Red: Manhattan faster)', fontsize=14)
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # 4. Cost comparison
    axes[1, 1].scatter(df_pivot_cost['euclidean'], df_pivot_cost['manhattan'], alpha=0.6, s=100, color='purple')
    max_cost = max(df_pivot_cost['euclidean'].max(), df_pivot_cost['manhattan'].max())
    axes[1, 1].plot([0, max_cost], [0, max_cost], 'r--', label='Equal cost')
    axes[1, 1].set_xlabel('Euclidean Path Cost', fontsize=12)
    axes[1, 1].set_ylabel('Manhattan Path Cost', fontsize=12)
    axes[1, 1].set_title('Path Cost Comparison', fontsize=14)
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('heuristic_comparison.png', dpi=300, bbox_inches='tight')
    print("Saved: heuristic_comparison.png")
    plt.show()

def plot_size_comparison(df):
    """Compare runtime across different grid sizes"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Performance by Grid Size', fontsize=16, fontweight='bold')
    
    # 1. Average time by size
    avg_time = df.groupby(['size', 'heuristic'])['time'].mean().reset_index()
    for heuristic in ['euclidean', 'manhattan']:
        data = avg_time[avg_time['heuristic'] == heuristic]
        axes[0, 0].plot(data['size'], data['time'], marker='o', linewidth=2, markersize=10, label=heuristic.capitalize())
    axes[0, 0].set_xlabel('Grid Size', fontsize=12)
    axes[0, 0].set_ylabel('Average Time (s)', fontsize=12)
    axes[0, 0].set_title('Average Execution Time by Size', fontsize=14)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Average nodes explored by size
    avg_nodes = df.groupby(['size', 'heuristic'])['nodes_explored'].mean().reset_index()
    for heuristic in ['euclidean', 'manhattan']:
        data = avg_nodes[avg_nodes['heuristic'] == heuristic]
        axes[0, 1].plot(data['size'], data['nodes_explored'], marker='s', linewidth=2, markersize=10, label=heuristic.capitalize())
    axes[0, 1].set_xlabel('Grid Size', fontsize=12)
    axes[0, 1].set_ylabel('Average Nodes Explored', fontsize=12)
    axes[0, 1].set_title('Average Nodes Explored by Size', fontsize=14)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Box plot of time by size
    df_filtered = df[df['time'] < df['time'].quantile(0.95)]  # Remove outliers for better viz
    sns.boxplot(data=df_filtered, x='size', y='time', hue='heuristic', ax=axes[1, 0])
    axes[1, 0].set_xlabel('Grid Size', fontsize=12)
    axes[1, 0].set_ylabel('Time (s)', fontsize=12)
    axes[1, 0].set_title('Time Distribution by Size', fontsize=14)
    axes[1, 0].legend(title='Heuristic')
    
    # 4. Time vs nodes scatter by size
    for size in sorted(df['size'].unique()):
        data = df[df['size'] == size]
        axes[1, 1].scatter(data['nodes_explored'], data['time'], label=f'{size}x{size}', alpha=0.6, s=80)
    axes[1, 1].set_xlabel('Nodes Explored', fontsize=12)
    axes[1, 1].set_ylabel('Time (s)', fontsize=12)
    axes[1, 1].set_title('Time vs Nodes by Grid Size', fontsize=14)
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('size_comparison.png', dpi=300, bbox_inches='tight')
    print("Saved: size_comparison.png")
    plt.show()

def plot_pattern_comparison(df):
    """Compare different maze patterns within each size"""
    sizes = sorted(df['size'].unique())
    
    fig, axes = plt.subplots(len(sizes), 2, figsize=(16, 6*len(sizes)))
    if len(sizes) == 1:
        axes = axes.reshape(1, -1)
    
    fig.suptitle('Performance by Maze Pattern', fontsize=16, fontweight='bold')
    
    for idx, size in enumerate(sizes):
        df_size = df[df['size'] == size]
        
        # 1. Nodes explored by pattern
        pattern_nodes = df_size.groupby(['pattern', 'heuristic'])['nodes_explored'].mean().reset_index()
        pattern_nodes_pivot = pattern_nodes.pivot(index='pattern', columns='heuristic', values='nodes_explored')
        pattern_nodes_pivot.plot(kind='bar', ax=axes[idx, 0], width=0.8)
        axes[idx, 0].set_xlabel('Maze Pattern', fontsize=12)
        axes[idx, 0].set_ylabel('Average Nodes Explored', fontsize=12)
        axes[idx, 0].set_title(f'Nodes Explored by Pattern (Size: {size}x{size})', fontsize=14)
        axes[idx, 0].legend(title='Heuristic')
        axes[idx, 0].tick_params(axis='x', rotation=45)
        axes[idx, 0].grid(True, alpha=0.3, axis='y')
        
        # 2. Runtime by pattern
        pattern_time = df_size.groupby(['pattern', 'heuristic'])['time'].mean().reset_index()
        pattern_time_pivot = pattern_time.pivot(index='pattern', columns='heuristic', values='time')
        pattern_time_pivot.plot(kind='bar', ax=axes[idx, 1], width=0.8, color=['coral', 'skyblue'])
        axes[idx, 1].set_xlabel('Maze Pattern', fontsize=12)
        axes[idx, 1].set_ylabel('Average Time (s)', fontsize=12)
        axes[idx, 1].set_title(f'Runtime by Pattern (Size: {size}x{size})', fontsize=14)
        axes[idx, 1].legend(title='Heuristic')
        axes[idx, 1].tick_params(axis='x', rotation=45)
        axes[idx, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('pattern_comparison.png', dpi=300, bbox_inches='tight')
    print("Saved: pattern_comparison.png")
    plt.show()

def print_summary_statistics(df):
    """Print summary statistics"""
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY STATISTICS")
    print("="*80)
    
    print("\n1. Overall Performance by Heuristic:")
    print("-" * 80)
    summary = df.groupby('heuristic').agg({
        'time': ['mean', 'std', 'min', 'max'],
        'nodes_explored': ['mean', 'std', 'min', 'max'],
        'cost': ['mean', 'std', 'min', 'max']
    }).round(4)
    print(summary)
    
    print("\n2. Performance by Size:")
    print("-" * 80)
    size_summary = df.groupby(['size', 'heuristic']).agg({
        'time': 'mean',
        'nodes_explored': 'mean',
        'cost': 'mean'
    }).round(4)
    print(size_summary)
    
    print("\n3. Performance by Pattern:")
    print("-" * 80)
    pattern_summary = df.groupby(['pattern', 'heuristic']).agg({
        'time': 'mean',
        'nodes_explored': 'mean',
        'cost': 'mean'
    }).round(4)
    print(pattern_summary)
    
    print("\n4. Winner Count (Faster Heuristic per Maze):")
    print("-" * 80)
    df_pivot = df.pivot_table(values='time', index='maze_name', columns='heuristic')
    euclidean_wins = (df_pivot['euclidean'] < df_pivot['manhattan']).sum()
    manhattan_wins = (df_pivot['manhattan'] < df_pivot['euclidean']).sum()
    ties = (df_pivot['euclidean'] == df_pivot['manhattan']).sum()
    print(f"Euclidean faster: {euclidean_wins}")
    print(f"Manhattan faster: {manhattan_wins}")
    print(f"Ties: {ties}")
    
    print("\n" + "="*80)

def main():
    """Main visualization function"""
    print("A* Benchmark Results Visualizer")
    print("="*80)
    
    # Load data
    df = load_latest_benchmark()
    if df is None:
        return
    
    print(f"\nLoaded {len(df)} benchmark results")
    print(f"Unique mazes: {df['maze_name'].nunique()}")
    print(f"Grid sizes: {sorted(df['size'].unique())}")
    print(f"Patterns: {sorted(df['pattern'].unique())}")
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    print("-" * 80)
    
    plot_heuristic_comparison(df)
    plot_size_comparison(df)
    plot_pattern_comparison(df)
    
    # Print statistics
    print_summary_statistics(df)
    
    print("\n✓ All visualizations complete!")
    print("Generated files:")
    print("  - heuristic_comparison.png")
    print("  - size_comparison.png")
    print("  - pattern_comparison.png")

if __name__ == "__main__":
    main()
