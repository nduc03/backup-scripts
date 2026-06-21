import json
import random
import re
import shlex
import subprocess
import time
from pathlib import Path


def clean_curl_command(curl_string):
    """Làm sạch các dấu gạch chéo ngược '\\' nối dòng của Bash."""
    cleaned = curl_string.replace("\\\r\n", " ").replace("\\\n", " ")
    cleaned = " ".join(cleaned.split())
    return cleaned


def extract_playlist_id(curl_string):
    """Trích xuất ID playlist nằm sau 'playlists/' và trước dấu hỏi ? hoặc /."""
    match = re.search(r"/playlists/([^/?\'\"\s]+)", curl_string)
    if match:
        return match.group(1).strip()
    return None


def is_valid_curl(content):
    """Kiểm tra xem nội dung file có hợp lệ không (phải chứa từ khóa 'curl')."""
    if not content or not content.strip():
        return False
    return "curl" in content.lower()


def run_curl(curl_cmd_string, page_label):
    """Chạy cURL trực tiếp, trả về mã trạng thái và nội dung JSON."""
    cleaned_cmd = clean_curl_command(curl_cmd_string)

    try:
        cmd_list = shlex.split(cleaned_cmd)
        cmd_list.extend(["-s", "-w", "\n%{http_code}"])

        print(
            f"🔍 [Debug {page_label}] Lệnh thực thi: {cmd_list[0]} {cmd_list[1][:60]}..."
        )

        result = subprocess.run(
            cmd_list,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        stdout_output = result.stdout.strip()
        stderr_output = result.stderr.strip()

        if result.returncode != 0 and stderr_output:
            print(
                f"❌ cURL System Exit Code: {result.returncode}. Stderr: {stderr_output}"
            )

        if not stdout_output:
            return "000", "", stderr_output

        lines = stdout_output.splitlines()
        status_code = lines[-1].strip()
        json_body = "\n".join(lines[:-1])

        return status_code, json_body, stderr_output

    except Exception as e:
        return "000", "", f"Lỗi Python Runtime: {str(e)}"


def check_has_next(json_body):
    """Kiểm tra trường 'next' ở ngay root JSON (Chỉ áp dụng cho file curl-page.txt)."""
    try:
        data = json.loads(json_body)
        return "next" in data
    except json.JSONDecodeError:
        return False


def main():
    base_curl_file = Path("curl-base.txt")
    page_curl_file = Path("curl-page.txt")

    # --- BƯỚC 1: KIỂM TRA FILE BASE ---
    if not base_curl_file.exists():
        print(f"❌ Lỗi: Không tìm thấy file '{base_curl_file.name}'!")
        return

    with open(base_curl_file, "r", encoding="utf-8") as f:
        base_content = f.read()

    if not is_valid_curl(base_content):
        print(
            f"❌ Lỗi: File '{base_curl_file.name}' rỗng hoặc không phải lệnh cURL!"
        )
        return

    base_id = extract_playlist_id(base_content)
    if not base_id:
        print(
            f"❌ Lỗi: Không thể trích xuất được ID playlist từ '{base_curl_file.name}'!"
        )
        return

    print(f"🎯 Đã nhận diện ID Playlist mục tiêu: {base_id}")

    # Tự động tạo thư mục mang tên ID playlist nếu chưa có
    playlist_folder = Path(base_id)
    playlist_folder.mkdir(parents=True, exist_ok=True)

    # --- BƯỚC 2: KIỂM TRA FILE PAGE ĐỂ QUYẾT ĐỊNH CÓ PHÂN TRANG KHÔNG ---
    has_page_curl = False
    page_content = ""

    if page_curl_file.exists():
        with open(page_curl_file, "r", encoding="utf-8") as f:
            page_content = f.read()

        if is_valid_curl(page_content):
            page_id = extract_playlist_id(page_content)

            if not page_id:
                print(
                    f"❌ Lỗi: Tìm thấy file page nhưng không trích xuất được ID từ '{page_curl_file.name}'!"
                )
                return

            # Cơ chế kiểm tra chéo ID tránh chạy nhầm bài cũ
            if base_id != page_id:
                print("\n" + "!" * 60)
                print(
                    "⚠️  CẢNH BÁO NGUY HIỂM: Phát hiện bất đồng bộ ID Playlist!"
                )
                print(f"   - ID trong curl-base.txt: {base_id}")
                print(f"   - ID trong curl-page.txt: {page_id}")
                print(
                    "🛑 Hệ thống chủ động DỪNG CHẠY để tránh trộn lẫn dữ liệu!"
                )
                print("!" * 60 + "\n")
                return

            has_page_curl = True
        else:
            print(
                f"ℹ️  Nhận thấy '{page_curl_file.name}' rỗng hoặc không hợp lệ. Coi như không có file page."
            )
    else:
        print(f"ℹ️  Không tìm thấy '{page_curl_file.name}'. Coi như không có file page.")

    # --- BƯỚC 3: TIẾN HÀNH TẢI PAGE 1 (KHÔNG CHECK NEXT) ---
    print(f"\n🎵 Đang tải Page 1 cho playlist: {base_id}...")
    status_code, json_body, stderr = run_curl(base_content, "Page 1")

    if status_code == "200":
        output_name = playlist_folder / "page1.json"
        with open(output_name, "w", encoding="utf-8") as f:
            f.write(json_body)
        print(f"✅ Đã lưu thành công '{output_name}'")
    else:
        print(f"❌ Gọi Page 1 thất bại. HTTP Status: {status_code}")
        return

    # Quyết định có chạy tiếp hay không phụ thuộc hoàn toàn vào việc bạn có cấu hình file curl-page.txt không
    if not has_page_curl:
        print(
            "\n🎉 QUY TRÌNH KẾT THÚC! Bạn không cấu hình file page hoặc file page không hợp lệ. Chỉ lưu duy nhất Page 1."
        )
        return

    # --- BƯỚC 4: VÒNG LẶP PHÂN TRANG TỰ ĐỘNG (BẮT ĐẦU CHECK NEXT TỪ ĐÂY) ---
    print(
        f"\n📂 Kích hoạt phân trang theo yêu cầu. Bắt đầu tải các page tiếp theo cho {base_id}..."
    )
    print("-" * 60)

    page_num = 2
    offset = 100

    while True:
        delay = round(random.uniform(2.0, 5.0), 3)
        print(f"⏳ Chờ {delay} giây trước khi gọi Page {page_num}...")
        time.sleep(delay)

        # Ghi đè offset
        modified_curl_str = re.sub(
            r"offset=\d+", f"offset={offset}", page_content
        )

        print(f"🚀 Đang tải Page {page_num} (offset={offset})...")
        status_code, json_body, stderr = run_curl(
            modified_curl_str, f"Page {page_num}"
        )

        if status_code == "200":
            file_name = playlist_folder / f"page{page_num}.json"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(json_body)
            print(f"  🔹 Đã lưu thành công '{file_name}'")

            # 🌟 CHECK NEXT TẠI ĐÂY: Chỉ check next đối với các response sinh ra từ curl-page.txt
            if not check_has_next(json_body):
                print(
                    f"🛑 Đã chạm tới trang cuối cùng (Không tìm thấy trường 'next' ở root của Page {page_num}). Chủ động kết thúc!"
                )
                break

            page_num += 1
            offset += 100
        else:
            print(
                f"⚠️ Thất bại tại Page {page_num}. HTTP Status: {status_code}. Dừng vòng lặp."
            )
            break

    print(
        f"\n🎉 QUY TRÌNH HOÀN THÀNH! Tổng số file JSON đã tải về trong thư mục '{base_id}': {page_num}"
    )


if __name__ == "__main__":
    main()