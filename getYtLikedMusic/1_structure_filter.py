import os
import json
import chompjs
import glob
import re

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


def parse_first_page(input_dir, output_dir):
    html_path = os.path.join(input_dir, 'likedvideo.html')
    print(f"Step 1: Parsing page 1 (HTML) from {html_path}...")

    if not os.path.exists(html_path):
        print(f"Error: {html_path} does not exist!")
        return

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    start_marker = "var ytInitialData = "
    start_idx = html_content.find(start_marker)

    if start_idx == -1:
        print("Error: Could not find 'var ytInitialData = ' in HTML file")
        return

    js_part = html_content[start_idx + len(start_marker):]

    try:
        data = chompjs.parse_js_object(js_part)
    except Exception as e:
        print(f"Error parsing JS block with chompjs: {e}")
        return

    contents = data.get('contents') or data.get('responseContext', {}).get('contents')

    if not contents:
        print("Error: Could not locate 'contents' object in ytInitialData")
        return

    try:
        path_data = contents['twoColumnBrowseResultsRenderer']['tabs'][0] \
                ['tabRenderer']['content']['sectionListRenderer']['contents'][0] \
                ['itemSectionRenderer']['contents']

        page1_items = [
            extracted for item in path_data
            if (extracted := extract_video_info(item))
        ]

        # Write output file
        output_path = os.path.join(output_dir, 'page1.json')
        with open(output_path, 'w', encoding='utf-8') as out_f:
            json.dump(page1_items, out_f, indent=2, ensure_ascii=False)

        print(f"Successfully wrote {len(page1_items)} items to {output_path}")

    except KeyError as ke:
        print(f"Error navigating deep path in page 1 data: {ke}")


def parse_json_pages(input_dir, output_dir):
    print("Step 2: Scanning and parsing all available likedvideoPage JSON files...")

    # 1. Dynamically find all matching paths
    search_pattern = os.path.join(input_dir, "likedvideoPage*.json")
    json_paths = glob.glob(search_pattern)

    if not json_paths:
        print(f"No files matching 'likedvideoPage*.json' found in {input_dir}.")
        return

    # 2. Extract page numbers and sort files numerically so they process in order (Page 2, Page 3, etc.)
    # Files will be stored as tuples: (page_num, file_path)
    ordered_files = []
    for path in json_paths:
        filename = os.path.basename(path)
        # Use regex to find digits following 'likedvideoPage'
        match = re.search(r"likedvideoPage(\d+)\.json", filename)
        if match:
            page_num = int(match.group(1))
            ordered_files.append((page_num, path))

    # Sort by the page number (the first element of the tuple)
    ordered_files.sort()

    # 3. Process the sorted files dynamically
    for page_num, json_path in ordered_files:
        print(f"Parsing page {page_num} from {json_path}...")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"Error parsing page {page_num} JSON: {e}")
            continue

        actions = json_data.get('onResponseReceivedActions', [])
        if not actions:
            print(f"Warning: 'onResponseReceivedActions' not found or empty in page {page_num} JSON")
            continue

        items = actions[0].get('appendContinuationItemsAction', {}).get('continuationItems', [])

        page_items = [
            extracted for item in items
            if (extracted := extract_video_info(item))
        ]

        output_path = os.path.join(output_dir, f"page{page_num}.json")
        with open(output_path, 'w', encoding='utf-8') as out_f:
            json.dump(page_items, out_f, indent=2, ensure_ascii=False)

        print(f"Successfully wrote {len(page_items)} items to {output_path}")


def main():
    # Define paths
    workspace_dir = '.'
    input_dir = os.path.join(workspace_dir, 'ytLikedVideo')
    output_dir = os.path.join(workspace_dir, 'filtered')

    # 1. Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory initialized at: {output_dir}")

    # 2. Parse Page 1 (HTML file)
    parse_first_page(input_dir, output_dir)

    # 3. Parse Pages 2-10 (JSON files)
    parse_json_pages(input_dir, output_dir)

if __name__ == '__main__':
    main()
