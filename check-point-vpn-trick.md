# Tip & Trick: Cài đặt Check Point VPN không xung đột với WSL2 Network (On-Demand)

Hướng dẫn này giúp bạn cấu hình Check Point Endpoint Security VPN chỉ khởi động khi cần thiết, ngăn chặn driver firewall của nó (`vsdatant`) can thiệp và làm hỏng hệ thống mạng của WSL2 khi bạn không dùng VPN.

## 1. Tắt Firewall Driver của Check Point khi không dùng

* **Bước 1:** Tải và cài đặt Check Point Endpoint Security VPN bình thường từ trang chủ.
* **Bước 2:** Vào chế độ **Safe Boot (Minimal)**.

    - Bạn có thể dùng `msconfig` vào tab **Boot**, tích chọn Safe Boot và chọn Minimal, sau đó chọn Restart.

    - Hoặc nếu bạn thích dòng lệnh thì mở **Command Prompt (Admin)** và chạy lệnh sau để vào Safe Mode ở lần boot tới:
        ```cmd
        bcdedit /set {current} safeboot minimal
        shutdown /r /t 0
        ```

* **Bước 3:** Sau khi máy đã reboot vào Safe Mode, mở tiếp **Command Prompt (Admin)** và chạy các lệnh sau để cấu hình lại service/driver:

    ```cmd
    :: Chuyển driver firewall về chế độ chạy theo nhu cầu
    sc config vsdatant start= demand

    :: Tắt hoàn toàn watchdog bảo vệ của Check Point để tránh nó tự bật lại driver
    sc config EPWD start= disabled
    ```
* **Bước 4:** Thoát khỏi Safe Mode và restart lại máy về chế độ bình thường bằng `msconfig` để tắt Safe Boot hoặc chạy lệnh sau trong **Command Prompt (Admin)**:

    ```cmd
    bcdedit /deletevalue {current} safeboot
    shutdown /r /t 0
    ```


## 2. Cấu hình bật Check Point theo nhu cầu (On-Demand)

* **Bước 5:** Tắt service TracSrvWrapper tự động chạy khi boot máy:
    - Bạn có thể dùng GUI bằng app Services tìm đến "Check Point Endpoint Security VPN" rồi vào properties rồi chỉnh Startup type thành Manual.

    - Hoăc nếu bạn thích dòng lệnh thì mở **Command Prompt (Admin)** và chạy:

    ```cmd
    sc config TracSrvWrapper start= demand
    ```
* **Bước 6:** Tạo một shortcut (`.lnk`) để vừa kích hoạt service, vừa mở giao diện Check Point cùng một lúc:
    1. Click chuột phải ngoài Desktop -> **New** -> **Shortcut**.
    2. Tại ô **Type the location of the item**, dán đoạn lệnh sau:

        ```cmd
        C:\Windows\System32\cmd.exe /c "net start "Check Point Endpoint Security VPN" & start "" "C:\Program Files (x86)\CheckPoint\Endpoint Connect\trgui.exe""
        ```
    3. Đặt tên cho Shortcut (ví dụ: `Bật Check Point VPN`).
    4. Sau khi tạo xong, click chuột phải vào file shortcut vừa tạo -> **Properties** -> **Advanced** -> Tích chọn **Run as administrator** -> **OK**.


> ⚠️ **LƯU Ý QUAN TRỌNG**
> * Thủ thuật này hoạt động bằng cách vô hiệu hóa hoàn toàn watchdog `EPWD`. Hiện tại đã test thành công tại các doanh nghiệp không áp dụng policy kiểm tra tính toàn vẹn của phần mềm (End-point Compliance Policy Monitor).
> * Cách này **không đảm bảo 100%** sẽ hoạt động với mọi môi trường corporate enterprise nếu hệ thống của công ty bạn có cơ chế quét driver ngầm và ép bật lại `EPWD`.
