import csv
import json
from pathlib import Path

folder_path = "."

# Tên file CSV đầu ra duy nhất
output_file = "appleMusic_likedPlaylist_exported.csv"
headers = ["Song", "Artist", "Album"]

# Mảng trung gian để gom toàn bộ bài hát từ tất cả các file
all_songs = {}

folder = Path(folder_path)
json_files = sorted(folder.glob("*.json"))

print("🚀 Bắt đầu quá trình gộp dữ liệu...")

# 2. VÒNG LẶP ĐỌC TỪNG FILE JSON
for index, file_path in enumerate(json_files, start=1):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Truy cập cấu trúc JSON
        library_songs = data.get("resources", {}).get("library-songs", {})

        # Đếm số bài hát bóc tách được từ file này
        songs_in_file = 0

        # Lặp qua từng obj nhạc trong file hiện tại
        for song_id, song_obj in library_songs.items():
            # Lấy các trường thông tin nằm trong attributes (đã sửa trường name)
            attributes = song_obj.get("attributes", {})
            song_name = attributes.get("name", "")
            artist_name = attributes.get("artistName", "")
            album_name = attributes.get("albumName", "")

            # Kiểm tra phòng hờ dữ liệu rác, nếu có tên bài hát thì mới lấy
            if song_name:
                all_songs[song_id] = {
                    "Song": song_name,
                    "Artist": artist_name,
                    "Album": album_name,
                }
                songs_in_file += 1

        print(
            f"  🔹 File {index}: Đã bóc thành công {songs_in_file} bài từ '{file_path}'"
        )

    except FileNotFoundError:
        print(f"  ❌ File {index}: Không tìm thấy file tại '{file_path}'. Bỏ qua.")
    except Exception as e:
        print(f"  ❌ File {index}: Có lỗi xảy ra khi đọc file này: {e}")

# 3. GHI TOÀN BỘ DỮ LIỆU ĐÃ GÔM ĐƯỢC VÀO FILE CSV DUY NHẤT
if all_songs:
    try:
        with open(output_file, "w", newline="", encoding="utf-8-sig") as csv_file:
            # Dùng 'utf-8-sig' để Excel hiển thị đúng tiếng Việt và ký tự đặc biệt
            writer = csv.DictWriter(csv_file, fieldnames=headers)

            # Ghi hàng tiêu đề (chỉ ghi 1 lần duy nhất ở đầu file)
            writer.writeheader()

            # Ghi hàng loạt tất cả bài hát thu thập được từ tất cả các file
            writer.writerows(all_songs.values())

        print("-" * 50)
        print(
            f"🎉 THÀNH CÔNG! Đã gộp tổng cộng {len(all_songs)} bài hát từ {len(json_files)} file JSON."
        )
        print(f"💾 Dữ liệu sạch đã được lưu tại: '{output_file}'")

    except Exception as e:
        print(f"❌ Không thể ghi file CSV: {e}")
else:
    print("⚠️ Không thu thập được dữ liệu nào từ các file JSON đã cung cấp.")