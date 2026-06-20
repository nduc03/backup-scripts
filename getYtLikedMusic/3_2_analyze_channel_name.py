import os
import sys
import json
import matplotlib.pyplot as plt
from collections import Counter

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    workspace_dir = '.'
    output_dir = os.path.join(workspace_dir, 'output')
    input_json_path = os.path.join(output_dir, 'likedMusicPass3.json')
    output_img_path = os.path.join(output_dir, 'channel_distribution.png')
    
    if not os.path.exists(input_json_path):
        print(f"Error: {input_json_path} not found.")
        return

    print(f"Reading from {input_json_path}...")
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"Error: Expected a JSON array in {input_json_path}")
        return

    channels = []
    skipped_count = 0

    for item in data:
        channel = item.get('channel')
        if not channel or not channel.strip():
            skipped_count += 1
            continue
        channels.append(channel.strip())

    print(f"Processed {len(channels)} valid channel entries. Skipped {skipped_count} items with missing/empty channels.")

    if not channels:
        print("No valid channels found to plot.")
        return

    # Count frequencies
    counts = Counter(channels)
    
    # Sort from highest to lowest
    sorted_counts = counts.most_common()
    
    # Top 9 + Others
    top_n = 9
    top_channels = sorted_counts[:top_n]
    others = sorted_counts[top_n:]
    
    others_count = sum(count for _, count in others)
    
    # Prepare plotting data
    labels = [name for name, _ in top_channels]
    values = [count for _, count in top_channels]
    
    if others_count > 0:
        labels.append("Others")
        values.append(others_count)

    # --- VALIDATION ---
    print("\n--- Validation ---")
    total_plotted = sum(values)
    total_valid = len(channels)
    print(f"Total entries in chart: {total_plotted}")
    print(f"Total valid entries parsed: {total_valid}")
    if total_plotted == total_valid:
        print("✅ Validation PASSED: Chart data matches JSON data perfectly.")
    else:
        print(f"❌ Validation FAILED: Chart has {total_plotted} entries, but JSON has {total_valid} valid entries.")
    print("------------------\n")

    # Plot aesthetics: Modern Dark Theme
    plt.style.use('dark_background')
    
    # Use a horizontal bar chart because channel names can be long
    fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor('#0d0e12')
    ax.set_facecolor('#0d0e12')

    # Color gradient for the bars
    # Let's use a nice teal to green gradient or similar
    bar_colors = [
        '#0f766e', '#0d9488', '#14b8a6', '#2dd4bf', '#5eead4', 
        '#99f6e4', '#ccfbf1', '#f0fdfa', '#ffffff', '#3f3f46' # Others is grey
    ]
    
    # We need to reverse the order for plotting so highest is at the top
    labels.reverse()
    values.reverse()
    bar_colors = bar_colors[:len(labels)]
    bar_colors.reverse()

    bars = ax.barh(labels, values, color=bar_colors, edgecolor='#1e1b4b', linewidth=1, height=0.7, alpha=0.9)

    # Grid styling
    ax.grid(True, axis='x', color='#1f2937', linestyle='--', linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)

    # Labels and Titles
    ax.set_title('Top 9 Channels + Others', fontsize=20, fontweight='bold', pad=20, color='#ffffff')
    ax.set_xlabel('Number of Songs', fontsize=14, labelpad=12, color='#9ca3af')
    # No ylabel needed since the labels themselves are descriptive

    # Tick formatting
    plt.xticks(fontsize=11, color='#9ca3af')
    plt.yticks(fontsize=12, fontweight='medium', color='#f3f4f6')

    # Remove top and right spines
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.spines['left'].set_color('#1f2937')
    ax.spines['bottom'].set_color('#1f2937')

    # Add count labels at the end of each bar
    for bar in bars:
        width = bar.get_width()
        if width > 0:
            ax.annotate(f'{width}',
                        xy=(width, bar.get_y() + bar.get_height() / 2),
                        xytext=(5, 0),  # 5 points horizontal offset
                        textcoords="offset points",
                        ha='left', va='center', fontsize=11, fontweight='semibold', color='#f3f4f6')

    # Increase margin on the right to make room for the annotations
    ax.margins(x=0.1)

    plt.tight_layout()
    
    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(output_img_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()
    
    print(f"Successfully generated plot at {output_img_path}")

if __name__ == '__main__':
    main()
