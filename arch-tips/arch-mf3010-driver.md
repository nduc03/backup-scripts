Step 1: install cups
```sh
sudo pacman -S cups
```
optional "print to pdf" printer: `cups-pdf`

Step 2: start service:
```sh
sudo systemctl enable --now cups.service
```

optional GUI:
```
sudo pacman -S system-config-printer
```
step 3: install canon mf support through AUR:
```
paru -S cnrdrvcups-lb
```
