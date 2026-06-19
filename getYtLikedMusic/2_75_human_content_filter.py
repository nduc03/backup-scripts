import os
import json

def main():
    workspace_dir = '.'
    output_dir = os.path.join(workspace_dir, 'output')
    
    liked_music_pass2_path = os.path.join(output_dir, 'likedMusicPass2.json')
    filtered_out_pass2_path = os.path.join(output_dir, 'filtered_out_pass2.json')
    pass3_txt_path = os.path.join(output_dir, 'pass3.txt')
    liked_music_pass3_path = os.path.join(output_dir, 'likedMusicPass3.json')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure pass2 files exist
    if not os.path.exists(liked_music_pass2_path):
        print(f"Error: {liked_music_pass2_path} not found. Please run previous steps.")
        return
        
    with open(liked_music_pass2_path, 'r', encoding='utf-8') as f:
        liked_music_pass3 = json.load(f)
        
    # Read manual IDs
    manual_ids = set()
    if os.path.exists(pass3_txt_path):
        with open(pass3_txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                vid = line.strip()
                if vid:
                    manual_ids.add(vid)
    else:
        print(f"Notice: {pass3_txt_path} not found. Creating an empty one.")
        with open(pass3_txt_path, 'w', encoding='utf-8') as f:
            pass

    if not manual_ids:
        print("No manual video IDs found in pass3.txt. likedMusicPass3.json will be identical to likedMusicPass2.json.")
    
    # Extract original objects for the manual IDs
    if manual_ids and os.path.exists(filtered_out_pass2_path):
        with open(filtered_out_pass2_path, 'r', encoding='utf-8') as f:
            filtered_out_pass2 = json.load(f)
            
        found_count = 0
        for video in filtered_out_pass2:
            vid = video.get('videoId')
            # Handle cases where video object might not have videoId (e.g. LLM unmapped errors)
            if vid and vid in manual_ids:
                liked_music_pass3.append(video)
                found_count += 1
                manual_ids.remove(vid)
                
        if manual_ids:
            print(f"Treating {len(manual_ids)} unresolved lines from pass3.txt as raw titles.")
            for line_val in manual_ids:
                liked_music_pass3.append({
                    "title": line_val,
                    "channel": "UNKNOWN"
                })
            
        print(f"Successfully added {found_count} manually verified videos from pass3.txt by ID.")
        
    # Write output
    with open(liked_music_pass3_path, 'w', encoding='utf-8') as f:
        json.dump(liked_music_pass3, f, indent=2, ensure_ascii=False)
        
    print(f"\nFinal Result: Saved {len(liked_music_pass3)} videos to {liked_music_pass3_path}")

if __name__ == "__main__":
    main()
