Assume EFI system paritition (ESP) is mounted at `/boot`.

Create folder for EFI output:
```
sudo mkdir -p /boot/EFI/Linux
```

Optionally rebuild initramfs:
```sh
sudo mkinitcpio -P
```

Build UKI:
```sh
ROOT_DEV=$(findmnt -n -o SOURCE /)
ROOT_UUID=$(blkid -s UUID -o value $ROOT_DEV)
# Main entry
sudo ukify build \
  --linux /boot/vmlinuz-linux \
  --microcode /boot/amd-ucode.img \
  --initrd /boot/initramfs-linux.img \
  --cmdline "root=UUID=$ROOT_UUID loglevel=3 quiet rw splash" \
  --stub /usr/lib/systemd/boot/efi/linuxx64.efi.stub \
  --os-release /etc/os-release \
  --uname $(uname -r) \
  --output /boot/EFI/Linux/arch-linux.efi
# Fallback entry
sudo ukify build \
  --linux /boot/vmlinuz-linux \
  --microcode /boot/amd-ucode.img \
  --initrd /boot/initramfs-linux-fallback.img \
  --cmdline "root=UUID=$ROOT_UUID loglevel=3 quiet rw splash" \
  --stub /usr/lib/systemd/boot/efi/linuxx64.efi.stub \
  --os-release /etc/os-release \
  --uname $(uname -r) \
  --output /boot/EFI/Linux/arch-linux-fallback.efi
```

#### Optional
Include nvidia kernel module to efi (needed for secure boot setup that requires nvidia):
- Edit `mkinitcpio.conf`:
```sh
sudo nano /etc/mkinitcpio.conf
```
- Add Nvidia modules
```sh
MODULES=( nvidia nvidia_drm )
```
- Rebuild initramfs image:
```sh
sudo mkinitcpio -P
```
