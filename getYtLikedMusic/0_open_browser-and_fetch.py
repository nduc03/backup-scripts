# TODO implementing and validating, not yet run and tested

# dùng playwright cho ngon, xem copy credential từ trình duyệt chính như nào?
# hoặc dùng trình duyệt chính?
# link: https://www.youtube.com/playlist?list=LL
# lây html
# lướt xuống cuối
# thấy https://www.youtube.com/youtubei/v1/browse?prettyPrint=false -> lưu lại response
# hoặc ko lướt thì dùng next token
# lưu html page1 và json các page sau vào ytLikedVideo


import os
import json
import time
from playwright.sync_api import sync_playwright

# Tạo thư mục lưu trữ
output_dir = "ytLikedVideo"
os.makedirs(output_dir, exist_ok=True)

def run():
    with sync_playwright() as p:
        # Kết nối vào Brave chính đang mở qua cổng debug
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print("❌ Lỗi: Bạn chưa mở Brave với cổng debug 9222! Hãy bật trình duyệt trước.")
            return

        context = browser.contexts[0]
        page = context.new_page()

        # Biến đếm N bắt đầu từ 2 cho các file JSON kế tiếp
        json_counter = 2

        # Hàm xử lý response để hứng dữ liệu JSON
        def handle_response(response):
            nonlocal json_counter
            if "youtubei/v1/browse" in response.url and response.request.method == "POST":
                if response.status == 200:
                    try:
                        data = response.json()
                        # Đặt tên file theo định dạng: likedvideoPageN.json (N >= 2)
                        file_path = os.path.join(output_dir, f"likedvideoPage{json_counter}.json")

                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)

                        print(f"📥 Đã lưu JSON: {file_path}")
                        json_counter += 1
                    except Exception:
                        pass

        # Đăng ký sự kiện lắng nghe mạng
        page.on("response", handle_response)

        # Truy cập trang Liked Videos
        print("🚀 Đang truy cập Playlist Liked Videos...")
        page.goto("https://www.youtube.com/playlist?list=LL", wait_until="networkidle")

        # Lưu HTML của trang đầu tiên với tên: likedvideo.html
        html_path = os.path.join(output_dir, "likedvideo.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"📄 Đã lưu HTML trang đầu: {html_path}")

        # Vòng lặp cuộn xuống cuối trang để kích hoạt gọi API tải thêm video
        print("⏳ Đang tự động cuộn xuống để tải thêm video...")
        last_height = page.evaluate("document.documentElement.scrollHeight")

        while True:
            page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")

            # Chờ 3 giây để dữ liệu tải về và hàm handle_response được kích hoạt
            time.sleep(3)

            new_height = page.evaluate("document.documentElement.scrollHeight")
            if new_height == last_height:
                time.sleep(2) # Chờ thêm một chút phòng trường hợp mạng chậm
                if page.evaluate("document.documentElement.scrollHeight") == last_height:
                    print("🎉 Đã lướt tới cuối danh sách!")
                    break
            last_height = new_height

        page.close()
        print("🏁 Hoàn thành!")

if __name__ == "__main__":
    run()