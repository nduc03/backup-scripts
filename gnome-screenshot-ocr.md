## screenshot ocr
Auto extract text on screen to clipboard

### For Gnome wayland 

#### Step 1: Install

install following: `gnome-screenshot`, `tesseract`, `wl-copy`
optional: `libnotify`

#### Step 2:
Create file named `ocrscreenshot` with content:
```sh
UUID=$(uuidgen)
gnome-screenshot -a -f /tmp/"$UUID"
tesseract /tmp/"$UUID" stdout | wl-copy
# optional notification if libnotify is installed
notify-send "Text from the selected area has been copied to the clipboard!"
```
and saved to some location
chmod that file: `chmod +x /path/to/ocrscreenshot`

#### Step 3:
Go to gnome keyboard setting, add custom keybind to `/path/to/ocrscreenshot`
