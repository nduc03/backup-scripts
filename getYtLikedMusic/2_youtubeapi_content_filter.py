import os
import json
from googleapiclient.discovery import build

# Curated YouTube Topic IDs for Music
MUSIC_TOPIC_IDS = {
    '/m/04rlf',   # Music (parent topic)
    '/m/02mscn',  # Christian music
    '/m/03t3_',   # Classical music
    '/m/01lyv',   # Country music
    '/m/02lkt',   # Electronic music
    '/m/064t9',   # Hip hop music
    '/m/05rwpb',  # Independent music
    '/m/03_d0',   # Jazz
    '/m/0g293',   # Music of Asia
    '/m/028sqc',  # Music of Latin America
    '/m/02wscf',  # Pop music
    '/m/07yv9',   # Reggae
    '/m/06by7',   # Rock music
    '/m/07gcr'    # Soul music
}

def main():
    # 1. Read API Key
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY environment variable is not set. Please set the environment variable and run the script again.")
        
    workspace_dir = '.'
    filtered_dir = os.path.join(workspace_dir, 'filtered')
    output_dir = os.path.join(workspace_dir, 'output')
    
    # 2. Combine all pages
    print("Step 1: Combining page files...")
    all_videos = []
    for page_num in range(1, 11):
        file_path = os.path.join(filtered_dir, f"page{page_num}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                videos = json.load(f)
                all_videos.extend(videos)
        else:
            print(f"Warning: {file_path} does not exist, skipping page {page_num}")
            
    print(f"Total videos to check: {len(all_videos)}")
    
    # Extract unique video IDs to query API
    unique_video_ids = []
    seen_ids = set()
    for video in all_videos:
        vid = video.get('videoId')
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            unique_video_ids.append(vid)
            
    print(f"Total unique video IDs: {len(unique_video_ids)}")
    
    # 3. Batch API Requests (50 at a time)
    print("Step 2: Batch querying YouTube Data API...")
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    music_video_ids = set()
    
    batch_size = 50
    for i in range(0, len(unique_video_ids), batch_size):
        batch = unique_video_ids[i:i + batch_size]
        ids_str = ",".join(batch)
        
        print(f"Querying batch {i//batch_size + 1}/{(len(unique_video_ids) - 1)//batch_size + 1} ({len(batch)} IDs)...")
        try:
            response = youtube.videos().list(
                part='snippet,topicDetails',
                id=ids_str
            ).execute()
            
            for item in response.get('items', []):
                vid = item.get('id')
                snippet = item.get('snippet', {})
                category_id = snippet.get('categoryId')
                
                topic_details = item.get('topicDetails', {})
                topic_ids = topic_details.get('topicIds', [])
                relevant_topic_ids = topic_details.get('relevantTopicIds', [])
                all_topics = set(topic_ids + relevant_topic_ids)
                
                # Filter criteria: Official Music Category (10) or any Music topic ID
                is_music = False
                if category_id == '10':
                    is_music = True
                elif all_topics.intersection(MUSIC_TOPIC_IDS):
                    is_music = True
                    
                if is_music:
                    music_video_ids.add(vid)
                    
        except Exception as e:
            print(f"Error querying batch starting at index {i}: {e}")
            
    # 4. Filter original list preserving order
    print("Step 3: Filtering combined list and saving output...")
    filtered_music_videos = [
        video for video in all_videos if video.get('videoId') in music_video_ids
    ]
    filtered_out_videos = [
        video for video in all_videos if video.get('videoId') not in music_video_ids
    ]
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save music videos
    output_path = os.path.join(output_dir, 'likedMusic.json')
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(filtered_music_videos, out_f, indent=2, ensure_ascii=False)
        
    # Save filtered out videos
    filtered_out_path = os.path.join(output_dir, 'filtered_out.json')
    with open(filtered_out_path, 'w', encoding='utf-8') as out_f:
        json.dump(filtered_out_videos, out_f, indent=2, ensure_ascii=False)
        
    print(f"Successfully wrote {len(filtered_music_videos)} music videos to {output_path}")
    print(f"Successfully wrote {len(filtered_out_videos)} filtered out videos to {filtered_out_path}")

if __name__ == '__main__':
    main()
