### fix dây mạng không tự nhận diện trên arch

- cài `ifplugd` và `ethtool`
- sử dụng `ifplugd` để tự nhận diên ethernet được cắm (vì nó hoạt động tốt hơn udev).
- sửa file `/etc/ifplugd/ifplugd.action`:
```bash
#!/bin/bash

# ví dụ cho enp3s0 khi được cắm
INTERFACE="$1"
ACTION="$2"

if [ "$ACTION" = "up" && "$INTERFACE" = "enp3s0"]; then
    # dùng ethtool để mở kết nối tốc độ 1000Mbps
    sleep 1 && /bin/ethtool -s enp3s0 speed 1000 duplex full autoneg on
fi
```
- enable service:
```sh
# ví dụ cho enp3s0
sudo systemctl enable --now ifplugd@enp3s0.service
```
