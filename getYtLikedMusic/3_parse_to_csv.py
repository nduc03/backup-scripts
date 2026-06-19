import os
import json
import csv

def main():
    workspace_dir = '.'
    output_dir = os.path.join(workspace_dir, 'output')
    
    input_json_path = os.path.join(output_dir, 'likedMusicPass3.json')
    output_csv_path = os.path.join(output_dir, 'likedMusic.csv')
    
    if not os.path.exists(input_json_path):
        print(f"Error: {input_json_path} not found. Please ensure you have completed the previous steps.")
        # Fallback for convenience if they skipped pass 3 but have pass 2
        fallback_path = os.path.join(output_dir, 'likedMusicPass2.json')
        if os.path.exists(fallback_path):
            print(f"Notice: Falling back to {fallback_path} instead.")
            input_json_path = fallback_path
        else:
            return

    print(f"Reading from {input_json_path}...")
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"Error: Expected a JSON array in {input_json_path}")
        return

    print(f"Writing to {output_csv_path}...")
    with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Write header with exactly the same name as json
        writer.writerow(['title', 'channel'])
        
        # Write rows
        row_count = 0
        for item in data:
            title = item.get('title', '')
            channel = item.get('channel', '')
            writer.writerow([title, channel])
            row_count += 1

    print(f"\nFinal Result: Successfully converted {row_count} videos to {output_csv_path}.")

if __name__ == "__main__":
    main()
