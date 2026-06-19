import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class MusicResponse(BaseModel):
    music_titles: list[str] = Field(description="The exact titles of the videos classified as music")

def main():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it to use the AI filter.")

    model = os.environ.get('GEMINI_MODEL', 'gemini-3.1-flash-lite')

    client = genai.Client(api_key=api_key)

    workspace_dir = '.'
    output_dir = os.path.join(workspace_dir, 'output')
    filtered_out_path = os.path.join(output_dir, 'filtered_out.json')
    liked_music_path = os.path.join(output_dir, 'likedMusic.json')

    if not os.path.exists(filtered_out_path):
        print(f"{filtered_out_path} not found, nothing to process.")
        return

    with open(filtered_out_path, 'r', encoding='utf-8') as f:
        filtered_out_videos = json.load(f)

    liked_music_videos = []
    if os.path.exists(liked_music_path):
        with open(liked_music_path, 'r', encoding='utf-8') as f:
            liked_music_videos = json.load(f)

    liked_music_pass2 = list(liked_music_videos)
    filtered_out_pass2 = []

    batch_size = 30
    for i in range(0, len(filtered_out_videos), batch_size):
        batch = filtered_out_videos[i:i + batch_size]
        
        # Prepare input for LLM: Remove videoId and duration to save tokens
        items_for_prompt = []
        for v in batch:
            items_for_prompt.append({
                "title": v.get("title"),
                "channel": v.get("channel")
            })

        print(f"Processing batch {i//batch_size + 1}/{(len(filtered_out_videos)-1)//batch_size + 1} ({len(batch)} videos)...")
        
        system_prompt = (
            "You are a strict YouTube video categorization assistant. "
            "Your task is to review the provided JSON array of videos and identify which ones are definitively MUSIC videos (songs, music tracks, official audio, lyric videos). "
            "You must be EXTREMELY conservative. Prefer false negatives. If a video is ambiguous, a podcast, an interview, a review, or a generic vlog that happens to feature music, classify it as NOT music. "
            "IMPORTANT: Your output must be a JSON array containing ONLY the EXACT 'title' strings of the videos you have classified as music. "
            "Do not alter the titles in any way. Do not return titles of videos that are not in the input list. If no videos are music, return an empty array."
        )

        user_prompt = json.dumps(items_for_prompt, ensure_ascii=False, indent=2)

        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=MusicResponse,
                    temperature=0.0
                )
            )

            # Use the parsed pydantic object directly if available, otherwise fallback to json.loads
            if getattr(response, 'parsed', None):
                music_titles = response.parsed.music_titles
            else:
                parsed_json = json.loads(response.text)
                music_titles = parsed_json.get("music_titles", [])
            
            matched_indices = set()
            
            for m_title in music_titles:
                found = False
                for idx, original_item in enumerate(batch):
                    if idx in matched_indices:
                        continue
                    if original_item.get("title") == m_title:
                        liked_music_pass2.append(original_item)
                        matched_indices.add(idx)
                        found = True
                        break
                
                if not found:
                    # Hallucination or typo by LLM: cannot be mapped back.
                    # Add to filtered out pass 2 without original info (no video id and duration)
                    filtered_out_pass2.append({
                        "title": m_title,
                        "error": "Failed to map AI output back to original item (title mismatch)"
                    })

            # Remaining items in batch that were not matched as music
            for idx, original_item in enumerate(batch):
                if idx not in matched_indices:
                    filtered_out_pass2.append(original_item)
                    
        except Exception as e:
            print(f"Error processing batch {i//batch_size + 1}: {e}")
            # Case where LLM has syntax error and cannot map back
            # Add these errors to filtered out pass 2 without original info (no video id and duration)
            print("Adding unmapped items to filtered_out_pass2 without videoId and duration due to error.")
            for item in items_for_prompt:
                filtered_out_pass2.append(item)

    # Save to disk
    os.makedirs(output_dir, exist_ok=True)
    liked_music_pass2_path = os.path.join(output_dir, 'likedMusicPass2.json')
    with open(liked_music_pass2_path, 'w', encoding='utf-8') as f:
        json.dump(liked_music_pass2, f, indent=2, ensure_ascii=False)

    filtered_out_pass2_path = os.path.join(output_dir, 'filtered_out_pass2.json')
    with open(filtered_out_pass2_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_out_pass2, f, indent=2, ensure_ascii=False)

    new_music_count = len(liked_music_pass2) - len(liked_music_videos)
    print(f"\nResults:")
    print(f"AI identified {new_music_count} missed music videos.")
    print(f"Successfully wrote {len(liked_music_pass2)} videos to {liked_music_pass2_path}")
    print(f"Successfully wrote {len(filtered_out_pass2)} videos to {filtered_out_pass2_path}")

if __name__ == "__main__":
    main()
