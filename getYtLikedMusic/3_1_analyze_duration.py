import os
import json
import sys
import matplotlib.pyplot as plt

def parse_duration_to_seconds(duration_str):
    if not duration_str or not isinstance(duration_str, str):
        return None
    parts = duration_str.strip().split(':')
    try:
        if len(parts) == 1:
            return int(parts[0])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return None
    return None

def round_seconds_to_minutes(total_seconds):
    if total_seconds is None:
        return None
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    # "the second under 29 will be round down and above 30 will be round up"
    # Under 29 means <= 29. Above 30 means >= 30.
    if seconds <= 29:
        return minutes

    return minutes + 1

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    workspace_dir = '.'
    output_dir = os.path.join(workspace_dir, 'output')
    input_json_path = os.path.join(output_dir, 'likedMusicPass3.json')
    output_img_path = os.path.join(output_dir, 'duration.png')

    if not os.path.exists(input_json_path):
        print(f"Error: {input_json_path} not found.")
        return

    print(f"Reading from {input_json_path}...")
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"Error: Expected a JSON array in {input_json_path}")
        return

    # Count frequencies for 0 to 9 minutes, and group 10+ minutes
    max_discrete_minutes = 9
    counts = {m: 0 for m in range(max_discrete_minutes + 1)}
    outliers_count = 0
    skipped_count = 0
    outliers_details = []

    for item in data:
        duration_str = item.get('duration')
        if not duration_str:
            skipped_count += 1
            continue

        seconds = parse_duration_to_seconds(duration_str)
        if seconds is None:
            skipped_count += 1
            continue

        rounded_minutes = round_seconds_to_minutes(seconds)

        if rounded_minutes <= max_discrete_minutes:
            counts[rounded_minutes] += 1
        else:
            outliers_count += 1
            outliers_details.append((item.get('title'), duration_str, rounded_minutes))

    # Print summary
    print(f"Processed {len(data) - skipped_count} songs. Skipped {skipped_count} songs.")
    print("Duration Distribution:")
    for m in range(max_discrete_minutes + 1):
        print(f"  {m} min: {counts[m]} songs")
    print(f"  10+ min: {outliers_count} songs")
    if outliers_count > 0:
        print("Outliers (10+ min):")
        for title, dur, rounded in sorted(outliers_details, key=lambda x: x[2], reverse=True):
            print(f"  - '{title}' ({dur} -> rounded to {rounded}m)")

    # Prepare data for plotting
    categories = [f"{m}m" for m in range(max_discrete_minutes + 1)] + ["10m+"]
    song_counts = [counts[m] for m in range(max_discrete_minutes + 1)] + [outliers_count]

    # --- VALIDATION ---
    print("\n--- Validation ---")
    total_plotted = sum(song_counts)
    total_valid = len(data) - skipped_count
    print(f"Total songs in chart: {total_plotted}")
    print(f"Total valid songs parsed: {total_valid}")
    if total_plotted == total_valid:
        print("✅ Validation PASSED: Chart data matches JSON data perfectly.")
    else:
        print(f"❌ Validation FAILED: Chart has {total_plotted} songs, but JSON has {total_valid} valid songs.")

    # Let's also do a double-check by re-counting manually from the raw data
    validation_counts = 0
    for item in data:
        dur = item.get('duration')
        if dur and parse_duration_to_seconds(dur) is not None:
            validation_counts += 1

    if total_plotted == validation_counts:
        print("✅ Validation PASSED: Manual re-count of valid durations matches chart data.")
    else:
        print(f"❌ Validation FAILED: Manual re-count found {validation_counts} valid durations.")
    print("------------------\n")

    # Plot aesthetics: Modern Dark Theme
    plt.style.use('dark_background')

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    fig.patch.set_facecolor('#0d0e12')
    ax.set_facecolor('#0d0e12')

    # Color gradient for the bars: from deep purple (for short) to vibrant cyan/blue (for typical)
    # We use a custom color list for an elegant aesthetic
    # Indigo/violet gradients
    bar_colors = [
        '#4f46e5',  # 0m
        '#6366f1',  # 1m
        '#818cf8',  # 2m
        '#a5b4fc',  # 3m
        '#c7d2fe',  # 4m
        '#e0e7ff',  # 5m
        '#a78bfa',  # 6m
        '#8b5cf6',  # 7m
        '#7c3aed',  # 8m
        '#6d28d9',  # 9m
        '#4c1d95',  # 10m+
    ]

    bars = ax.bar(categories, song_counts, color=bar_colors, edgecolor='#1e1b4b', linewidth=1, width=0.7, alpha=0.9)

    # Grid styling
    ax.grid(True, which='both', color='#1f2937', linestyle='--', linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)

    # Labels and Titles
    ax.set_title('Distribution of Liked Music Durations', fontsize=18, fontweight='bold', pad=20, color='#ffffff')
    ax.set_xlabel('Duration (Rounded to Nearest Minute)', fontsize=12, labelpad=12, color='#9ca3af')
    ax.set_ylabel('Number of Songs', fontsize=12, labelpad=12, color='#9ca3af')

    # Tick formatting
    plt.xticks(fontsize=10, color='#9ca3af')
    plt.yticks(fontsize=10, color='#9ca3af')

    # Remove top and right spines
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.spines['left'].set_color('#1f2937')
    ax.spines['bottom'].set_color('#1f2937')

    # Add count labels on top of each bar (only if count > 0)
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{height}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4),  # 4 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='semibold', color='#f3f4f6')

    plt.tight_layout()

    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(output_img_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()

    print(f"Successfully generated plot at {output_img_path}")

if __name__ == '__main__':
    main()
