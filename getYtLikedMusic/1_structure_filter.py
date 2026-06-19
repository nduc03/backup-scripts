import os
import json
import chompjs

def extract_video_info(item):
    if 'lockupViewModel' not in item:
        return None
    
    vm = item['lockupViewModel']
    video_id = vm.get('contentId')
    
    lmvm = vm.get('metadata', {}).get('lockupMetadataViewModel', {})
    title = lmvm.get('title', {}).get('content')
    
    channel = None
    
    meta_vm = lmvm.get('metadata', {}).get('contentMetadataViewModel', {})
    rows = meta_vm.get('metadataRows', [])
    
    if len(rows) > 0:
        parts = rows[0].get('metadataParts', [])
        if len(parts) > 0:
            channel = parts[0].get('text', {}).get('content')
            
    # Extract duration from thumbnail overlays
    duration = None
    overlays = vm.get('contentImage', {}).get('thumbnailViewModel', {}).get('overlays', [])
    for overlay in overlays:
        if 'thumbnailBottomOverlayViewModel' in overlay:
            badges = overlay['thumbnailBottomOverlayViewModel'].get('badges', [])
            for badge in badges:
                if 'thumbnailBadgeViewModel' in badge:
                    text_val = badge['thumbnailBadgeViewModel'].get('text')
                    if text_val:
                        duration = text_val
                        break
            if duration:
                break
                
    return {
        'videoId': video_id,
        'title': title,
        'channel': channel,
        'duration': duration
    }

def main():
    # Define paths
    workspace_dir = '.'
    input_dir = os.path.join(workspace_dir, 'ytLikedVideo')
    output_dir = os.path.join(workspace_dir, 'filtered')
    
    # 1. Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory initialized at: {output_dir}")
    
    # 2. Parse Page 1 (HTML file)
    html_path = os.path.join(input_dir, 'likedvideo.html')
    print(f"Step 1: Parsing page 1 (HTML) from {html_path}...")
    
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        start_marker = "var ytInitialData = "
        start_idx = html_content.find(start_marker)
        if start_idx != -1:
            # Extract JS string starting from the object declaration
            js_part = html_content[start_idx + len(start_marker):]
            
            # Fix the `{ytInit` typo/corruption
            js_part_fixed = js_part.replace("{ytInit", "{")
            
            try:
                data = chompjs.parse_js_object(js_part_fixed)
                # Try navigating different potential paths for ytInitialData contents
                contents = None
                
                # Check path 1: standard contents
                if 'contents' in data:
                    contents = data['contents']
                # Check path 2: responseContext.contents (as mentioned in request details, just in case)
                elif 'responseContext' in data and 'contents' in data['responseContext']:
                    contents = data['responseContext']['contents']
                    
                if contents:
                    try:
                        # contents.twoColumnBrowseResultsRenderer.tabs[0].tabRenderer.content.sectionListRenderer.contents[0].itemSectionRenderer.contents
                        path_data = contents['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
                        
                        page1_items = []
                        for item in path_data:
                            extracted = extract_video_info(item)
                            if extracted:
                                page1_items.append(extracted)
                                
                        output_path = os.path.join(output_dir, 'page1.json')
                        with open(output_path, 'w', encoding='utf-8') as out_f:
                            json.dump(page1_items, out_f, indent=2, ensure_ascii=False)
                        print(f"Successfully wrote {len(page1_items)} items to {output_path}")
                    except KeyError as ke:
                        print(f"Error navigating deep path in page 1 data: {ke}")
                else:
                    print("Error: Could not locate 'contents' object in ytInitialData")
            except Exception as e:
                print(f"Error parsing JS block with chompjs: {e}")
        else:
            print("Error: Could not find 'var ytInitialData = ' in HTML file")
    else:
        print(f"Error: {html_path} does not exist!")

    # 3. Parse Pages 2-10 (JSON files)
    print("Step 2: Parsing pages 2-10 (JSON)...")
    for page_num in range(2, 11):
        json_file_name = f"likedvideoPage{page_num}.json"
        json_path = os.path.join(input_dir, json_file_name)
        
        if os.path.exists(json_path):
            print(f"Parsing page {page_num} from {json_path}...")
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Access items at onResponseReceivedActions[0].appendContinuationItemsAction.continuationItems
                actions = json_data.get('onResponseReceivedActions', [])
                if actions and len(actions) > 0:
                    action = actions[0]
                    items = action.get('appendContinuationItemsAction', {}).get('continuationItems', [])
                    
                    page_items = []
                    for item in items:
                        extracted = extract_video_info(item)
                        if extracted:
                            page_items.append(extracted)
                            
                    output_path = os.path.join(output_dir, f"page{page_num}.json")
                    with open(output_path, 'w', encoding='utf-8') as out_f:
                        json.dump(page_items, out_f, indent=2, ensure_ascii=False)
                    print(f"Successfully wrote {len(page_items)} items to {output_path}")
                else:
                    print(f"Warning: 'onResponseReceivedActions' not found or empty in page {page_num} JSON")
            except Exception as e:
                print(f"Error parsing page {page_num} JSON: {e}")
        else:
            print(f"Warning: {json_path} does not exist, skipping page {page_num}")

if __name__ == '__main__':
    main()
